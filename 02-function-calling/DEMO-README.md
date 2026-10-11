# Demo: Function Calling

## Topic
Custom `@tool` functions + built-in `current_time` tool

## Duration
~7 minutes

## Demo Flow
1. **(1 min)** Recap — stateless agent with built-in calculator
2. **(2 min)** Introduce the `@tool` decorator: write a custom flight search tool that reads from `flights.json`
3. **(1 min)** Show the `current_time` built-in tool — zero code, just import
4. **(2 min)** Run `agentcore dev` and invoke with multi-tool queries
5. **(1 min)** Show how Strands automatically chains tool calls

## Key Concepts
- **@tool decorator**: turns any Python function into an agent-callable tool
  - Docstring = tool description (the LLM reads this!)
  - Type hints = parameter schema (must be annotated)
- **current_time**: built-in Strands tool — returns the current UTC/local time
- **Tool chaining**: agent can call multiple tools in sequence automatically
- **JSON file reading**: data stays local

## Talking Points
- "Notice the docstring — this is what the LLM uses to decide WHEN to call this tool. Write it like you're explaining the tool to a smart colleague."
- "The type hints on parameters aren't optional — Strands uses them to build the JSON schema that the model receives."
- "Watch how Strands calls `search_flights`, gets the results

## Setup
```bash
pip install -r requirements.txt
```

## How to Run
```bash
agentcore dev
agentcore invoke --dev '{"message": "Are there any flights from London to Paris on 15 March 2026?"}'

agentcore configure
agentcore deploy
agentcore invoke '{"message": "What time is it right now, and are there morning flights from JFK to LAX today?"}'
agentcore invoke '{"message": "Show me hotels in Barcelona under $200 per night"}'
```

## Datasets
- `datasets/flights.json` — 15 flight records
- `datasets/hotels.json` — 10 hotel records
