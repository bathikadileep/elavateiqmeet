"""
ElevateIQ — Outbound Webhooks Async Dispatch Engine
===================================================
Dispatches HTTP POST webhooks with HMAC-SHA256 signatures and exponential backoff retries.
"""

import json
import hmac
import hashlib
import logging
import requests
import threading
import time
from typing import Dict, Any
from flask import current_app
from backend.extensions import db
from backend.models.models import WebhookSubscription, WebhookDeliveryLog

log = logging.getLogger("elevateiq.services.webhooks")


class WebhookService:

    @staticmethod
    def dispatch_event(event_type: str, payload: Dict[str, Any], user_id: str = None):
        """
        Asynchronously dispatch webhook event to all subscribed endpoints.
        """
        app = current_app._get_current_object()
        thread = threading.Thread(
            target=WebhookService._async_dispatch,
            args=(app, event_type, payload, user_id),
            daemon=True
        )
        thread.start()

    @staticmethod
    def _async_dispatch(app, event_type: str, payload: Dict[str, Any], user_id: str = None):
        """Worker thread dispatching HTTP POST requests."""
        with app.app_context():
            try:
                query = WebhookSubscription.query.filter_by(is_active=True)
                if user_id:
                    query = query.filter_by(user_id=user_id)
                subscriptions = query.all()

                for sub in subscriptions:
                    if event_type in sub.events_json or "*" in sub.events_json:
                        WebhookService._send_webhook_with_retry(sub, event_type, payload)
            except Exception as e:
                log.warning("Error during webhook async dispatch: %s", e)

    @staticmethod
    def _send_webhook_with_retry(sub: WebhookSubscription, event_type: str, payload: Dict[str, Any]):
        """Send webhook HTTP POST with HMAC-SHA256 signature and exponential retry backoff."""
        body_bytes = json.dumps({"event": event_type, "timestamp": time.time(), "data": payload}).encode("utf-8")
        signature = hmac.new(sub.secret_token.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-ElevateIQ-Event": event_type,
            "X-ElevateIQ-Signature": f"sha256={signature}",
            "User-Agent": "ElevateIQ-Webhook-Engine/1.0"
        }

        max_attempts = 3
        status_code = 0
        response_body = ""
        is_success = False

        for attempt in range(1, max_attempts + 1):
            try:
                res = requests.post(sub.target_url, data=body_bytes, headers=headers, timeout=5)
                status_code = res.status_code
                response_body = res.text[:500]

                if res.status_code in [200, 201, 202, 204]:
                    is_success = True
                    break
            except Exception as err:
                response_body = str(err)[:500]

            time.sleep(0.5 * attempt) # Exponential backoff retry

        log.info("Webhook %s sent to %s | success=%s | status=%d", event_type, sub.target_url, is_success, status_code)
        try:
            delivery_log = WebhookDeliveryLog(
                subscription_id=sub.id,
                event_type=event_type,
                status_code=status_code,
                response_body=response_body,
                attempts=max_attempts,
                is_success=is_success
            )
            db.session.add(delivery_log)
            db.session.commit()
        except Exception as err:
            log.warning("Failed saving webhook delivery log: %s", err)
