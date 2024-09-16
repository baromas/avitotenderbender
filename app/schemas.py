from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class TenderStatus(str, Enum):
    CREATED = "Created"
    PUBLISHED = "Published"
    CLOSED = "Closed"


class TenderServiceType(str, Enum):
    CONSTRUCTION = "Construction"
    DELIVERY = "Delivery"
    MANUFACTURE = "Manufacture"


class TenderBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    service_type: TenderServiceType
    organization_id: UUID
    creator_username: str
    version: int = Field(default=1, ge=1)


class TenderCreate(TenderBase):
    pass


class TenderUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    service_type: Optional[TenderServiceType] = None
    organization_id: Optional[UUID] = None
    creator_username: Optional[str] = None
    version: Optional[int] = Field(default=1, ge=1)


class TenderHistoryBase(BaseModel):
    tender_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[TenderServiceType] = None
    status: Optional[TenderStatus] = None
    organization_id: Optional[UUID] = None
    creator_username: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TenderHistoryCreate(TenderHistoryBase):
    pass


class TenderHistory(TenderHistoryBase):
    id: UUID


class Tender(TenderBase):
    id: UUID = Field(...)
    status: TenderStatus = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        orm_mode = True
        use_enum_values = True
        allow_population_by_field_name = True


class BidStatus(str, Enum):
    CREATED = "Created"
    PUBLISHED = "Published"
    CANCELED = "Canceled"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class BidBase(BaseModel):
    name: str
    description: str
    tender_id: UUID
    organization_id: UUID
    creator_username: str


class AuthorType(str, Enum):
    USER = "User"
    ORGANIZATION = "Organization"


class BidCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    tenderId: UUID
    authorType: AuthorType
    authorId: UUID


class Bid(BaseModel):
    id: UUID
    name: str
    description: str
    tender_id: UUID
    status: str
    authorType: AuthorType
    authorId: UUID
    version: int
    createdAt: datetime

    class Config:
        orm_mode = True
