# models.py
from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class AlertImportance(str, Enum):
    INFORMATION = "Information"
    WARNING = "Warning"
    CRITICAL = "Critical"

class AssetClass(str, Enum):
    EQUITIES = "Equities"
    FIXED_INCOME = "Fixed Income"
    COMMODITIES = "Commodities"
    FX = "FX"
    CRYPTO = "Crypto"

class Underlier(BaseModel):
    id: str
    name: str
    asset_class: AssetClass

class Process(BaseModel):
    id: str
    name: str
    description: str

class AlertStatus(str, Enum):
    NEW = "New"
    ACKNOWLEDGED = "Acknowledged"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"

class Alert(BaseModel):
    id: str
    timestamp: datetime
    importance: AlertImportance
    title: str
    description: str
    asset_classes: List[AssetClass]
    underliers: List[Underlier]
    processes: List[Process]
    status: AlertStatus = AlertStatus.NEW
    assigned_to: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    comments: Optional[str] = None