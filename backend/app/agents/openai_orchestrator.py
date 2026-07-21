import asyncio
from dataclasses import dataclass
import json
from typing import Annotated

from agents import (
    Agent,
    AgentsException,
    HostedMCPTool,
    RunConfig,
    RunContextWrapper,
    Runner,
    function_tool,
    handoff,
    set_default_openai_key,
)
from pydantic import Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.ai.model_settings import build_agent_model_settings
from app.memory.schemas import MemoryCandidate
from app.memory.service import MemoryService
from app.prompts.agents import (
    MEMORY_INSTRUCTIONS,
    PLANNER_INSTRUCTIONS,
    REASONING_INSTRUCTIONS,
    RESEARCH_INSTRUCTIONS,
    WORKSPACE_INSTRUCTIONS,
    WRITER_INSTRUCTIONS,
)
from app.repositories.memory_repository import MemoryRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.agent import (
    AgentRunResponse,
    AgentStep,
    GoalAnalysis,
    OpenAIWorkflowOutput,
    PlannedTask,
)
from app.services.errors import (
    AIServiceError,
    WorkflowNotFoundError,
    WorkflowRetryNotAllowedError,
)
from app.tools.memory_tools import build_default_tool_registry
from app.tools.registry import ToolRegistry


@dataclass
class OpenAIAgentContext:
    """Local dependencies shared by OpenAI Agents SDK tools."""

    db: Session
    tools: ToolRegistry


def _serialize_tool_result(result: object) -> str:
    """Serialize Pydantic tool outputs without exposing database objects."""
    model_dump_json = getattr(result, "model_dump_json", None)
    if callable(model_dump_json):
        return model_dump_json()
    return str(result)


@function_tool(name_override="search_memory", timeout=15.0)
async def search_memory_tool(
    context: RunContextWrapper[OpenAIAgentContext],
    query: Annotated[str, Field(min_length=1, max_length=2000)],
    limit: Annotated[int, Field(ge=1, le=20)] = 5,
) -> str:
    """Search FARAN long-term memory for information relevant to a query."""
    result = context.context.tools.call(
        "search_memory",
        db=context.context.db,
        query=query,
        limit=limit,
    )
    return _serialize_tool_result(result)


@function_tool(name_override="assemble_context", timeout=15.0)
async def assemble_context_tool(
    context: RunContextWrapper[OpenAIAgentContext],
    query: Annotated[str, Field(min_length=1, max_length=2000)],
    limit: Annotated[int, Field(ge=1, le=20)] = 5,
) -> str:
    """Assemble primary, connected, and important memories for a query."""
    result = context.context.tools.call(
        "assemble_context",
        db=context.context.db,
        query=query,
        limit=limit,
    )
    return _serialize_tool_result(result)


@function_tool(name_override="reflect_memory", timeout=15.0)
async def reflect_memory_tool(
    context: RunContextWrapper[OpenAIAgentContext],
) -> str:
    """Identify recurring topics and patterns in FARAN long-term memory."""
    result = context.context.tools.call("reflect_memory", db=context.context.db)
    return _serialize_tool_result(result)


def build_openai_agent_graph() -> Agent[OpenAIAgentContext]:
    """Build FARAN's manager-style multi-agent graph with an explicit handoff."""
    memory_agent = Agent[OpenAIAgentContext](
        name="Memory Agent",
        handoff_description="Retrieves and assembles the user's long-term memory.",
        instructions=MEMORY_INSTRUCTIONS,
        model=settings.OPENAI_ANALYSIS_MODEL,
        tools=[search_memory_tool, assemble_context_tool, reflect_memory_tool],
    )
    research_agent = Agent[OpenAIAgentContext](
        name="Research Agent",
        handoff_description="Investigates the user's request using available memory evidence.",
        instructions=RESEARCH_INSTRUCTIONS,
        model=settings.OPENAI_ANALYSIS_MODEL,
        tools=[search_memory_tool],
    )
    reasoning_agent = Agent[OpenAIAgentContext](
        name="Reasoning Agent",
        handoff_description="Synthesizes evidence into a grounded recommendation.",
        instructions=REASONING_INSTRUCTIONS,
        model=settings.OPENAI_ANALYSIS_MODEL,
    )
    writer_agent = Agent[OpenAIAgentContext](
        name="Writer Agent",
        handoff_description="Produces FARAN's final user-facing response.",
        instructions=WRITER_INSTRUCTIONS,
        model=settings.OPENAI_ANALYSIS_MODEL,
    )
    workspace_agent = Agent[OpenAIAgentContext](
        name="FARAN Workspace Agent",
        handoff_description="Coordinates FARAN's specialist agents to complete the request.",
        instructions=WORKSPACE_INSTRUCTIONS,
        model=settings.OPENAI_MODEL,
        output_type=OpenAIWorkflowOutput,
        tools=[
            memory_agent.as_tool(
                tool_name="consult_memory_agent",
                tool_description="Retrieve and assemble relevant long-term memory.",
            ),
            research_agent.as_tool(
                tool_name="consult_research_agent",
                tool_description="Investigate the request using available memory evidence.",
            ),
            reasoning_agent.as_tool(
                tool_name="consult_reasoning_agent",
                tool_description="Synthesize evidence into a grounded recommendation.",
            ),
            writer_agent.as_tool(
                tool_name="consult_writer_agent",
                tool_description="Write the final user-facing answer.",
            ),
            *_connected_workspace_tools(),
        ],
    )
    return Agent[OpenAIAgentContext](
        name="Planner Agent",
        instructions=PLANNER_INSTRUCTIONS,
        model=settings.OPENAI_ANALYSIS_MODEL,
        handoffs=[
            handoff(
                workspace_agent,
                tool_description_override=(
                    "Transfer the planned request to FARAN's workspace execution agent."
                ),
            )
        ],
    )


def _connected_workspace_tools() -> list[HostedMCPTool]:
    """Build allowlisted OpenAI connector and remote MCP tools when configured."""
    tools: list[HostedMCPTool] = []
    if settings.OPENAI_CONNECTOR_ID:
        tools.append(
            HostedMCPTool(
                tool_config={
                    "type": "mcp",
                    "server_label": "faran_connector",
                    "connector_id": settings.OPENAI_CONNECTOR_ID,
                    "authorization": settings.OPENAI_CONNECTOR_AUTHORIZATION,
                    "allowed_tools": settings.openai_connector_allowed_tools,
                    "allowed_callers": ["direct"],
                    "require_approval": "never",
                    "defer_loading": True,
                }
            )
        )
    if settings.OPENAI_MCP_SERVER_URL:
        tools.append(
            HostedMCPTool(
                tool_config={
                    "type": "mcp",
                    "server_label": settings.OPENAI_MCP_SERVER_LABEL,
                    "server_url": settings.OPENAI_MCP_SERVER_URL,
                    "allowed_tools": settings.openai_mcp_allowed_tools,
                    "allowed_callers": ["direct"],
                    "require_approval": "never",
                    "defer_loading": True,
                }
            )
        )
    return tools


class OpenAIAgentOrchestrator:
    """Execute FARAN workflows through OpenAI Agents SDK."""

    plan = [
        "Plan the workspace task.",
        "Retrieve and assemble relevant long-term memory.",
        "Research available evidence when needed.",
        "Reason over evidence and uncertainty.",
        "Write the final response.",
    ]

    def __init__(self, db: Session) -> None:
        self.db = db
        self.workflow_repository = WorkflowRepository(db)

    async def run(
        self,
        user_input: str,
        conversation_id: str | None = None,
    ) -> AgentRunResponse:
        """Run and persist one traced OpenAI multi-agent workflow."""
        return await self._execute(user_input, conversation_id=conversation_id)

    async def retry(self, workflow_id: int) -> AgentRunResponse:
        """Retry a failed OpenAI workflow without duplicating state."""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError()
        if workflow.status != "failed" or workflow.attempt_count >= workflow.max_attempts:
            raise WorkflowRetryNotAllowedError()
        return await self._execute(workflow.user_input, workflow_id=workflow.id)

    async def execute_queued(self, workflow_id: int) -> AgentRunResponse:
        """Execute one workflow already claimed by a durable worker."""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError()
        if workflow.status != "claimed":
            raise WorkflowRetryNotAllowedError()
        return await self._execute(
            workflow.user_input,
            workflow_id=workflow.id,
            conversation_id=workflow.conversation_id,
        )

    async def _execute(
        self,
        user_input: str,
        workflow_id: int | None = None,
        conversation_id: str | None = None,
    ) -> AgentRunResponse:
        if not settings.OPENAI_API_KEY:
            raise AIServiceError("OpenAI agent credentials are not configured")

        set_default_openai_key(settings.OPENAI_API_KEY, use_for_tracing=True)
        previous_response_id = (
            self.workflow_repository.latest_response_id(conversation_id)
            if conversation_id is not None
            else None
        )
        workflow = (
            self.workflow_repository.get_by_id(workflow_id)
            if workflow_id is not None
            else self.workflow_repository.create(
                user_input,
                self.plan,
                max_attempts=settings.WORKFLOW_MAX_ATTEMPTS,
                runtime="openai",
                conversation_id=conversation_id,
            )
        )
        if workflow is None:
            raise WorkflowNotFoundError()
        self.workflow_repository.begin(workflow)
        self.db.commit()

        try:
            result = await asyncio.wait_for(
                Runner.run(
                    build_openai_agent_graph(),
                    user_input,
                    context=OpenAIAgentContext(
                        db=self.db,
                        tools=build_default_tool_registry(),
                    ),
                    max_turns=settings.AGENT_MAX_TURNS,
                    previous_response_id=previous_response_id,
                    auto_previous_response_id=conversation_id is not None,
                    run_config=RunConfig(
                        model_settings=build_agent_model_settings(),
                        workflow_name="FARAN Workspace Workflow",
                        group_id=f"workflow-{workflow.id}",
                        tracing_disabled=not settings.OPENAI_TRACING_ENABLED,
                        trace_include_sensitive_data=(
                            settings.OPENAI_TRACE_INCLUDE_SENSITIVE_DATA
                        ),
                    ),
                ),
                timeout=settings.AGENT_WORKFLOW_TIMEOUT_SECONDS,
            )
            output = _workflow_output(result.final_output)
            final_answer = output.final_answer
            steps = _steps_from_result(result)
            tasks = [
                PlannedTask(
                    sequence=index,
                    title=task[:160],
                    description=task,
                )
                for index, task in enumerate(output.tasks, start=1)
            ]
            payload = {
                "final_answer": final_answer,
                "tasks": [task.model_dump(mode="json") for task in tasks],
                "research_status": output.research_status,
                "research_summary": output.research_summary,
                "completion_criteria": output.completion_criteria,
                "steps": [step.model_dump() for step in steps],
            }
            memory = _persist_workflow_memory(
                db=self.db,
                workflow_id=workflow.id,
                user_input=user_input,
                payload=payload,
            )
            payload["memory_id"] = memory.id
            response_id = getattr(result, "last_response_id", None)
            self.workflow_repository.complete(
                workflow,
                payload,
                response_id=response_id,
            )
            self.db.commit()
        except AgentsException as exc:
            self._record_failure(workflow.id, "OpenAI agent workflow failed")
            raise AIServiceError("OpenAI agent workflow failed") from exc
        except SQLAlchemyError:
            self.db.rollback()
            self._record_failure(workflow.id, "OpenAI workflow persistence failed")
            raise
        except Exception as exc:
            self._record_failure(workflow.id, "OpenAI agent workflow failed")
            raise AIServiceError("OpenAI agent workflow failed") from exc

        return AgentRunResponse(
            workflow_id=workflow.id,
            status=workflow.status,
            plan=self.plan,
            steps=steps,
            final_answer=final_answer,
            goal_analysis=_goal_analysis(user_input),
            tasks=tasks,
            memory_id=memory.id,
            conversation_id=workflow.conversation_id,
            response_id=workflow.response_id,
        )

    def _record_failure(self, workflow_id: int, message: str) -> None:
        self.db.rollback()
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is not None:
            self.workflow_repository.fail(workflow, message)
            self.db.commit()


def _steps_from_result(result: object) -> list[AgentStep]:
    """Convert SDK run items into a stable, non-sensitive API summary."""
    steps: list[AgentStep] = []
    for item in getattr(result, "new_items", []):
        agent = getattr(getattr(item, "agent", None), "name", "OpenAI Agent")
        item_type = getattr(item, "type", item.__class__.__name__)
        steps.append(
            AgentStep(
                agent=agent,
                action=str(item_type),
                output="Agent step completed.",
            )
        )
    if not steps:
        steps.append(
            AgentStep(
                agent="FARAN Workspace Agent",
                action="complete",
                output="OpenAI agent workflow completed.",
            )
        )
    return steps


def _workflow_output(value: object) -> OpenAIWorkflowOutput:
    """Normalize SDK structured output and retain compatibility with mocked tests."""
    if isinstance(value, OpenAIWorkflowOutput):
        return value
    if isinstance(value, dict):
        return OpenAIWorkflowOutput.model_validate(value)
    return OpenAIWorkflowOutput(
        final_answer=str(value),
        tasks=["Review and apply the completed FARAN workspace result."],
        research_status="skipped",
        research_summary="No structured research summary was returned.",
        completion_criteria=["The requested result was returned to the user."],
    )


def _goal_analysis(user_input: str) -> GoalAnalysis:
    topic = " ".join(user_input.rstrip(".!?").split()[:6])[:120] or "Workspace Goal"
    return GoalAnalysis(
        goal=user_input,
        objective=f"Complete the workspace goal: {user_input}",
        topic=topic,
        success_criteria=["The structured workspace result satisfies the request."],
    )


def _persist_workflow_memory(
    db: Session,
    workflow_id: int,
    user_input: str,
    payload: dict[str, object],
):
    analysis = _goal_analysis(user_input)
    candidate = MemoryCandidate(
        source_type="agent_workflow",
        source_id=workflow_id,
        source_title=user_input[:255],
        source_content=json.dumps(payload, ensure_ascii=True),
        summary=str(payload["final_answer"])[:2000],
        topic=analysis.topic,
        tags=["agent", "workflow", "openai"],
        importance=4,
        insights=(
            "FARAN completed a structured GPT-5.6 workspace workflow and preserved "
            "its tasks, research status, and completion criteria."
        ),
    )
    return MemoryService(MemoryRepository(db)).persist_candidate(candidate)
