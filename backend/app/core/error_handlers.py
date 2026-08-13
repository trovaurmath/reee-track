from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ApplicationError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        request: Request,
        exception: ApplicationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exception.status_code,
            content={
                "error": exception.code,
                "message": exception.message,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

