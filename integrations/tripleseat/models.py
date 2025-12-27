from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    reason: Optional[str] = None

@dataclass
class OrderDetails:
    revel_order_id: str
    subtotal: float
    discount: float
    final_total: float
    payment_type: Optional[str] = None

@dataclass
class InjectionResult:
    success: bool
    order_details: Optional[OrderDetails] = None
    error: Optional[str] = None