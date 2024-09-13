from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum


# Определение возможных значений типа организации
class OrganizationType(str, enum.Enum):
    IE = 'IE'
    LLC = 'LLC'
    JSC = 'JSC'


class Organization(Base):
    __tablename__ = 'organization'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(100), nullable=False)
    description = Column(String)
    type = Column(
        Enum(OrganizationType, name='organization_type'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


# Определение перечислений (Enum) для типов организации и статусов
class OrganizationType(str, enum.Enum):
    IE = 'IE'
    LLC = 'LLC'
    JSC = 'JSC'


class TenderStatus(str, enum.Enum):
    CREATED = "CREATED"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class BidStatus(str, enum.Enum):
    CREATED = "CREATED"
    PUBLISHED = "PUBLISHED"
    CANCELED = "CANCELED"


class DecisionType(str, enum.Enum):
    APPROVED = 'Approved'
    REJECTED = 'Rejected'


# Модель сотрудника (Employee)
class Employee(Base):
    __tablename__ = 'employee'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    username = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


# Модель ответственных за организацию (OrganizationResponsible)
class OrganizationResponsible(Base):
    __tablename__ = 'organization_responsible'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organization.id', ondelete='CASCADE'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('employee.id', ondelete='CASCADE'))


# Модель тендера (Tender)
class Tender(Base):
    __tablename__ = 'tender'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=False)
    service_type = Column(String(50))
    status = Column(Enum(TenderStatus), nullable=False, default=TenderStatus.CREATED)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organization.id'))
    creator_username = Column(String(50), ForeignKey('employee.username'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


# Модель предложения (Bid)
class Bid(Base):
    __tablename__ = 'bid'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=False)
    status = Column(Enum(BidStatus), nullable=False, default=BidStatus.CREATED)
    tender_id = Column(UUID(as_uuid=True), ForeignKey('tender.id'))
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organization.id'))
    creator_username = Column(String(50), ForeignKey('employee.username'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


# Модель решения по предложению (BidDecision)
class BidDecision(Base):
    __tablename__ = 'bid_decision'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    bid_id = Column(UUID(as_uuid=True), ForeignKey('bid.id', ondelete='CASCADE'))
    decision = Column(Enum(DecisionType), nullable=False)
    username = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


# Модель отзыва на предложение (BidReview)
class BidReview(Base):
    __tablename__ = 'bid_review'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    bid_id = Column(UUID(as_uuid=True), ForeignKey('bid.id', ondelete='CASCADE'))
    description = Column(String(1000), nullable=False)
    username = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
