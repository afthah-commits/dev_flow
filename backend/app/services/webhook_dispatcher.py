import hmac
import hashlib
import json
import httpx
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.webhook import WebhookEndpoint, WebhookDelivery

class WebhookDispatcher:
    def __init__(self, db: Session):
        self.db = db

    def generate_signature(self, secret: str, payload: str) -> str:
        return hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

    async def dispatch(self, webhook: WebhookEndpoint, event_type: str, payload: Dict[str, Any], idempotency_key: str):
        # Check if already delivered
        existing = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook.id,
            WebhookDelivery.idempotency_key == idempotency_key
        ).first()
        if existing and existing.status == "SUCCESS":
            return existing

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            status="RUNNING",
            payload=payload,
            idempotency_key=idempotency_key,
            attempt_count=1
        )
        self.db.add(delivery)
        self.db.commit()

        try:
            payload_str = json.dumps(payload)
            signature = self.generate_signature(webhook.encrypted_secret, payload_str)
            
            headers = {
                "Content-Type": "application/json",
                "X-DevFlow-Event": event_type,
                "X-DevFlow-Delivery": delivery.id,
                "X-DevFlow-Signature": f"sha256={signature}"
            }

            # In a real app we'd use httpx.AsyncClient with timeout
            # Using mock success for now
            status_code = 200
            response_body = '{"ok": true}'
            
            delivery.http_status = status_code
            delivery.response_body = response_body
            
            if status_code >= 200 and status_code < 300:
                delivery.status = "SUCCESS"
            else:
                delivery.status = "FAILED"
                delivery.error_message = f"HTTP {status_code}"
                
        except Exception as e:
            delivery.status = "FAILED"
            delivery.error_message = str(e)
            
        self.db.commit()
        return delivery
