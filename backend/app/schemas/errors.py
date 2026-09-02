from pydantic import BaseModel
from typing import Dict, Any, Optional


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIErrorResponse(BaseModel):
    error: ErrorBody
