from fastapi import APIRouter, HTTPException, Request, Response

from app.vcs.factory import detect_vcs_type, get_provider

router = APIRouter()


@router.post("")
async def receive_webhook(request: Request) -> Response:
    headers = dict(request.headers)
    raw_body = await request.body()

    vcs_type = detect_vcs_type(headers)
    if vcs_type is None:
        raise HTTPException(status_code=400, detail="Unknown VCS provider")

    provider = get_provider(vcs_type.value)

    if not provider.validate_webhook(headers, raw_body):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    body = await request.json()
    event = provider.parse_webhook_event(headers, body)

    return Response(
        status_code=202,
        content=f'{{"status": "accepted", "vcs": "{event.vcs_type.value}", "pr": {event.pr_number}}}',
        media_type="application/json",
    )
