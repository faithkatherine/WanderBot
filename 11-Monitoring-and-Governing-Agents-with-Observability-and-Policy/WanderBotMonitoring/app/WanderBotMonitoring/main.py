"""
================================================================================
WanderBot — EXERCISE: AgentCore Native Observability
================================================================================
Topic    : Observability for agents and tool calls via AgentCore's built-in
           OpenTelemetry instrumentation.
Exercise : Wire up WanderBot with search_flights and search_hotels, then
           observe the agent in the CloudWatch GenAI Observability Dashboard.

EXERCISE INSTRUCTIONS
---------------------
  Step 1 : Uncomment the search_flights @tool
  Step 2 : Uncomment the search_hotels @tool
  Step 3 : Wire both tools into the Agent and invoke it
================================================================================
"""

import json
import logging
from pathlib import Path

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

logging.basicConfig(level=logging.INFO, format=""
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("WanderBot.Observability")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datasets"
print(f"DATA_DIR: {DATA_DIR}")

app = BedrockAgentCoreApp()
model = BedrockModel(model_id="us.amazon.nova-2-lite-v1:0")


# ===========================================================================
# TODO Step 1: Implement search_flights
#
@tool
def search_flights(origin: str, destination: str) -> str:
    """Search available flights between two cities."""
    flights = json.loads((DATA_DIR / "flights.json").read_text())
    matches = [
        f for f in flights
        if f.get("origin", "").upper() == origin.upper()
        and f.get("destination", "").upper() == destination.upper()
        and f.get("status") != "CANCELLED"
    ]
    if not matches:
        return f"No flights found from {origin} to {destination}."
    return json.dumps(matches[:5], indent=2)
# ===========================================================================


# ===========================================================================
# TODO Step 2: Implement search_hotels
#
@tool
def search_hotels(city: str, max_price: float = 500.0) -> str:
    """Search available hotels in a city with an optional maximum price."""
    hotels = json.loads((DATA_DIR / "hotels.json").read_text())
    matches = [
        h for h in hotels
        if h.get("location", "").lower() == city.lower()
        and h.get("available", True)
        and h.get("price_per_night_usd", 0) <= max_price
    ]
    if not matches:
        return f"No hotels found in {city} under ${max_price}/night."
    return json.dumps(matches[:5], indent=2)
# ===========================================================================


SYSTEM_PROMPT = """
You are WanderBot, the AI travel assistant for Horizon Travel.

Use search_flights to find available flights and
search_hotels to find accommodation.
Always confirm routes and availability before making recommendations."""


@app.entrypoint
async def invoke(payload: dict, context=None) -> dict:
    """WanderBot — observability exercise entry point."""
    raw = payload.get("message") or payload.get("prompt") or "Hello!"
    try:
        user_message = json.loads(raw).get("message", raw)
    except (json.JSONDecodeError, AttributeError):
        user_message = raw
    logger.info("User: %s", user_message[:80])

    # TODO Step 3: Build the Agent with both tools and invoke it
    #
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[search_flights, search_hotels],
    )
    response = agent(user_message)
    return response
    pass


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run()
