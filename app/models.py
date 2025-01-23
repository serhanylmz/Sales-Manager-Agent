from sqlalchemy import Column, String, JSON, UUID, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # User's full name
    email = Column(String, unique=True, nullable=False)
    company_name = Column(String, nullable=False)
    website = Column(String)
    industry = Column(String, nullable=False)
    
    # Relationships
    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    icp = relationship("ICP", back_populates="user", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="products")

class ICP(Base):
    __tablename__ = "icp"
    icp_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    target_industries = Column(JSON, nullable=False)
    target_pain_points = Column(JSON, nullable=False)  # Store specific pain points the product solves
    geography = Column(String, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="icp")
    
    # Index for faster lookups
    __table_args__ = (
        Index('idx_icp_user_id', 'user_id'),
    )

class Lead(Base):
    __tablename__ = "leads"
    lead_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    lead_name = Column(String, nullable=False)  # Contact person's name
    company_name = Column(String, nullable=False)  # Company name
    company_website = Column(String, nullable=False, unique=True)  # Prevent duplicate leads
    lead_email = Column(String, nullable=False)
    status = Column(String, nullable=False, default="new")  # new, qualified, contacted, converted, rejected
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="leads")
    research = relationship("LeadResearch", back_populates="lead", cascade="all, delete-orphan")
    
    # Indexes for faster lookups
    __table_args__ = (
        Index('idx_leads_user_id', 'user_id'),
        Index('idx_leads_status', 'status'),
        Index('idx_leads_created_at', 'created_at'),
    )

class LeadResearch(Base):
    __tablename__ = "lead_research"
    research_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.lead_id", ondelete="CASCADE"), nullable=False)
    insights = Column(JSON, nullable=False)
    source = Column(String, nullable=False)  # Website URL or other source
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="research")
    
    # Index for faster lookups
    __table_args__ = (
        Index('idx_research_lead_id', 'lead_id'),
        Index('idx_research_created_at', 'created_at'),
    )