from sqlalchemy import Column, Float, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from api.v1.models.base_class import BaseModel


class DonationStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Donation(BaseModel):
    __tablename__ = "donations"

    donor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    amount = Column(Float, nullable=False)
    tx_hash = Column(String(255), unique=True, nullable=True)
    status = Column(Enum(DonationStatus), default=DonationStatus.pending, nullable=False)

    # relationships
    donor = relationship("User", back_populates="donations")
    project = relationship("Project", back_populates="donations")
