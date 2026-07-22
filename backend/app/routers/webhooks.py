from json import JSONDecodeError

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.services.review_service import accept_review
from app.vcs.factory import detect_vcs_type, get_provider

router = APIRouter()


@router.post("")
async def receive_webhook(request: Request) -> JSONResponse:
    headers = dict(request.headers)
    raw_body = await request.body()

    vcs_type = detect_vcs_type(headers)
    if vcs_type is None:
        raise HTTPException(status_code=400, detail="Unknown VCS provider")

    try:
        provider = get_provider(vcs_type.value)
    except ValueError as exc:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, str(exc)) from exc

    if not provider.validate_webhook(headers, raw_body):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        body = await request.json()
        event = provider.parse_webhook_event(headers, body)
    except (JSONDecodeError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    if event is None:
        return JSONResponse(status_code=202, content={"status": "ignored"})

    try:
        review, created = await accept_review(event)
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Unable to queue review") from exc
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted" if created else "duplicate",
            "review_id": str(review.id),
            "vcs": event.vcs_type.value,
            "pr": event.pr_number,
        },
    )
