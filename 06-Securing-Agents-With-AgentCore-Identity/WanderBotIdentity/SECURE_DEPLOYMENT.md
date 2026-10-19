# Secure Deployment Guide

This guide shows how to securely deploy the WanderBot agent without exposing sensitive endpoints in version control.

## Overview

The `GATEWAY_ENDPOINT` is stored in AWS Systems Manager Parameter Store and loaded by the Lambda function at runtime. This keeps sensitive values out of git while maintaining easy deployment.

## Setup Steps

### 1. Store the Gateway Endpoint in Parameter Store

Run this command once to store your gateway endpoint:

```bash
aws ssm put-parameter \
  --name "/wanderbot/gateway-endpoint" \
  --value "https://wanderbot-gateway-t2kkoaaf4m.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp" \
  --type "String" \
  --overwrite
```

**Note:** This parameter is stored in AWS and is NOT committed to git.

### 2. Deploy the Agent

```bash
cd agentcore
agentcore deploy
```

The CDK stack will automatically:
- Read the endpoint from Parameter Store during deployment
- Inject it as the `GATEWAY_ENDPOINT` environment variable in Lambda
- Grant the Lambda function permission to access the parameter

### 3. Local Development

For local development, keep the endpoint in `.env.local` (already gitignored):

```bash
# agentcore/.env.local
GATEWAY_ENDPOINT=https://wanderbot-gateway-t2kkoaaf4m.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
```

Then run:

```bash
agentcore dev
```

## Updating the Endpoint

If your gateway endpoint changes:

1. Update Parameter Store:
   ```bash
   aws ssm put-parameter \
     --name "/wanderbot/gateway-endpoint" \
     --value "NEW_ENDPOINT_URL" \
     --type "String" \
     --overwrite
   ```

2. Redeploy (CDK will pick up the new value):
   ```bash
   agentcore deploy
   ```

## Security Benefits

✅ No sensitive URLs in git history
✅ Parameter Store values are encrypted at rest
✅ Access controlled via IAM
✅ Easy to rotate without code changes
✅ Audit trail of parameter changes via CloudTrail

## What's Committed to Git

- `agentcore.json` - Configuration WITHOUT environment variables
- `cdk-stack.ts` - CDK code that reads from Parameter Store
- `.env.local` - **NOT committed** (in .gitignore)

## Troubleshooting

### Error: Parameter not found

If you see an error during deployment about the parameter not existing:

```bash
# Verify the parameter exists
aws ssm get-parameter --name "/wanderbot/gateway-endpoint"

# If not, create it with the command in Step 1
```

### Error: Access denied

If Lambda can't read the parameter:

The CDK stack should automatically grant read permissions. If you see this error, check that the Lambda execution role has `ssm:GetParameter` permission for `/wanderbot/gateway-endpoint`.
