from fastapi import Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    """Raised by a repository when a row doesn't exist. Mapped to a 404 below."""

    def __init__(self, resource: str, identifier: object):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} {identifier} not found")


class ConflictError(Exception):
    """Raised when a create request would duplicate an existing record."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.detail})
