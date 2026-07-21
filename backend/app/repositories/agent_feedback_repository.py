from sqlalchemy.orm import Session

from app.models.agent_feedback import AgentFeedback


class AgentFeedbackRepository:
    """Persist expert corrections and generated regression cases."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        workflow_id: int,
        correction: str,
        expected_outcome: str,
        regression_case_json: str,
        suggested_task: str,
    ) -> AgentFeedback:
        feedback = AgentFeedback(
            workflow_id=workflow_id,
            correction=correction,
            expected_outcome=expected_outcome,
            regression_case_json=regression_case_json,
            suggested_task=suggested_task,
        )
        self.db.add(feedback)
        self.db.flush()
        self.db.refresh(feedback)
        return feedback

    def list_for_workflow(self, workflow_id: int) -> list[AgentFeedback]:
        return (
            self.db.query(AgentFeedback)
            .filter(AgentFeedback.workflow_id == workflow_id)
            .order_by(AgentFeedback.id.asc())
            .all()
        )
