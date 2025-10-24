from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from api.v1.models.base_class import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False, index=True)
    region = Column(String(100), nullable=True)
    verified = Column(Boolean, default=False, nullable=False)

    # link to user who created the organization
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # relationships
    creator = relationship("User", back_populates="organizations")
