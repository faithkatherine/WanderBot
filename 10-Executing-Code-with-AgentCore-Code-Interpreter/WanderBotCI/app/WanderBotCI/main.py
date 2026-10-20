"""
================================================================================
WanderBot — EXERCISE: AgentCore Code Interpreter
================================================================================
Topic    : Isolated code execution with AgentCore Code Interpreter
Exercise : Add a calculate_trip_cost tool that runs exact arithmetic inside a
           secure, isolated Python sandbox managed by AgentCore.

WHY CODE INTERPRETER?
---------------------
  - LLMs make arithmetic mistakes
  - Running LLM-written code in your app process is unsafe
  - AgentCore spins up an ephemeral sandbox per call — no host access, no
    state leaking between requests (clearContext=True)

EXERCISE INSTRUCTIONS
---------------------
  Step 1 : Import code_session from
  bedrock_agentcore.tools.code_interpreter_client
  Step 2 : Set the REGION constant
  Step 3 : Implement the calculate_trip_cost @tool (template provided below)
  Step 4 : Wire the tool into the Agent and invoke it
================================================================================
"""

import json
import logging
from pathlib import Path

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

# TODO Step 1: Import code_session
from bedrock_agentcore.tools.code_interpreter_client import code_session

logging.basicConfig(level=logging.INFO, format=""
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("WanderBot.CodeInterpreter")

app = BedrockAgentCoreApp()
model = BedrockModel(model_id="us.amazon.nova-2-lite-v1:0")

# TODO Step 2: Set the REGION constant
REGION = "us-east-1"

RATES_PATH = Path(__file__).parent / "datasets" / "exchange_rates.json"
RATES = json.loads(RATES_PATH.read_text())["rates"]

TAX_RATE = 0.12
TIER_DISCOUNT = {"Silver": 0.0, "Gold": 0.08, "Platinum": 0.15}
PRELUDE = (
    "import json, math\n"
    "from decimal import Decimal, ROUND_HALF_UP\n"
    "def money(x):\n"
    "    return float(\n"
    "        Decimal(str(x)).quantize(Decimal('0.01'), \n"
    "        rounding=ROUND_HALF_UP)\n"
    "    )\n"
    f"RATES = {json.dumps(RATES)}\n"
    f"TAX_RATE = {TAX_RATE}\n"
    f"TIER_DISCOUNT = {json.dumps(TIER_DISCOUNT)}\n"
)


# ===========================================================================
# TODO Step 3: Implement the calculate_trip_cost tool
# ===========================================================================

@tool
def calculate_trip_cost(
      code: str, description: str = ""
      ) -> str:  # type: ignore
    """
    Execute Python code in an isolated AgentCore sandbox and return the output.

    Use this for ANY arithmetic involving prices, nights, taxes, discounts,
    loyalty points, currency conversion, or totals. The code must be
    self-contained and must print() the final result.

    Predefined in the sandbox (use these, never hard-code your own values):
        RATES: dict of exchange rates from USD, e.g. RATES["GBP"]
        TAX_RATE: 0.12
        TIER_DISCOUNT: {"Silver": 0.0, "Gold": 0.08, "Platinum": 0.15}
        json and math are already imported.
        money(x): rounds a currency amount to 2 decimals.
        Wrap every monetary value you print.

    Args:
        code: Complete Python script. Print results as JSON,
              e.g. print(json.dumps({"total_usd": total})).
        description: Short note on what the calculation does.
    """

    if description:
        code = f"# {description}\n{code}"
    code = PRELUDE + code

    # Print the LLM-generated code so you can see what the agent wrote
    print(f"\nGenerated Code:\n{code}\n")

    try:
        with code_session(REGION) as code_client:
            response = code_client.invoke("executeCode", {
                "code": code,
                "language": "python",
                "clearContext": True,
            })

        for event in response["stream"]:
            return json.dumps(event["result"])

        return json.dumps({
            "error": "Sandbox returned no output. "
            "Make sure the code calls print()."
        })

    except Exception as e:
        logger.warning("Code Interpreter unavailable: %s", e)
        return json.dumps({
            "error": "Exact calculation unavailable: "
            "the secure sandbox could not be reached.",
            "detail": str(e)[:200],
            "instruction": "Do not estimate the total. "
                           "Tell the customer the exact breakdown "
                           "cannot be calculated right now and "
                           "ask them to try again shortly.",
        })


SYSTEM_PROMPT = """
You are WanderBot, the AI travel assistant for Horizon Travel.

You have access to the calculate_trip_cost tool, which runs exact arithmetic
inside a secure, isolated Python sandbox via the AgentCore Code Interpreter.

USE calculate_trip_cost WHENEVER a customer asks about:
- Hotel stay totals (nights * rate, taxes, multi-room bookings)
- Trip totals with flights, loyalty discounts, points, or currency conversion
- Any "how much will it cost if..." question

Pricing rules for trip totals:
(use the predefined RATES, TAX_RATE, TIER_DISCOUNT):
1. Base = flight price + nightly rate x nights.
2. Apply the loyalty tier discount from TIER_DISCOUNT to the base.
3. Points: round the balance down to the nearest 100; 100 points = $1;
   the redemption is capped at 50% of the base.
4. Apply TAX_RATE to the amount remaining after the discount and points.
5. Convert the final USD total to the requested currency using RATES.
6. Points earned = 1 point per $1 of the final USD total, rounded down.

RULES for the code you write:
- Use TAX_RATE, TIER_DISCOUNT and RATES. 
Never type tax rates, discounts or exchange rates yourself.
- Wrap every monetary value you print in money(), never round().
- json, math and money() are already defined; do not redefine them.

Always write a short Python script that computes the answer and prints the
breakdown as JSON. Never estimate or guess numbers yourself. If the tool
returns an error, explain that the exact total cannot be calculated right now.
Present the result clearly with a brief explanation."""


@app.entrypoint
async def invoke(payload: dict, context=None) -> dict:
    """WanderBot — Code Interpreter entry point."""
    raw = payload.get("message") or payload.get("prompt") or "Hello!"
    try:
        user_message = json.loads(raw).get("message", raw)
    except (json.JSONDecodeError, AttributeError):
        user_message = raw

    logger.info("User: %s", user_message[:80])

    # Step 4: Build the Agent with calculate_trip_cost and invoke it
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[calculate_trip_cost],
    )
    response = agent(user_message)
    logger.info("Assistant: %s", str(response)[:100])
    return {"response": str(response)}


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run()
