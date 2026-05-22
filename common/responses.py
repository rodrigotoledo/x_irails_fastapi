from fastapi import Response
from fastapi.responses import JSONResponse


def data_response(data: object, status_code: int = 200) -> JSONResponse:
    return JSONResponse({"data": data}, status_code=status_code)


def paginated_response(
    data: list[object], page: int, limit: int, total: int, status_code: int = 200
) -> JSONResponse:
    return JSONResponse(
        {
            "data": data,
            "meta": {"page": page, "limit": limit, "total": total},
        },
        status_code=status_code,
    )


def error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict | None = None,
) -> JSONResponse:
    return JSONResponse(
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
        status_code=status_code,
    )


def no_content_response() -> Response:
    return Response(status_code=204)