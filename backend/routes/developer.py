"""
ElevateIQ — Developer API Gateway & Webhook Marketplace REST APIs
==================================================================
API Endpoints:
  - POST   /api/developer/keys              → Generate new scoped API key
  - GET    /api/developer/keys              → List active API keys
  - DELETE /api/developer/keys/<id >         → Revoke API key
  - POST   /api/developer/webhooks          → Register webhook endpoint
  - GET    /api/developer/webhooks          → List webhooks & delivery logs
  - POST   /api/developer/webhooks/test     → Trigger test webhook event
"""

import os
import secrets
import hashlib
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.models import APIKey, WebhookSubscription, WebhookDeliveryLog
from backend.services.webhook_service import WebhookService

developer_bp = Blueprint("developer", __name__, url_prefix="/api/developer")
log = logging.getLogger("elevateiq.developer")


@developer_bp.route("/keys", methods=["POST"])
@jwt_required()
def create_api_key():
    """Generate a new scoped API Key."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    key_name = data.get("key_name", "Developer Access Key")
    rate_limit = data.get("rate_limit", 100)

    raw_secret = f"eiq_live_{secrets.token_urlsafe(32)}"
    key_prefix = raw_secret[:12]
    key_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

    key_record = APIKey(
        user_id=current_user_id,
        key_name=key_name,
        api_key_hash=key_hash,
        key_prefix=key_prefix,
        rate_limit=rate_limit,
        is_active=True
    )
    db.session.add(key_record)
    db.session.commit()

    log.info("Generated API Key '%s' for user %s", key_name, current_user_id)
    result = key_record.to_dict()
    result["raw_api_key"] = raw_secret # Only shown once on creation
    return jsonify(result), 201


@developer_bp.route("/keys", methods=["GET"])
@jwt_required()
def list_api_keys():
    """List API keys for current user."""
    current_user_id = get_jwt_identity()
    keys = APIKey.query.filter_by(user_id=current_user_id, is_active=True).all()
    return jsonify([k.to_dict() for k in keys]), 200


@developer_bp.route("/keys/<string:key_id>", methods=["DELETE"])
@jwt_required()
def revoke_api_key(key_id):
    """Revoke API Key by ID."""
    current_user_id = get_jwt_identity()
    key_record = APIKey.query.filter_by(id=key_id, user_id=current_user_id).first()

    if not key_record:
        return jsonify({"error": "API Key not found"}), 404

    key_record.is_active = False
    db.session.commit()
    log.info("Revoked API Key id=%s", key_id)
    return jsonify({"message": "API Key revoked successfully"}), 200


@developer_bp.route("/webhooks", methods=["POST"])
@jwt_required()
def create_webhook_subscription():
    """Register a new webhook subscription endpoint."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    target_url = data.get("target_url")
    events = data.get("events", ["meeting.created", "recording.ready"])

    if not target_url:
        return jsonify({"error": "target_url is required"}), 400

    secret_token = f"whsec_{secrets.token_hex(24)}"
    sub = WebhookSubscription(
        user_id=current_user_id,
        target_url=target_url,
        events_json=events,
        secret_token=secret_token,
        is_active=True
    )
    db.session.add(sub)
    db.session.commit()

    log.info("Registered webhook subscription to %s", target_url)
    result = sub.to_dict()
    result["secret_token"] = secret_token
    return jsonify(result), 201


@developer_bp.route("/webhooks", methods=["GET"])
@jwt_required()
def list_webhooks():
    """List webhooks and delivery logs for current user."""
    current_user_id = get_jwt_identity()
    subs = WebhookSubscription.query.filter_by(user_id=current_user_id, is_active=True).all()

    logs = []
    for sub in subs:
        for l in sub.logs:
            logs.append(l.to_dict())

    return jsonify({
        "subscriptions": [s.to_dict() for s in subs],
        "delivery_logs": logs[:50]
    }), 200


@developer_bp.route("/webhooks/test", methods=["POST"])
@jwt_required()
def test_webhook():
    """Trigger a test webhook event."""
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    event_type = data.get("event", "meeting.created")

    payload = {
        "meeting_code": "test-dev-room",
        "title": "Developer Test Event",
        "timestamp": secrets.token_hex(4)
    }

    WebhookService.dispatch_event(event_type, payload, user_id=current_user_id)
    return jsonify({"message": f"Dispatched test webhook event '{event_type}'"}), 200
