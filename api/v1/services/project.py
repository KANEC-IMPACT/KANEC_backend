from sqlalchemy.orm import Session
from api.v1.models.project import Project
from api.v1.models.donation import Donation
from api.v1.schemas.project import ProjectCreate, ProjectResponse
from api.v1.services.hedera import create_project_wallet, verify_transaction
from datetime import datetime, timezone
from uuid import UUID
from typing import List
import os
import uuid
from PIL import Image
import io

# Configure upload directory
UPLOAD_DIR = "static/projects"
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_IMAGE_SIZE = (1200, 800)  # Optimal size for web display

async def optimize_and_save_image(image_file, upload_dir: str, filename: str) -> str:
    """
    Optimize and save uploaded image with proper sizing and compression.
    """
    os.makedirs(upload_dir, exist_ok=True)
    
    # Read image file
    image_data = await image_file.read()
    image = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if necessary (for JPEG)
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    
    # Resize image while maintaining aspect ratio
    image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
    
    # Generate unique filename
    file_extension = '.webp'  # Use modern format for better compression
    unique_filename = f"{filename}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save optimized image
    image.save(file_path, 'WEBP', quality=85, optimize=True)
    
    return f"/static/projects/{unique_filename}"

async def create_project(db: Session, project: ProjectCreate, user_id: UUID, image_file = None) -> Project:
    """
    Create a new project with a Hedera wallet in the database.
    """
    wallet_address = await create_project_wallet(db)
    
    # Handle image upload if provided
    image_path = None
    if image_file:
        filename = str(uuid.uuid4())
        image_path = await optimize_and_save_image(image_file, UPLOAD_DIR, filename)
    
    new_project = Project(
        title=project.title,
        description=project.description,
        category=project.category,
        target_amount=project.target_amount,
        amount_raised=0.0,
        location=project.location,
        verified=project.verified,
        wallet_address=wallet_address,  
        image=image_path,  # Store the image path
        created_by=user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

async def upload_project_image(db: Session, project_id: UUID, image_file, user_id: UUID) -> Project:
    """
    Upload and optimize image for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    
    # Check if user owns the project or is admin
    if project.created_by != user_id:
        raise ValueError("Not authorized to update this project")
    
    # Handle image upload
    filename = str(uuid.uuid4())
    image_path = await optimize_and_save_image(image_file, UPLOAD_DIR, filename)
    
    # Update project with new image
    project.image = image_path
    project.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(project)
    return project

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
        "image": project.image,  # Include image in transparency data
        "donations": verified_donations
    }