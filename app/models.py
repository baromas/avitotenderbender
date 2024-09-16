from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
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


class TenderStatus(str, enum.Enum):
    Created = "Created"
    Published = "Published"
    Closed = "Closed"


class TenderServiceType(str, enum.Enum):
    Construction = "Construction"
    Delivery = "Delivery"
    Manufacture = "Manufacture"


class TenderHistory(Base):
    __tablename__ = 'tender_history'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    tender_id = Column(UUID(as_uuid=True), ForeignKey('tender.id', ondelete='CASCADE'))
    name = Column(String(100), nullable=True)
    description = Column(String, nullable=True)
    service_type = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    organization_id = Column(UUID, nullable=True)
    creator_username = Column(String(50), nullable=True)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class BidStatus(str, enum.Enum):
    Created = "Created"
    Published = "Published"
    Canceled = "Canceled"


class DecisionType(str, enum.Enum):
    Approved = 'Approved'
    Rejected = 'Rejected'


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
    service_type = Column(Enum(TenderServiceType, name='tender_service_type'), nullable=False)
    status = Column(Enum(TenderStatus, name='tender_status'), nullable=False, default=TenderStatus.Created)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organization.id'))
    creator_username = Column(String(50), ForeignKey('employee.username'))
    version = Column(Integer(), nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


# Модель предложения (Bid)
class Bid(Base):
    __tablename__ = 'bid'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=False)
    status = Column(Enum(BidStatus), nullable=False, default=BidStatus.Created)
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
