import argparse

from app.db import SessionLocal, init_db
from app.services import process_due_questions


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify DearFuture questions that are due.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum questions per run")
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        questions = process_due_questions(db, limit=max(1, args.limit))

    resolved = sum(question.status == "resolved" for question in questions)
    retrying = sum(question.status == "retry_pending" for question in questions)
    failed = sum(question.status == "failed" for question in questions)
    print(
        f"Processed {len(questions)} question(s): "
        f"{resolved} resolved, {retrying} retrying, {failed} failed."
    )


if __name__ == "__main__":
    main()
