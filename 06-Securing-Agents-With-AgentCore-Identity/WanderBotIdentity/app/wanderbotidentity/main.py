"""
================================================================================
WanderBot — EXERCISE: AgentCore Identity
================================================================================

NOTE
----
No code changes are required in this exercise. The agent code from the
previous lesson works as-is. Your task is entirely infrastructure:

  1. Deploy the loyalty Lambda
  2. Create a REST API in API Gateway with API key required
  3. Create an API key and a usage plan, and associate them
  4. Store the API key in AgentCore Identity
  5. Add the API as a target in the existing Gateway, wired to the Identity

Once that is done, set GATEWAY_ENDPOINT below to your Gateway URL and run
this file. No code edits needed.

See README.md for the full step-by-step.
================================================================================
"""

import os
import json
import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp.client.streamable_http import streamable_http_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient

logging.basicConfig(level=logging.INFO, format=""
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("WanderBot.AgentCoreIdentity")

app = BedrockAgentCoreApp()
model = BedrockModel(model_id="us.amazon.nova-2-lite-v1:0")

# TODO: Set this to your Gateway endpoint here
GATEWAY_ENDPOINT = os.environ.get(
    "GATEWAY_ENDPOINT", "https://your-gateway-endpoint.amazonaws.com")

SYSTEM_PROMPT = """
You are WanderBot, the AI travel assistant for Horizon Travel.

All of your tools are provided dynamically through the AgentCore Gateway.
Discover the available tools at runtime and use them to
answer customer questions about bookings, travel plans, and account details.

Guidelines:
- Rely on the tools available to you through the Gateway
— do not assume capabilities that aren't exposed as tools.
- Choose the most relevant tool for each request and
call it with the required parameters.
- If a request needs information across multiple tools, call them in sequence
and combine the results.
- If no available tool can fulfil a request,
say so clearly instead of guessing.
- Ask clarifying questions when the user's request is ambiguous
or missing required details.
- Present results in a clear, concise, customer-friendly format."""


@app.entrypoint
async def invoke(payload: dict, context=None) -> dict:
    # Handle both direct message and CLI-wrapped prompt
    raw = payload.get("message") or payload.get("prompt") or "Hello!"
    try:
        # Handles the CLI wrapping a JSON string:
        # {"prompt": '{"message": "..."}'}
        user_message = json.loads(raw).get("message", raw)
    except (json.JSONDecodeError, AttributeError):
        # Plain-text prompt
        user_message = raw

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


if __name__ == "__main__":
    app.run()
