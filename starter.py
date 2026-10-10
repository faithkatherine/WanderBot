import asyncio
import json

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator

app = BedrockAgentCoreApp()
MODEL_ID = "us.amazon.nova-lite-v1:0"
model = BedrockModel(model_id=MODEL_ID)
SYSTEM_PROMPT = """
You are WanderBot, Horizon Travel's helpful assistant.

POLICIES:
Baggage:
- Economy: 1 free checked bag (23kg max), $50 per additional bag
- Business: 2 free checked bags (32kg max), $40 per additional bag
- Carry-on: 1 bag + 1 personal item included (all classes)

Check-in:
- Online check-in: 24 hours before departure
- Airport check-in: Close 45 min before domestic, 60 min international

Cabin Classes:
- Economy: Standard seating, meals on long-haul flights
- Business: Lie-flat seats, priority boarding, lounge access, premium meals
- Upgrade fee: $200-$500 depending on route

Cancellation:
- Cancel >7 days before: Full refund minus $50 fee
- Cancel 1-7 days before: 50% refund
- Cancel <24 hours: No refund

IMPORTANT: Always use the calculator tool for ANY numeric calculation,
including addition, multiplication, totals, or conversions. Never do
arithmetic yourself.
"""


@app.entrypoint
async def invoke(payload: dict, context=None) -> dict:
    # AgentCore uses 'prompt' for the user message
    # Fall back to 'message' for local testing compatibility
    user_message = payload.get("prompt") or payload.get("message", "Hello!")

    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[calculator],
    )
    response = agent(user_message)
    # AgentResult has the final output in the content attribute
    return {"response": str(response)}

if __name__ == "__main__":
    # Local testing (run with: python starter.py)
    # For AgentCore dev server: agentcore dev
    # Deploy to runtime: agentcore deploy --auto-update-on-conflict

    # Example test payloads
    test_payload = {
        "message": (
            "I have 3 bags in economy. How much will extra baggage cost?"
        )
    }

    # More test scenarios:
    # {"message": "When should I arrive for an international flight?"}
    # {"message": "What's included in business class?"}
    # {"message": "If I cancel 5 days before, what refund do I get?"}

    response = asyncio.run(invoke(test_payload))
    print(json.dumps(response, indent=2))
