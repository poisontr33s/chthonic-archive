#!/usr/bin/env python3
#-*- coding: utf-8 -*-



import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import os

import boto3

# Config via env vars so you can switch profiles/regions without editing code.
AWS_PROFILE = os.environ.get("AWS_PROFILE", "my-sso")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-opus-4-6-v1")

session = boto3.Session(profile_name=AWS_PROFILE)
brt = session.client("bedrock-runtime", region_name=AWS_REGION)

body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 300,
    "messages": [
        {
            "role": "user",
            "content": "Reply with: (1) model name, (2) max context you support on this request.",
        }
    ],
    # Enables 1M context beta (required when you exceed 200K context).
    "anthropic_beta": ["context-1m-2025-08-07"],
}

resp = brt.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
data = json.loads(resp["body"].read())
print(data["content"][0]["text"])
