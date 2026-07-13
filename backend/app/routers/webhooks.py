from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.post("")
async def receive_webhook(request: Request) -> Response:
    return Response(status_code=202, content='{"status": "not_implemented"}', media_type="application/json")
