"""
Organization, Show, Season, and Customer models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Organization(Base):
    """Comprehensive organization model with complete business information."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # Test data flag
    is_test_data = Column(Boolean, default=False, nullable=False)  # True for test organizations

    # Name fields
    name = Column(String(255), nullable=True)  # Display name or primary name
    legal_name = Column(String(255), nullable=False)  # Official legal name
    trade_name = Column(String(255), nullable=True)  # DBA, trade name, alias

    # Organization classification
    organization_type = Column(String(50), nullable=True)  # LLC, Corporation, Nonprofit, etc.
    industry = Column(String(100), nullable=True)  # Broadcasting, Technology, etc.
    sector = Column(String(100), nullable=True)  # Media, Healthcare, etc.

    # Identification
    registration_number = Column(String(100), nullable=True)  # Business registration number
    tax_id = Column(String(50), nullable=True)  # EIN, VAT number, etc.

    # Contact information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=False, default="United States")

    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)

    # Operational data
    founded_date = Column(DateTime(timezone=True), nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    annual_revenue = Column(BigInteger, nullable=True)  # Store in cents for precision
    status = Column(String(20), nullable=False, default="active")  # active, inactive, suspended

    # System metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Legacy settings field (deprecated, use specific fields above)
    settings = Column(JSON, default=dict)

    # Relationships
    shows = relationship("Show", back_populates="organization", cascade="all, delete-orphan")
    speakers = relationship("Speaker", back_populates="organization", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="organization", cascade="all, delete-orphan")


class Show(Base):
    """A show/program under an organization."""
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # Test data flag
    is_test_data = Column(Boolean, default=False, nullable=False)  # True for test shows
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Show settings
    timezone = Column(String(50), nullable=True, default='America/New_York')  # IANA timezone (e.g., America/New_York, America/Los_Angeles)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    settings = Column(JSON, default=dict)  # Show-specific settings

    # Relationships
    organization = relationship("Organization", back_populates="shows")
    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan")
    speakers = relationship("Speaker", back_populates="show", cascade="all, delete-orphan")


class Season(Base):
    """Season/Series - flexible grouping of episodes."""
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)

    # Flexible identification
    name = Column(String(255), nullable=False)  # "Series 1" or "Election 2024"
    number = Column(Integer, nullable=True)  # Optional enumeration
    slug = Column(String(100), nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    show = relationship("Show", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")


class Customer(Base):
    """Customer/Sponsor model for managing advertisers and sponsors."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)

    # Organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Company information
    company_name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)  # Short name for UI display
    industry = Column(String(100), nullable=True)  # Retail, Tech, Healthcare, etc.

    # Primary contact
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_title = Column(String(100), nullable=True)  # Marketing Manager, etc.

    # Billing information
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(Text, nullable=True)

    # Relationship metadata
    customer_type = Column(String(50), default="advertiser")  # advertiser, sponsor, partner
    tier = Column(String(50), default="standard")  # premium, standard, basic
    notes = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_test_data = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="customers")

    def __repr__(self):
        return f"<Customer(id={self.id}, company_name='{self.company_name}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "company_name": self.company_name,
            "display_name": self.display_name or self.company_name,
            "industry": self.industry,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "contact_title": self.contact_title,
            "billing_email": self.billing_email,
            "billing_address": self.billing_address,
            "customer_type": self.customer_type,
            "tier": self.tier,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
