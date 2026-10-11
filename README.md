# Bedrock AgentCore and Strands SDK - Complete Setup Guide

This guide covers everything you need to build, test, and deploy AI agents using Amazon Bedrock AgentCore and Strands SDK.

**✅ Verified Working Configuration** - Successfully tested with AWS Academy accounts using local build deployment with auto-created IAM roles.

## Quick Start (5 Minutes to Deployment)

```bash
# 1. Setup (one time)
python -m venv .venv && source .venv/bin/activate
pip install strands-agents strands-agents-tools bedrock-agentcore
source ../load-aws-env.sh

# 2. Create ECR repository
aws ecr create-repository --repository-name wanderbot --region us-east-1

# 3. Configure YAML (.bedrock_agentcore.yaml)
#    execution_role: null
#    execution_role_auto_create: true
#    ecr_repository: <URI from step 2>

# 4. Deploy!
agentcore deploy --local-build --auto-update-on-conflict

# 5. Test
agentcore invoke '{"prompt": "Hello!"}'
```

**Key Success Factors:**
- ✅ Use `--local-build` (CodeBuild restricted in AWS Academy)
- ✅ Enable `execution_role_auto_create: true` (creates correct trust policy)
- ✅ Agent name must be lowercase (Docker requirement)
- ✅ Model ID: `us.amazon.nova-lite-v1:0` (inference profile format)

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Credentials Setup](#aws-credentials-setup)
3. [Project Structure](#project-structure)
4. [YAML Configuration Requirements](#yaml-configuration-requirements)
5. [Dockerfile Requirements](#dockerfile-requirements)
6. [Local Testing](#local-testing)
7. [Deployment to AWS](#deployment-to-aws)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.14+** - Agent runtime
- **Docker Desktop** - For local builds and containerization
- **uv** - Fast Python package manager
- **Node.js & npm** (optional) - For new AgentCore CLI

### Required Python Packages
```bash
pip install \
  strands-agents \
  strands-agents-tools \
  bedrock-agentcore \
  bedrock-agentcore-starter-toolkit
```

### Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## AWS Credentials Setup

See [CREDENTIALS-SETUP.md](./CREDENTIALS-SETUP.md) for detailed AWS credentials configuration.

### Quick Setup
1. Edit `.env` file with your AWS credentials:
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_SESSION_TOKEN="your-token"  # For AWS Academy
export AWS_DEFAULT_REGION="us-east-1"
```

2. Load credentials:
```bash
source load-aws-env.sh
# or use the alias:
aws-env
```

---

## Project Structure

```
YourAgent/
├── .bedrock_agentcore.yaml    # AgentCore configuration
├── Dockerfile                 # Container definition
├── requirements.txt           # Python dependencies
├── starter.py                 # Main agent code
├── .gitignore                 # Git ignore rules
└── .venv/                     # Virtual environment
```

---

## YAML Configuration Requirements

### Minimal `.bedrock_agentcore.yaml`

```yaml
default_agent: your-agent-name

agents:
  your-agent-name:
    name: your-agent-name  # MUST be lowercase for Docker
    language: python
    entrypoint: starter.py
    deployment_type: container
    platform: linux/amd64

    aws:
      region: us-east-1
      account: null  # Auto-filled from credentials
      execution_role: arn:aws:iam::ACCOUNT_ID:role/YourExecutionRole
      ecr_repository: ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/your-repo

    environment:
      AWS_REGION: us-east-1
```

### Key Requirements
1. **Agent name MUST be lowercase** - Docker tags don't accept uppercase
2. **execution_role** - IAM role ARN for agent execution
3. **ecr_repository** - Full ECR repository URI for container storage
4. **platform: linux/amd64** - Required for AWS deployment (even on ARM Macs)

---

## Dockerfile Requirements

### Standard Python Agent Dockerfile

```dockerfile
# Use official Python base image
FROM public.ecr.aws/docker/library/python:3.14-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY starter.py .

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run the agent
CMD ["python", "-m", "uvicorn", "starter:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Dockerfile Best Practices
- Use slim base images to reduce size
- Install dependencies before copying code (better layer caching)
- Set `PYTHONUNBUFFERED=1` for real-time logs
- Use `--no-cache-dir` with pip to reduce image size

---

## Local Testing

### 1. Test with Python directly
```bash
cd YourAgent
source .venv/bin/activate
python starter.py
```

### 2. Test with AgentCore Dev Server
```bash
# Terminal 1: Start dev server
agentcore dev

# Terminal 2: Test the agent
agentcore invoke --dev "Your test message here"
```

The dev server:
- ✅ Builds container locally
- ✅ Mocks AWS runtime
- ✅ No AWS credentials needed
- ✅ No AWS costs
- ✅ Hot reloads on file changes

---

## Deployment to AWS

### Prerequisites

#### 1. Create ECR Repository (Required)
**This must be done before deployment:**
```bash
aws ecr create-repository \
  --repository-name your-agent-name \
  --region us-east-1
```

Note the `repositoryUri` from the output - add this to your YAML config.

#### 2. IAM Execution Role - Use Auto-Create (RECOMMENDED)

**The easiest and most reliable method is to let AgentCore auto-create the role.**

In your `.bedrock_agentcore.yaml`:
```yaml
aws:
  execution_role: null  # Set to null
  execution_role_auto_create: true  # Enable auto-create
  ecr_repository: YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/your-repo
```

The auto-created role will have the **correct trust policy** with:
- ✅ Service principal: `bedrock-agentcore.amazonaws.com`
- ✅ Proper conditions for AgentCore Runtime
- ✅ Required permissions

**Manual Role Creation (Only if auto-create fails):**

If you must create the role manually, use this **exact trust policy**:

```bash
cat > /tmp/agentcore-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "bedrock-agentcore.amazonaws.com"
    },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "aws:SourceAccount": "YOUR_ACCOUNT_ID"
      },
      "ArnLike": {
        "aws:SourceArn": "arn:aws:bedrock-agentcore:us-east-1:YOUR_ACCOUNT_ID:*"
      }
    }
  }]
}
EOF

aws iam create-role \
  --role-name YourAgentRuntimeRole \
  --assume-role-policy-document file:///tmp/agentcore-trust-policy.json

aws iam attach-role-policy \
  --role-name YourAgentRuntimeRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

aws iam attach-role-policy \
  --role-name YourAgentRuntimeRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

aws iam attach-role-policy \
  --role-name YourAgentRuntimeRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

**CRITICAL:** The service principal MUST be exactly `bedrock-agentcore.amazonaws.com`.
- ❌ NOT `bedrock.amazonaws.com`
- ❌ NOT `bedrock-runtime.amazonaws.com`
- ❌ NOT account root principal

### Deployment Methods

#### Method 1: Local Build + Deploy (Recommended)
```bash
# 1. Activate environment and load credentials
source .venv/bin/activate
aws-env

# 2. Deploy (builds locally, deploys to AWS)
agentcore deploy --local-build --auto-update-on-conflict
```

**This method:**
- ✅ Builds Docker container on your Mac
- ✅ Pushes to your ECR repository
- ✅ Deploys to AgentCore Runtime
- ✅ Works with AWS Academy
- ✅ Auto-creates IAM role with correct trust policy

**Use when:**
- Working with AWS Academy (CodeBuild is restricted)
- You have Docker Desktop installed
- You want full control over the build process

#### Method 2: CodeBuild (Cloud Build)

**⚠️ Note:** CodeBuild may be restricted in AWS Academy accounts.

```bash
source .venv/bin/activate
aws-env
agentcore deploy --auto-update-on-conflict
```

**Use when:**
- Full AWS account (not AWS Academy)
- Building for production
- Don't want to use local Docker

### Deployment Process
1. **Build** - Create Docker container locally
2. **Push** - Upload image to ECR repository
3. **Role Setup** - Auto-create or use existing IAM role
4. **Deploy** - Create/update AgentCore Runtime
5. **Ready** - Agent endpoint active and available

### Post-Deployment - Testing Your Agent

#### Check Deployment Status
```bash
agentcore status
```

#### Invoke Your Agent
```bash
# Simple test
agentcore invoke '{"prompt": "Hello!"}'

# Test with agent functionality
agentcore invoke '{"prompt": "I have 3 bags in economy. What will extra baggage cost?"}'

# Test calculator tool usage
agentcore invoke '{"prompt": "What is 50 times 2?"}'
```

#### View Logs
```bash
# Tail live logs
aws logs tail /aws/bedrock-agentcore/runtimes/YOUR-AGENT-ID-DEFAULT \
  --log-stream-name-prefix "2026/10/10/[runtime-logs]" \
  --follow

# View recent logs
aws logs tail /aws/bedrock-agentcore/runtimes/YOUR-AGENT-ID-DEFAULT \
  --log-stream-name-prefix "2026/10/10/[runtime-logs]" \
  --since 1h
```

#### Get Agent Details
```bash
# List all agents
aws bedrock-agent list-agents --region us-east-1

# Get specific agent info
aws bedrock-agent get-agent --agent-id YOUR-AGENT-ID --region us-east-1
```

---

## Troubleshooting

### Common Issues

#### 1. "repository name must be lowercase"
**Problem:** Agent name in YAML has uppercase letters
**Solution:** Change `name:` field to all lowercase

```yaml
agents:
  myagent:
    name: myagent  # NOT MyAgent
```

#### 2. "Missing 'aws.execution_role'" or "Role validation failed"
**Problem:** No IAM role configured or wrong trust policy
**Solution:** Use auto-create (RECOMMENDED):

```yaml
# In .bedrock_agentcore.yaml
aws:
  execution_role: null
  execution_role_auto_create: true
```

Then deploy. The toolkit will create a role with the correct trust policy.

**If auto-create fails:** Create role manually with service principal `bedrock-agentcore.amazonaws.com` (see Deployment Prerequisites)

#### 3. "ECR repository not configured"
**Problem:** No ECR repository created
**Solution:** Create ECR repo and add to YAML config

#### 4. "CodeBuild failed: STOPPED during PROVISIONING"
**Problem:** AWS Academy restricts CodeBuild
**Solution:** Use `--local-build` flag instead

#### 5. "Dockerfile not found"
**Problem:** Missing Dockerfile for local builds
**Solution:** Create Dockerfile (see Dockerfile Requirements)

#### 6. Session Token Expired
**Problem:** AWS credentials expired (AWS Academy)
**Solution:** Get fresh credentials, update `.env`, run `aws-env`

#### 7. Docker not running
**Problem:** Docker daemon not started
**Solution:** Start Docker Desktop

### Checking Logs

#### CodeBuild Logs
```bash
# List recent builds
aws codebuild list-builds-for-project \
  --project-name bedrock-agentcore-your-agent-builder

# Get build details
aws codebuild batch-get-builds --ids BUILD_ID
```

#### CloudWatch Logs
```bash
# Tail build logs
aws logs tail /aws/codebuild/bedrock-agentcore-your-agent-builder \
  --since 10m --follow

# Tail agent runtime logs
aws logs tail /aws/bedrock/agentcore/your-agent \
  --since 10m --follow
```

---

## Complete Workflow Example

### First Time Setup
```bash
# 1. Navigate to exercise folder
cd WanderBot

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Load AWS credentials
source ../load-aws-env.sh

# 5. Create ECR repository (one time only)
aws ecr create-repository --repository-name wanderbot --region us-east-1

# 6. Update .bedrock_agentcore.yaml:
#    - Set agent name (lowercase!)
#    - Set ecr_repository URI (from step 5 output)
#    - Set execution_role: null
#    - Set execution_role_auto_create: true
```

### Development Cycle
```bash
# 1. Activate environment and load credentials
source .venv/bin/activate
aws-env

# 2. Test locally
python starter.py

# 3. Test in container
agentcore dev
# In another terminal:
agentcore invoke --dev "test message"

# 4. Deploy to AWS
agentcore deploy --local-build --auto-update-on-conflict

# 5. Test deployed agent
agentcore invoke "test message"
```

### When Credentials Expire
```bash
# 1. Get new credentials from AWS Academy
# 2. Update .env file in parent directory
# 3. Reload credentials
aws-env
# 4. Continue working
```

---

## Important Notes

### AWS Academy Specific Considerations

**Works with AWS Academy:**
- ✅ Local build deployment (`--local-build`)
- ✅ Auto-created IAM roles (`execution_role_auto_create: true`)
- ✅ ECR repositories
- ✅ AgentCore Runtime deployment
- ✅ Bedrock model access (Nova Lite)

**Restricted in AWS Academy:**
- ❌ CodeBuild (use `--local-build` instead)
- ❌ Updating IAM trust policies (use auto-create or create new roles)
- ❌ Some IAM administrative actions

**Best Practice for AWS Academy:**
Always use:
```bash
agentcore deploy --local-build --auto-update-on-conflict
```

With YAML config:
```yaml
execution_role: null
execution_role_auto_create: true
```

### AWS Resources (Created Once)
These persist across sessions:
- ✅ IAM Execution Role
- ✅ ECR Repository
- ✅ S3 Buckets (auto-created)
- ✅ CodeBuild Projects (auto-created)

**Reusable for future exercises in the same AWS account!**

### AWS Resources (Session-Based)
These expire and need refresh:
- ❌ AWS Access Key
- ❌ AWS Secret Key
- ❌ AWS Session Token (AWS Academy)

**Update in `.env` when expired**

### Docker Image Tags
- Must be **lowercase only**
- Format: `bedrock_agentcore-{agent-name}:{timestamp}`
- Each deployment creates a new immutable tag

### Model IDs
For Amazon Nova models, use **inference profiles**:
```python
MODEL_ID = "us.amazon.nova-lite-v1:0"  # Correct
# NOT: "amazon.nova-lite-v1:0"
```

---

## Additional Resources

- [Strands SDK Documentation](https://strandsagents.com/docs)
- [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/)
- [Docker Documentation](https://docs.docker.com/)
- [AWS IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
- [Amazon ECR](https://docs.aws.amazon.com/ecr/)

---

## Quick Reference Commands

```bash
# AWS Credentials
aws-env                                  # Load credentials
echo $AWS_ACCESS_KEY_ID                  # Verify loaded

# Local Testing
python starter.py                        # Direct Python
agentcore dev                            # Container dev server
agentcore invoke --dev "message"         # Test dev server

# Deployment
agentcore deploy --local-build --auto-update-on-conflict  # Local build
agentcore deploy --auto-update-on-conflict                # CodeBuild

# Debugging
docker ps                                # Check running containers
docker images                            # List Docker images
aws ecr describe-repositories            # List ECR repos
aws iam list-roles | grep Agent          # Find IAM roles
aws logs tail /aws/codebuild/...         # View build logs
```

---

## License & Support

For course-related questions, consult your Udacity instructor.
For AgentCore issues, see the [AWS Support](https://aws.amazon.com/support/).

---

*Last Updated: 2026-10-11*
