from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.utils.logging import logger


class APIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


async def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    api_exc = exc if isinstance(exc, APIException) else APIException(status_code=500, code="INTERNAL_ERROR", message=str(exc))
    logger.error(
        f"API Error {api_exc.status_code}: {api_exc.code} - {api_exc.message}",
        extra={"route": request.url.path}
    )
    return JSONResponse(
        status_code=api_exc.status_code,
        content={
            "error": {
                "code": api_exc.code,
                "message": api_exc.message,
                "details": api_exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    val_exc = exc if isinstance(exc, RequestValidationError) else RequestValidationError([])
    logger.warning(
        f"Validation Error: {val_exc.errors()}",
        extra={"route": request.url.path}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload",
                "details": {"errors": val_exc.errors()}
            }
        }
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"Unhandled Error: {str(exc)}",
        exc_info=exc,
        extra={"route": request.url.path}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred",
                "details": {}
            }
        }
    )
