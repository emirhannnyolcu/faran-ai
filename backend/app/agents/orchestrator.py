from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.base import AgentContext
from app.agents.memory_agent import MemoryAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.task_agent import TaskAgent
from app.agents.tool_agent import ToolAgent
from app.agents.writer_agent import WriterAgent
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.agent import AgentRunResponse
from app.core.settings import settings
from app.services.errors import WorkflowNotFoundError, WorkflowRetryNotAllowedError
from app.tools.memory_tools import build_default_tool_registry


class AgentOrchestrator:
    """Coordinate FARAN's multi-agent workflow."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.workflow_repository = WorkflowRepository(db)
        self.tool_agent = ToolAgent()
        self.planner = PlannerAgent()
        self.research = ResearchAgent(self.tool_agent)
        self.task = TaskAgent()
        self.memory = MemoryAgent(self.tool_agent)
        self.reasoning = ReasoningAgent()
        self.writer = WriterAgent()

    async def run(
        self,
        user_input: str,
        conversation_id: str | None = None,
    ) -> AgentRunResponse:
        """Run the full FARAN agent workflow."""
        return self._execute(user_input, conversation_id=conversation_id)

    async def retry(self, workflow_id: int) -> AgentRunResponse:
        """Retry a failed workflow without creating a duplicate record."""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError()
        if workflow.status != "failed" or workflow.attempt_count >= workflow.max_attempts:
            raise WorkflowRetryNotAllowedError()
        return self._execute(workflow.user_input, workflow_id=workflow.id)

    async def execute_queued(self, workflow_id: int) -> AgentRunResponse:
        """Execute one workflow already claimed by a durable worker."""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError()
        if workflow.status != "claimed":
            raise WorkflowRetryNotAllowedError()
        return self._execute(
            workflow.user_input,
            workflow_id=workflow.id,
            conversation_id=workflow.conversation_id,
        )

    def _execute(
        self,
        user_input: str,
        workflow_id: int | None = None,
        conversation_id: str | None = None,
    ) -> AgentRunResponse:
        context = AgentContext(
            user_input=user_input,
            db=self.db,
            tools=build_default_tool_registry(),
        )
        self.planner.run(context)
        workflow = (
            self.workflow_repository.get_by_id(workflow_id)
            if workflow_id is not None
            else self.workflow_repository.create(
                user_input,
                context.plan,
                max_attempts=settings.WORKFLOW_MAX_ATTEMPTS,
                runtime="deterministic",
                conversation_id=conversation_id,
            )
        )
        if workflow is None:
            raise WorkflowNotFoundError()
        self.workflow_repository.begin(workflow)
        self.db.commit()
        context.workflow_id = workflow.id

        try:
            self.research.run(context)
            self.task.run(context)
            self.memory.run(context)
            self.reasoning.run(context)
            final_answer = self.writer.run(context)
            result = {
                "goal_analysis": (
                    context.goal_analysis.model_dump(mode="json")
                    if context.goal_analysis
                    else None
                ),
                "plan": context.plan,
                "research": (
                    context.research.model_dump(mode="json")
                    if context.research
                    else None
                ),
                "tasks": [task.model_dump(mode="json") for task in context.tasks],
                "memory_id": context.memory_id,
                "final_answer": final_answer,
                "steps": [step.model_dump() for step in context.steps],
            }
            self.workflow_repository.complete(workflow, result)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            self._record_failure(workflow.id, "Workflow persistence failed")
            raise exc
        except Exception as exc:
            self._record_failure(workflow.id, "Agent workflow failed")
            raise exc

        return AgentRunResponse(
            workflow_id=workflow.id,
            status=workflow.status,
            plan=context.plan,
            steps=context.steps,
            final_answer=final_answer,
            goal_analysis=context.goal_analysis,
            research=context.research,
            tasks=context.tasks,
            memory_id=context.memory_id,
            conversation_id=workflow.conversation_id,
        )

    def _record_failure(self, workflow_id: int, message: str) -> None:
        self.db.rollback()
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is not None:
            self.workflow_repository.fail(workflow, message)
            self.db.commit()
