import asyncio
import json

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.agents.orchestrator import AgentOrchestrator
from app.memory.schemas import MemoryCandidate
from app.memory.service import MemoryService
from app.models.memory_item import MemoryItem
from app.models.memory_vector import MemoryVector
from app.models.workflow_run import WorkflowRun
from app.repositories.memory_repository import MemoryRepository


def test_goal_workflow_persists_plan_tasks_and_memory(client):
    response = client.post(
        "/agent/run",
        json={"user_input": "Launch a focused weekly learning routine"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["goal_analysis"]["goal"] == (
        "Launch a focused weekly learning routine"
    )
    assert len(payload["plan"]) == 5
    assert payload["research"]["status"] == "skipped"
    assert payload["research"]["decision"]["required"] is False
    assert [task["sequence"] for task in payload["tasks"]] == [1, 2, 3, 4, 5]
    assert {task["status"] for task in payload["tasks"]} == {"pending"}

    step_agents = [step["agent"] for step in payload["steps"]]
    assert step_agents.index("Planner Agent") < step_agents.index("Task Agent")
    assert step_agents.index("Task Agent") < step_agents.index("Memory Agent")

    db = client.app.state.testing_session_factory()
    try:
        workflow = db.query(WorkflowRun).one()
        result = json.loads(workflow.result_json)
        memory = db.query(MemoryItem).filter_by(id=payload["memory_id"]).one()
        vector = db.query(MemoryVector).filter_by(memory_id=memory.id).one()

        assert result["goal_analysis"] == payload["goal_analysis"]
        assert result["tasks"] == payload["tasks"]
        assert result["memory_id"] == memory.id
        assert memory.source_type == "goal_workflow"
        assert memory.source_id == workflow.id
        assert memory.topic == payload["goal_analysis"]["topic"]
        stored_content = json.loads(memory.source_content)
        assert stored_content["research"] == payload["research"]
        assert vector.memory_id == memory.id
    finally:
        db.close()


def test_goal_workflow_integrates_research_findings(client):
    db = client.app.state.testing_session_factory()
    try:
        memory = MemoryService(MemoryRepository(db)).persist_candidate(
            MemoryCandidate(
                source_title="Focused learning",
                source_content="Compare short practice sessions and weekly reviews.",
                summary="Short practice plus weekly review improves consistency.",
                topic="Learning Strategy",
                tags=["learning", "review"],
                importance=4,
                insights="Use measurable review checkpoints.",
            )
        )
        db.commit()
        source_memory_id = memory.id
    finally:
        db.close()

    response = client.post(
        "/agent/run",
        json={"user_input": "Compare learning strategies from my saved memory"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["research"]["status"] == "completed"
    assert payload["research"]["decision"]["required"] is True
    assert payload["research"]["findings"][0]["memory_id"] == source_memory_id
    assert len(payload["plan"]) == 6
    assert len(payload["tasks"]) == 6
    assert "Apply relevant long-term memory evidence" in payload["plan"][2]

    step_agents = [step["agent"] for step in payload["steps"]]
    assert step_agents.index("Planner Agent") < step_agents.index("Research Agent")
    assert step_agents.index("Research Agent") < step_agents.index("Task Agent")

    db = client.app.state.testing_session_factory()
    try:
        goal_memory = db.query(MemoryItem).filter_by(id=payload["memory_id"]).one()
        stored_content = json.loads(goal_memory.source_content)
        assert stored_content["research"] == payload["research"]
    finally:
        db.close()


def test_goal_workflow_adds_evidence_task_when_research_is_insufficient(client):
    response = client.post(
        "/agent/run",
        json={"user_input": "Research options for a new learning system"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["research"]["status"] == "insufficient"
    assert payload["research"]["findings"] == []
    assert len(payload["plan"]) == 6
    assert payload["plan"][2] == (
        "Collect the missing evidence required to validate the goal plan."
    )
    assert payload["tasks"][2]["description"] == payload["plan"][2]


def test_goal_workflow_rolls_back_memory_and_marks_failure(client, monkeypatch):
    def fail_memory_write(*args, **kwargs):
        raise SQLAlchemyError("memory write failed")

    monkeypatch.setattr(
        "app.tools.memory_tools.MemoryService.persist_candidate",
        fail_memory_write,
    )
    db = client.app.state.testing_session_factory()
    try:
        orchestrator = AgentOrchestrator(db)
        with pytest.raises(SQLAlchemyError):
            asyncio.run(orchestrator.run("Build a reliable review habit"))
    finally:
        db.close()

    db = client.app.state.testing_session_factory()
    try:
        workflow = db.query(WorkflowRun).one()
        assert workflow.status == "failed"
        assert workflow.last_error == "Workflow persistence failed"
        assert workflow.result_json is None
        assert db.query(MemoryItem).count() == 0
        assert db.query(MemoryVector).count() == 0
    finally:
        db.close()
