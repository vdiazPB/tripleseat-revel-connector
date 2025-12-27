from fastapi import FastAPI, Request, HTTPException
import logging
from integrations.tripleseat.webhook_handler import handle_tripleseat_webhook
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TripleSeat-Revel Connector")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhooks/tripleseat")
async def tripleseat_webhook(request: Request):
    try:
        await handle_tripleseat_webhook(request)
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        # Always return 200 OK as per spec
        return {"status": "received"}