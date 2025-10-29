import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from api.v1.models.user import User
from api.utils.settings import settings
from api.v1.schemas.user import UserCreate, Login, UserResponse
from api.db.database import get_db
from passlib.context import CryptContext
from api.v1.services.hedera import create_user_wallet, encrypt_private_key
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ENCRYPTION_KEY = settings.PRIVATE_KEY_ENCRYPTION_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login_swagger")

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for the user.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Get the current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def register_user(db: Session, user_data: UserCreate) -> dict:
    """
    Register a new user with auto-generated Hedera wallet and encrypted private key.
    """
    if db.query(User).filter(User.email == user_data.email).first():
        raise ValueError("Email already registered")

    try:
        wallet_address, private_key = await create_user_wallet()
        logger.info(f"Created Hedera wallet for user: {wallet_address}")
        
        encrypted_private_key = encrypt_private_key(private_key, ENCRYPTION_KEY)
        
    except Exception as e:
        logger.error(f"Failed to create wallet for user: {str(e)}")
        raise ValueError("Failed to create user wallet. Please try again.")

    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        role=user_data.role,
        wallet_address=wallet_address,
        encrypted_private_key=encrypted_private_key,  
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": UserResponse.from_orm(new_user),
        "wallet_address": wallet_address
    }

async def login_user(db: Session, login_data: Login) -> dict:
    """
    Authenticate a user and generate a JWT token.
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise ValueError("Invalid credentials")

    hashed_password = str(user.password)
    if not hashed_password or not pwd_context.verify(login_data.password, hashed_password):
        raise ValueError("Invalid credentials")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

async def login_user_swagger(db: Session, form_data: OAuth2PasswordRequestForm) -> dict:
    """
    Authenticate a user and generate a JWT token for OAuth2 password flow.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise ValueError("Invalid credentials")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }