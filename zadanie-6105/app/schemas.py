from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class TenderStatus(str, Enum):
    CREATED = "CREATED"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class BidStatus(str, Enum):
    CREATED = "CREATED"
    PUBLISHED = "PUBLISHED"
    CANCELED = "CANCELED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TenderBase(BaseModel):
    name: str
    description: str
    service_type: Optional[str]
    organization_id: UUID
    creator_username: str


class TenderCreate(TenderBase):
    pass


class TenderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[str] = None
    organization_id: Optional[UUID] = None
    creator_username: Optional[str] = None


class Tender(TenderBase):
    id: UUID
    status: TenderStatus  # Используем перечисление для статуса
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class BidBase(BaseModel):
    name: str
    description: str
    tender_id: UUID
    organization_id: UUID
    creator_username: str


class BidCreate(BidBase):
    pass


class Bid(BidBase):
    id: UUID
    status: BidStatus  # Используем перечисление для статуса
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
