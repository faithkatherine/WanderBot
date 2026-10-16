"""
================================================================================
WanderBot — EXERCISE: AgentCore Gateway
================================================================================
Topic     : Calling Lambda-backed tools via AgentCore Gateway and MCP
Exercise  : Connect WanderBot to the Gateway using MCPClient
and MCP tool discovery

ARCHITECTURE
------------
  WanderBot (Strands Agent)
      ↓  tool call (MCP protocol)
  AgentCore Gateway  (No Authentication)
      ↓  direct Lambda invocation
  booking_lambda.py
"""

import json
import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp.mcp_client import MCPClient

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("WanderBot.AgentCoreGateway")

# ---------------------------------------------------------------------------
# App and model
# ---------------------------------------------------------------------------
app = BedrockAgentCoreApp()
model = BedrockModel(model_id="us.amazon.nova-2-lite-v1:0")

# ---------------------------------------------------------------------------
# Gateway endpoint — set via environment variable
# ---------------------------------------------------------------------------
GATEWAY_ENDPOINT = (
    "https://wanderbot-gateway-t2kkoaaf4m.gateway."
    "bedrock-agentcore.us-east-1.amazonaws.com/mcp"
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are WanderBot, the AI travel assistant for Horizon Travel.

You have access to tools via the AgentCore Gateway:
- get_booking(booking_ref)     : Retrieve a booking by reference (e.g. BK-1001)
- list_bookings_by_email(email): List all bookings for a customer email

Use these tools to help customers with their bookings.
Present results clearly and ask clarifying questions when needed."""


# ===========================================================================
# ENTRY POINT
# ===========================================================================

@app.entrypoint
async def invoke(payload: dict, _context=None) -> dict:
    """
    WanderBot — AgentCore Gateway entry point.

    Payload keys:
        message or prompt (str): User's prompt
    """
    # Handle both direct message and CLI-wrapped prompt
    if "prompt" in payload:
        # AgentCore CLI wraps input in {"prompt": '{"message": "..."}'}
        prompt_data = json.loads(payload["prompt"])
        user_message = prompt_data.get("message", "Hello!")
    else:
        user_message = payload.get("message", "Hello!")

    logger.info("User: %s", user_message[:100])

    # Step 2: Connection to the Gateway using MCPClient
    client = MCPClient(
        lambda: streamable_http_client(GATEWAY_ENDPOINT)  # type: ignore
    )

    # Step 3: Discover all tools registered in the Gateway
    # Step 4: Create the Agent with discovered tools and invoke it
    with client:
        tools = client.list_tools_sync()
        logger.info("Discovered %d tools from Gateway", len(tools))
        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
        )

        response = agent(user_message)
        logger.info("Assistant: %s", str(response)[:100])

        return {"response": response}


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run()
