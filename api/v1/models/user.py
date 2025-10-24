from sqlalchemy import Column, String, Enum
from enum import Enum as PyEnum
from api.v1.models.base_class import BaseModel
from sqlalchemy.orm import relationship


class UserRole(PyEnum):
    DONOR = "donor"
    ADMIN = "admin"
    ORG = "org"


class User(BaseModel):
    __tablename__ = "users"

    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.DONOR)
    wallet_address = Column(String(255), unique=True, nullable=True)

       
    projects = relationship("Project", back_populates="creator", cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="donor", cascade="all, delete-orphan")
    organizations = relationship("Organization", back_populates="creator", cascade="all, delete-orphan")

