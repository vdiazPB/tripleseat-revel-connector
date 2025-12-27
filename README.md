# TripleSeat → Revel Connector

A production-grade API-only connector that processes Triple Seat event webhooks and injects orders into Revel POS.

## Features

- **Webhook-driven**: Processes Triple Seat event updates automatically
- **Idempotent**: Safe replay protection prevents duplicate orders
- **Time-gated**: Only processes events during the configured window
- **Validation**: Ensures events meet all business rules before injection
- **Email notifications**: Success/failure alerts via SendGrid
- **No database**: Stateless design for reliability

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `uvicorn app:app --reload`

## Environment Variables

See `.env.example` for required configuration.

## Webhook Endpoint

```
POST /webhooks/tripleseat
```

The endpoint verifies Triple Seat signatures and processes valid events through the injection pipeline.

## Deployment

Deploy to Render using the provided `render.yaml` configuration.
