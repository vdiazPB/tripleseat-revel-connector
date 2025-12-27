from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhooks/tripleseat")
async def tripleseat_webhook(request: Request):
    payload = await request.json()
    return {"received": True}
