# Exercise: Short-Term Memory

## Overview
Build a custom `ShortTermMemoryHookProvider` that hooks into the Strands agent lifecycle to give WanderBot persistent short-term memory via AgentCore Memory. The agent will remember what the customer said in earlier invocations, enabling natural multi-turn travel planning conversations.

**Estimated time:** 20 minutes

## Learning Objectives
1. Implement the `HookProvider` interface by extending `HookProvider`
2. Use `register_hooks()` to bind callbacks to specific lifecycle events
3. Understand how `AgentInitializedEvent` and `MessageAddedEvent` power the memory pattern
4. Pass `hooks=[]` and `state={}` to the Strands `Agent` constructor

## Prerequisites
- Dataset in `datasets/` folder: `hotels.json`
- A memory resource created via the CLI or AgentCore console

## Setup
```bash
pip install -r requirements.txt
```



## Dataset
| File | Contents |
|------|----------|
| `datasets/hotels.json` | 10 hotels across 4 cities (Barcelona, Tokyo, Rome, Dubai) with ratings, prices, and amenities |

## Key Concept: The HookProvider Pattern

A `HookProvider` lets you hook into specific moments in the agent's lifecycle. You subclass it, implement `register_hooks()`, and bind callbacks to events:

| Event | When it fires | What we do |
|-------|--------------|------------|
| `AgentInitializedEvent` | Once, when the agent is set up | Retrieve last K turns from AgentCore Memory and inject into `system_prompt` |
| `MessageAddedEvent` | Every time a message is added | Persist the message to AgentCore Memory via `create_event()` |

Session identity is passed via `agent.state` and read inside the hooks as `event.agent.state.get("session_id")`.

## Exercise Steps

### Step 1:  Create Memory Resource
Before starting the exercise, create a memory resource using the AgentCore CLI:

```bash
agentcore memory create WanderBot
```

Copy the Memory ID from the output and set it as the `MEMORY_ID` value in `starter.py`.

**Note:** When deploying, AgentCore can auto-create a memory resource if configured in `.bedrock_agentcore.yaml`:
```yaml
memory:
  mode: STM_ONLY
  event_expiry_days: 30
```

The auto-created memory ID will be saved in your config file and can be used in your code.

You can also create the memory resource manually through the AgentCore console in the browser — go to the Memory section, click Create, set the name and expiry.

### Step 2: Import hook classes
Import `HookProvider`, `HookRegistry`, `AgentInitializedEvent`, and `MessageAddedEvent` from `strands.hooks`.

### Step 3: Implement `__init__`
Store `memory_client`, `memory_id`, and `last_k_turns` as instance attributes.

### Step 4: Implement `register_hooks()`
Register two callbacks:
- `AgentInitializedEvent` → `self.on_agent_initialized`
- `MessageAddedEvent` → `self.on_message_added`

The `on_agent_initialized` and `on_message_added` methods are already provided for you. They will work once Steps 1–3 are complete.

### Step 5: Wire up the entry point
Create the Agent with:
- `hooks=[ShortTermMemoryHookProvider(memory_client, MEMORY_ID)]`
- `state={"session_id": session_id, "actor_id": actor_id}`

## Local Testing (No Deployment)

Test your implementation locally without deploying to AWS:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run test script
python test_agent.py
```

The test script will simulate a multi-turn conversation to verify memory is working.

## Deployment to AWS

### Prerequisites

1. **Create ECR Repository** (one-time setup):
```bash
aws ecr create-repository --repository-name wanderbot_short_term_memory --region us-east-1
```

2. **Ensure `.bedrock_agentcore.yaml` exists** with correct configuration:
```yaml
default_agent: wanderbot_short_term_memory

agents:
  wanderbot_short_term_memory:
    name: wanderbot_short_term_memory  # Must be lowercase
    language: python
    entrypoint: starter.py
    deployment_type: container
    platform: linux/amd64  # CRITICAL: Must be amd64, NOT arm64

    aws:
      region: us-east-1
      account: YOUR_ACCOUNT_ID
      execution_role: null  # Auto-create recommended
      execution_role_auto_create: true
      ecr_repository: YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/wanderbot_short_term_memory
```

**IMPORTANT:** `platform: linux/amd64` is required. Using `linux/arm64` will cause 500 errors on AWS.

3. **Ensure `Dockerfile` exists** in the project root:
```dockerfile
FROM public.ecr.aws/docker/library/python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY starter.py .
COPY datasets/ ./datasets/
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "starter.py"]
```

### Deploy Commands

```bash
# 1. Refresh AWS credentials (if using AWS Academy)
aws-env

# 2. Deploy with local build (required for AWS Academy)
agentcore deploy --local-build --auto-update-on-conflict

# 3. Wait 2-3 minutes for deployment to complete

# 4. Check status
agentcore status

# 5. View logs if needed
aws logs tail /aws/bedrock-agentcore/runtimes/AGENT_ID-DEFAULT \
  --log-stream-name-prefix "$(date +%Y/%m/%d)/[runtime-logs]" \
  --since 30m
```

### Multi-turn test:
```bash
# Turn 1: Start planning
agentcore invoke '{"message": "I want to plan a trip to Barcelona on a budget", "actor_id": "alice"}'

# Turn 2: Agent should remember Barcelona and the budget preference
agentcore invoke '{"message": "What hotels are available under $150 per night?", "actor_id": "alice"}'

# Turn 3: Agent should remember the hotel results
agentcore invoke '{"message": "Which one has the best cancellation policy?", "actor_id": "alice"}'
```

## Expected Behaviour
- **Turn 1**: Agent acknowledges Barcelona and budget preference — no tool call needed
- **Turn 2**: Agent uses `search_hotels` with city=Barcelona and max_price_usd=150, returns Catalonia Plaza ($145) and Hostal Grau ($85)
- **Turn 3**: Agent remembers the hotel results from Turn 2 and compares cancellation policies without calling the tool again

## Hints
- `event.agent.state` is the dict you passed as `state={}` when creating the Agent — that's how `session_id` and `actor_id` reach your hooks
- The `on_agent_initialized` and `on_message_added` methods are already written — you just need to make them reachable by completing the class structure and registering the hooks
- `context.session_id` provides the session ID automatically from AgentCore — you don't need to pass it in the payload

## Common Errors

### Development Errors
| Error | Fix |
|-------|-----|
| Agent forgets earlier turns | Check that `register_hooks()` correctly binds both callbacks |
| `NameError: HookProvider` | Complete Step 1 — import the hook classes from `strands.hooks` |
| `MEMORY_ID` is empty | Set it to the value from `agentcore memory create` output |
| Agent doesn't use memory at all | Check that `hooks=[]` and `state={}` are passed to the Agent constructor in Step 4 |

### Deployment Errors
| Error | Fix |
|-------|-----|
| **500 error: "Received error from runtime"** | Most common cause: Platform mismatch. Change `platform: linux/arm64` to `platform: linux/amd64` in `.bedrock_agentcore.yaml` and redeploy |
| **"Agent is Deploying"** | Wait 2-3 minutes for container to start. Check `agentcore status` periodically |
| **"security token is invalid"** | AWS credentials expired. Run `aws-env` to reload fresh credentials |
| **"ECR repository not found"** | Create ECR repo: `aws ecr create-repository --repository-name wanderbot_short_term_memory --region us-east-1` |
| **CodeBuild restricted** | Use `--local-build` flag: `agentcore deploy --local-build` |

### Checking CloudWatch Logs
```bash
# Get agent ID from status output
agentcore status

# Tail logs (replace AGENT_ID with actual ID)
aws logs tail /aws/bedrock-agentcore/runtimes/AGENT_ID-DEFAULT \
  --log-stream-name-prefix "$(date +%Y/%m/%d)/[runtime-logs]" \
  --since 30m \
  --follow
```