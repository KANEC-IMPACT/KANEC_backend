from sqlalchemy import Column, String, Text, Boolean, Float, ForeignKey, Integer, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.v1.models.base_class import BaseModel


class Project(BaseModel):
    __tablename__ = "projects"

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    amount_raised = Column(Float, default=0.0)
    backers_count = Column(Integer, default=0)
    location = Column(String(255), nullable=True)
    verified = Column(Boolean, default=False)
    wallet_address = Column(String(255), nullable=False)
    image = Column(LargeBinary, nullable=True) 
    image_mime_type = Column(String(50), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # relationships
    creator = relationship("User", back_populates="projects")
    donations = relationship("Donation", back_populates="project", cascade="all, delete-orphan")