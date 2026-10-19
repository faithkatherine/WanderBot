"""
================================================================================
WanderBot — Lambda: Loyalty Points API
================================================================================
Function Name : wanderbot-loyalty-points
Runtime       : Python 3.14

Sits behind an API Gateway REST API with API key authentication.
API Gateway validates the x-api-key header before invoking this Lambda.
The key value is stored in AgentCore Identity and injected by the Gateway.

ENDPOINT
--------
  GET /loyalty/{member_id}
  — Returns loyalty account details for the given member ID (e.g. hz-001).
  — No authorizer. API key validation is handled by API Gateway.

EVENT FORMAT (API Gateway Lambda proxy)
---------------------------------------
  {
    "httpMethod": "GET",
    "path": "/loyalty/hz-001",
    "pathParameters": {"member_id": "hz-001"}
  }

RESPONSE FORMAT
---------------
  {"statusCode": 200, "body": "{...}"}
================================================================================
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Demo loyalty data — keyed by member ID
# ---------------------------------------------------------------------------
LOYALTY_ACCOUNTS = {
    "hz-001": {
        "member_id": "hz-001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "tier": "Gold",
        "points_balance": 4250,
        "cash_value_usd": 42.50,
        "points_expiry_date": "2027-09-15",
        "member_since": "2023-01-10",
    },
    "hz-002": {
        "member_id": "hz-002",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "tier": "Platinum",
        "points_balance": 7820,
        "cash_value_usd": 78.20,
        "points_expiry_date": "2028-03-01",
        "member_since": "2021-06-15",
    },
    "hz-003": {
        "member_id": "hz-003",
        "name": "Carol Davis",
        "email": "carol@example.com",
        "tier": "Silver",
        "points_balance": 340,
        "cash_value_usd": 3.40,
        "points_expiry_date": "2027-06-20",
        "member_since": "2025-06-20",
    },
}


# ---------------------------------------------------------------------------
# Lambda handler — API Gateway proxy integration
# ---------------------------------------------------------------------------

def lambda_handler(event: dict, context) -> dict:
    path_params = event.get("pathParameters") or {}
    member_id = path_params.get("member_id", "").strip().lower()
    logger.info("Request received: %s", json.dumps(event))
    logger.info("Loyalty API invoked: member_id=%s", member_id)

    if not member_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing path parameter: member_id"}),
        }

    account = LOYALTY_ACCOUNTS.get(member_id)
    if not account:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": f"No loyalty account found for member {member_id}"}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps(account),
    }