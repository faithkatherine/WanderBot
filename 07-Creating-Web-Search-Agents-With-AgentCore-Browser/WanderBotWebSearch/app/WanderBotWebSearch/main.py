"""
================================================================================
WanderBot — EXERCISE: AgentCore Browser
================================================================================
Topic    : Live web browsing with AgentCoreBrowser
Exercise : Give WanderBot a browser so it can look up destination information
           from Wikivoyage in real time

EXERCISE INSTRUCTIONS
---------------------
  Step 1: Import AgentCoreBrowser from strands_tools.browser
  Step 2: In invoke(), instantiate AgentCoreBrowser() and create the agent
          with browser.browser to the agent's tools list
================================================================================
"""

import json
import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
import nest_asyncio
import playwright
# TODO Step 1: Import AgentCoreBrowser from strands_tools.browser
from strands_tools.browser import AgentCoreBrowser


logging.basicConfig(level=logging.INFO, format=""
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("WanderBot.AgentCoreBrowser")

app = BedrockAgentCoreApp()
model = BedrockModel(model_id="us.amazon.nova-2-lite-v1:0")

SYSTEM_PROMPT = """
You are WanderBot, the AI travel assistant for Horizon Travel.


You have access to a live web browser.
When starting a browser session, use a session_name of lowercase letters,
numbers and hyphens only (e.g. "tokyo-guide"). Never use underscores.
Use it to look up destination information
on Wikivoyage (en.wikivoyage.org) — a free, open travel guide.

When a customer asks about a destination:
1. Navigate to en.wikivoyage.org/wiki/<DestinationName>
2. Read the page — focus on highlights, neighbourhoods, and practical tips
3. Summarise what you find clearly and concisely

Always tell the customer that the information came from Wikivoyage.
If a tool fails, tell the customer and
do not answer from memory as if it were live data.
"""


@app.entrypoint
async def invoke(payload: dict, context=None) -> dict:
    """WanderBot — AgentCore Browser entry point."""
    raw = payload.get("message") or payload.get("prompt") or "Hello!"
    try:
        # Handles the CLI wrapping a JSON string:
        # {"prompt": '{"message": "..."}'}
        user_message = json.loads(raw).get("message", raw)
    except (json.JSONDecodeError, AttributeError):
        # Plain-text prompt
        user_message = raw

    logger.info("User: %s", user_message[:80])

    # TODO Step 2: Instantiate AgentCoreBrowser (session_timeout=600 is fine)
    # and create an agent with browser.browser to the agent's tools list
    browser = AgentCoreBrowser(session_timeout=600)
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[browser.browser]
    )

    response = agent(user_message)
    return response


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run()
