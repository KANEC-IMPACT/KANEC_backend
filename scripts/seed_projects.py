"""Seed deterministic project records into the existing project database.

Run from the backend directory with:

    python -m scripts.seed_projects
"""

import argparse
from decimal import Decimal
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.db.database import SessionLocal
from api.v1.models.project import Project
from api.v1.models.user import User


PROJECTS = (
    {
        "title": "Clean Water for Rural Communities",
        "description": "Support reliable access to clean drinking water through community wells and local maintenance training.",
        "category": "Water and Sanitation",
        "target_amount": Decimal("25000.00"),
        "location": "Kano, Nigeria",
        "wallet_address": "0.0.100001",
    },
    {
        "title": "Digital Skills for Young People",
        "description": "Equip young people with practical digital skills, mentorship, and access to technology for meaningful work.",
        "category": "Education",
        "target_amount": Decimal("18000.00"),
        "location": "Lagos, Nigeria",
        "wallet_address": "0.0.100002",
    },
    {
        "title": "Community Health Outreach",
        "description": "Bring preventive health screenings, essential supplies, and health education to underserved neighborhoods.",
        "category": "Healthcare",
        "target_amount": Decimal("32000.00"),
        "location": "Kaduna, Nigeria",
        "wallet_address": "0.0.100003",
    },
    {
        "title": "Women-Led Food Gardens",
        "description": "Help women-led cooperatives establish sustainable food gardens and strengthen local food security.",
        "category": "Agriculture",
        "target_amount": Decimal("14000.00"),
        "location": "Oyo, Nigeria",
        "wallet_address": "0.0.100004",
    },
    {
        "title": "Solar Power for Learning Centers",
        "description": "Install dependable solar power systems so community learning centers can operate after dark.",
        "category": "Energy",
        "target_amount": Decimal("27500.00"),
        "location": "Abuja, Nigeria",
        "wallet_address": "0.0.100005",
    },
)


def seed_projects(count: int = len(PROJECTS)) -> int:
    """Insert deterministic projects and return the number of new rows."""
    if count < 1 or count > len(PROJECTS):
        raise ValueError(f"count must be between 1 and {len(PROJECTS)}")

    db = SessionLocal()
    try:
        creators = db.query(User).order_by(User.id).all()
        if not creators:
            raise RuntimeError("cannot seed projects: no users exist")

        existing_titles = {
            title for (title,) in db.query(Project.title).all()
        }
        inserted = 0

        for index, project_data in enumerate(PROJECTS[:count]):
            if project_data["title"] in existing_titles:
                continue

            target_amount = project_data["target_amount"]
            project_values = {
                **project_data,
                "target_amount": float(target_amount),
                "amount_raised": 0.0,
                "backers_count": 0,
                "verified": index % 2 == 0,
                "created_by": creators[index % len(creators)].id,
            }
            db.add(
                Project(**project_values)
            )
            inserted += 1

        db.commit()
        return inserted
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=len(PROJECTS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inserted = seed_projects(count=args.count)
    print(f"Inserted {inserted} project(s).")


if __name__ == "__main__":
    main()