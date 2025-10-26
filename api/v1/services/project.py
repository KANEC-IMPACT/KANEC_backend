# api/v1/services/project.py
from sqlalchemy.orm import Session
from api.v1.models.project import Project
from api.v1.models.donation import Donation
from api.v1.schemas.project import ProjectCreate, ProjectResponse
from api.v1.services.hedera import create_project_wallet, verify_transaction
from datetime import datetime, timezone
from uuid import UUID
from typing import List

async def create_project(db: Session, project: ProjectCreate, user_id: UUID) -> Project:
    """
    Create a new project with a Hedera wallet in the database.
    """
    # Create Hedera wallet first
    wallet_address = await create_project_wallet(db)  # No project passed yet
    new_project = Project(
        title=project.title,
        description=project.description,
        category=project.category,
        target_amount=project.target_amount,
        amount_raised=0.0,
        location=project.location,
        verified=project.verified,
        wallet_address=wallet_address,  # Set wallet_address
        created_by=user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

async def get_verified_projects(db: Session) -> List[Project]:
    """
    Get all verified projects.
    """
    return db.query(Project).filter(Project.verified == True).all()

async def get_project_by_id(db: Session, project_id: UUID) -> Project:
    """
    Get a project by its ID.
    """
    return db.query(Project).filter(Project.id == project_id).first()

async def verify_project(db: Session, project_id: UUID) -> Project:
    """
    Verify a project (set verified=True).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    project.verified = True
    db.commit()
    db.refresh(project)
    return project

async def get_project_transparency(db: Session, project_id: UUID) -> dict:
    """
    Get transparency details for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    
    donations = db.query(Donation).filter(Donation.project_id == project_id).all()
    verified_donations = []
    for donation in donations:
        verification = await verify_transaction(donation.tx_hash) if donation.tx_hash else {"valid": False, "from_account": None, "to_account": None, "amount": 0.0}
        verified_donations.append({
            "amount": donation.amount,
            "tx_hash": donation.tx_hash,
            "status": donation.status.value,
            "from_account": verification["from_account"],
            "to_account": verification["to_account"],
            "valid": verification["valid"]
        })
    
    return {
        "project_id": project_id,
        "wallet_address": project.wallet_address,
        "amount_raised": project.amount_raised,
        "donations": verified_donations
    }