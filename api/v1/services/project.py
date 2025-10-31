from sqlalchemy.orm import Session
from api.v1.models.project import Project
from api.v1.models.donation import Donation
from api.v1.schemas.project import ProjectCreate, ProjectResponse, ProjectDB
from api.v1.services.hedera import create_project_wallet, verify_transaction
from datetime import datetime, timezone
from uuid import UUID
from typing import List
import os
import uuid
from PIL import Image
import io
from fastapi import HTTPException

# Remove UPLOAD_DIR since we're storing in DB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_IMAGE_SIZE = (1200, 800)  # Optimal size for web display

def project_to_response(project: Project) -> ProjectResponse:
    """Convert database Project model to API response model"""
    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        category=project.category,
        target_amount=project.target_amount,
        amount_raised=project.amount_raised,
        backers_count=project.backers_count,
        location=project.location,
        verified=project.verified,
        wallet_address=project.wallet_address,
        image=f"/projects/{project.id}/image" if project.image else None,
        image_mime_type=project.image_mime_type,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at
    )

async def optimize_image(image_file) -> tuple[bytes, str]:
    """
    Optimize uploaded image and return binary data and MIME type.
    """
    # Read image file
    image_data = await image_file.read()
    image = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if necessary (for JPEG)
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    
    # Resize image while maintaining aspect ratio
    image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
    
    # Convert to bytes
    output = io.BytesIO()
    image.save(output, 'WEBP', quality=85, optimize=True)
    optimized_data = output.getvalue()
    
    return optimized_data, 'image/webp'

async def create_project(db: Session, project: ProjectCreate, user_id: UUID, image_file = None) -> ProjectResponse:
    """
    Create a new project with a Hedera wallet in the database.
    """
    wallet_address = await create_project_wallet(db)
    
    # Handle image upload if provided
    image_data = None
    mime_type = None
    if image_file:
        image_data, mime_type = await optimize_image(image_file)
    
    new_project = Project(
        title=project.title,
        description=project.description,
        category=project.category,
        target_amount=project.target_amount,
        amount_raised=0.0,
        backers_count=0,
        location=project.location,
        verified=project.verified,
        wallet_address=wallet_address,  
        image=image_data,  # Store binary data
        image_mime_type=mime_type,  # Store MIME type
        created_by=user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return project_to_response(new_project)

async def upload_project_image(db: Session, project_id: UUID, image_file, user_id: UUID) -> ProjectResponse:
    """
    Upload and optimize image for a project (store in database).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    
    # Check if user owns the project or is admin
    if project.created_by != user_id:
        raise ValueError("Not authorized to update this project")
    
    # Handle image upload and optimization
    image_data, mime_type = await optimize_image(image_file)
    
    # Update project with new image data
    project.image = image_data
    project.image_mime_type = mime_type
    project.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(project)
    return project_to_response(project)

async def get_project_image(db: Session, project_id: UUID) -> tuple[bytes, str]:
    """
    Get image data and MIME type for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.image:
        raise ValueError("Project or image not found")
    
    return project.image, project.image_mime_type or 'image/webp'

async def get_verified_projects(db: Session) -> List[ProjectResponse]:
    """
    Get all verified projects.
    """
    projects = db.query(Project).filter(Project.verified == True).all()
    return [project_to_response(project) for project in projects]

async def get_project_by_id(db: Session, project_id: UUID) -> ProjectResponse:
    """
    Get a project by its ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    return project_to_response(project)

async def verify_project(db: Session, project_id: UUID) -> ProjectResponse:
    """
    Verify a project (set verified=True).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    project.verified = True
    db.commit()
    db.refresh(project)
    return project_to_response(project)

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
        "backers_count": project.backers_count,
        "image": f"/projects/{project_id}/image" if project.image else None,
        "donations": verified_donations
    }