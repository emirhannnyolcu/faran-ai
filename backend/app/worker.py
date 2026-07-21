import argparse
import time

from app.core.database import SessionLocal, engine
from app.repositories.workflow_repository import WorkflowRepository
from app.services.workflow_service import execute_workflow
from app.services.schedule_service import ScheduleService


def process_batch(limit: int = 10) -> int:
    """Execute one bounded batch of durable queued workflows."""
    db = SessionLocal()
    try:
        scheduled_ids = ScheduleService(db).enqueue_due(limit=limit)
        workflow_ids = scheduled_ids + [
            workflow.id for workflow in WorkflowRepository(db).list_queued(limit=limit)
            if workflow.id not in scheduled_ids
        ]
    finally:
        db.close()
    for workflow_id in workflow_ids:
        execute_workflow(engine, workflow_id)
    return len(workflow_ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FARAN workflow worker")
    parser.add_argument("--once", action="store_true", help="Process one batch and exit")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()

    while True:
        processed = process_batch(limit=max(1, args.batch_size))
        if args.once:
            return
        if processed == 0:
            time.sleep(max(0.1, args.interval))


if __name__ == "__main__":
    main()
