import os
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}


def verify_tripleseat_signature(
    raw_body: bytes,
    received_signature: str,
    secret: str
) -> bool:
    computed = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed, received_signature)


@app.post("/webhooks/tripleseat")
async def tripleseat_webhook(request: Request):
    secret = os.getenv("TRIPLESEAT_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    raw_body = await request.body()

    # Try common Triple Seat signature headers
    signature = (
        request.headers.get("X-Tripleseat-Signature")
        or request.headers.get("Tripleseat-Signature")
    )

    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    if not verify_tripleseat_signature(raw_body, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Signature verified — safe to parse payload
    payload = await request.json()

    # TEMP: log minimal info only (do not log full payload in prod)
    print("✅ Triple Seat webhook verified")

    return {"status": "accepted"}
