"""
ElevateIQ — Enterprise SAML 2.0 & OIDC Single Sign-On APIs
===========================================================
API Endpoints:
  - GET  /api/sso/metadata/<tenant_domain>    → Download SP Metadata XML for IdP setup
  - POST /api/sso/saml/acs                    → SAML Assertion Consumer Service Endpoint
  - GET  /api/sso/oidc/authorize              → Construct OIDC login authorization URL
  - POST /api/sso/oidc/callback               → Process OIDC auth code token exchange
"""

import logging
from flask import Blueprint, jsonify, request, Response, redirect
from backend.services.sso_service import SSOService

sso_bp = Blueprint("sso", __name__, url_prefix="/api/sso")
log = logging.getLogger("elevateiq.sso")


@sso_bp.route("/metadata/<string:tenant_domain>", methods=["GET"])
def get_sp_metadata(tenant_domain):
    """Generate SP Metadata XML file for enterprise SAML IdP configuration."""
    entity_id = f"https://elevateiq.com/sso/saml/{tenant_domain}"
    acs_url = f"https://elevateiq.com/api/sso/saml/acs?tenant={tenant_domain}"
    metadata_xml = SSOService.generate_saml_sp_metadata(entity_id, acs_url)
    return Response(metadata_xml, mimetype="application/xml", headers={
        "Content-Disposition": f"attachment; filename=elevateiq_sp_metadata_{tenant_domain}.xml"
    })


@sso_bp.route("/saml/acs", methods=["POST"])
def saml_acs():
    """Assertion Consumer Service endpoint receiving base64 SAMLResponse from IdP."""
    tenant_domain = request.args.get("tenant", "default.com")
    saml_response = request.form.get("SAMLResponse") or request.json.get("SAMLResponse") if request.is_json else None

    if not saml_response:
        return jsonify({"error": "SAMLResponse parameter missing"}), 400

    try:
        auth_data = SSOService.process_saml_assertion(saml_response, tenant_domain)
        return jsonify(auth_data), 200
    except Exception as err:
        log.warning("SAML ACS verification failed for tenant %s: %s", tenant_domain, err)
        return jsonify({"error": str(err)}), 401


@sso_bp.route("/oidc/authorize", methods=["GET"])
def oidc_authorize():
    """Redirect user to enterprise Azure AD / Okta OIDC login screen."""
    client_id = request.args.get("client_id", "elevateiq-enterprise-client")
    redirect_uri = request.args.get("redirect_uri", "https://elevateiq.com/api/sso/oidc/callback")
    state = request.args.get("state", "random_nonce_12345")
    auth_url = SSOService.build_oidc_authorization_url(client_id, redirect_uri, state)
    return redirect(auth_url)
