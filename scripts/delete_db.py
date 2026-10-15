"""Delete all application data while preserving the database schema.

Run from the backend directory with:

    python -m scripts.delete_db --confirm DELETE
"""

import argparse
from pathlib import Path
import sys

from sqlalchemy import inspect

# Allow the script to be run as ``python scripts/delete_db.py`` as well
# as ``python -m scripts.delete_db``.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.db.database import SessionLocal, engine
from api.v1.models import BaseModel


CONFIRMATION = "DELETE"


def delete_application_data() -> dict[str, int]:
    """Delete rows from every registered application model."""
    db = SessionLocal()
    deleted: dict[str, int] = {}
    try:
        existing_tables = set(inspect(engine).get_table_names())

        # Reverse dependency order so child rows are removed before parents.
        for table in reversed(BaseModel.metadata.sorted_tables):
            if table.name not in existing_tables:
                continue
            result = db.execute(table.delete())
            deleted[table.name] = result.rowcount or 0

        db.commit()
        return deleted
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm",
        required=True,
        help=f"Type {CONFIRMATION} to confirm deleting all application data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.confirm != CONFIRMATION:
        raise SystemExit("Deletion cancelled: confirmation must be exactly DELETE.")

    deleted = delete_application_data()
    total = sum(deleted.values())
    print(f"Deleted {total} row(s) from {len(deleted)} table(s).")
    for table_name, row_count in deleted.items():
        print(f"  {table_name}: {row_count}")


if __name__ == "__main__":
    main()