# api/v1/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.services.auth import register_user, login_user
from api.v1.schemas.user import UserCreate, Login

auth = APIRouter(prefix="/api", tags=["auth"])

@auth.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    try:
        response = await register_user(db, user)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@auth.post("/login")
async def login_user_endpoint(login: Login, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.
    """
    try:
        response = await login_user(db, login)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))