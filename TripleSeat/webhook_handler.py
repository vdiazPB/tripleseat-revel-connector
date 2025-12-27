from fastapi import FastAPI, Request
from datetime import datetime

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhooks/tripleseat")
async def tripleseat_webhook(request: Request):
    payload = await request.json()

    # Minimal defensive logging (safe)
    event_id = payload.get("event", {}).get("id")
    new_status = payload.get("event", {}).get("status")

    print(
        f"[TripleSeat] Webhook received | "
        f"event_id={event_id} | status={new_status}"
    )

    # Always acknowledge receipt
    # Business logic happens downstream
    return {"status": "received"}
