from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.hedera import create_project_wallet
from api.v1.services.project import create_project, get_verified_projects, get_project_by_id, verify_project, get_project_transparency, upload_project_image, get_project_image
from api.v1.schemas.project import ProjectCreate, ProjectResponse
from api.v1.services.auth import get_current_user
from uuid import UUID
from typing import List

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse)
async def create_project_endpoint(project: ProjectCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Create a new project with a Hedera wallet.
    """
    try:
        if current_user.role.value not in ["admin", "org"]:
            raise HTTPException(status_code=403, detail="Only admins or orgs can create projects")
        new_project = await create_project(db, project, current_user.id)
        return new_project
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{project_id}/image", response_model=ProjectResponse)
async def upload_project_image_endpoint(
    project_id: UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Upload an image for a project.
    """
    try:
        if current_user.role.value not in ["admin", "org"]:
            raise HTTPException(status_code=403, detail="Only admins or orgs can upload project images")
        
        # Validate image file type
        if image.filename:
            file_extension = image.filename.lower().split('.')[-1]
            if f".{file_extension}" not in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
                raise HTTPException(status_code=400, detail="Invalid image format. Allowed: jpg, jpeg, png, gif, webp")
        
        updated_project = await upload_project_image(db, project_id, image, current_user.id)
        return updated_project
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}/image")
async def get_project_image_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get project image as binary data.
    """
    try:
        image_data, mime_type = await get_project_image(db, project_id)
        return Response(content=image_data, media_type=mime_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ProjectResponse])
async def get_verified_projects_endpoint(db: Session = Depends(get_db)):
    """
    Get all verified projects.
    """
    try:
        projects = await get_verified_projects(db)
        return projects
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    """
    Get a single project by ID.
    """
    try:
        project = await get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}/transparency")
async def get_project_transparency_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    """
    Get transparency details for a project.
    """
    try:
        return await get_project_transparency(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{project_id}/verify")
async def verify_project_endpoint(project_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Verify a project (admin only).
    """
    try:
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Only admins can verify projects")
        project = await verify_project(db, project_id)
        return project
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))