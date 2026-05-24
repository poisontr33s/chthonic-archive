#!/usr/bin/env python3
#-*- coding: utf-8 -*-



import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import os

import boto3

AWS_PROFILE = os.environ.get("AWS_PROFILE", "my-sso")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-opus-4-6-v1")

# WARNING: This can cost money. Keep it small until basic invocation works.
# This string is character-based, not token-based.
# Increase gradually only after you confirm model access and pricing expectations.
repeat = int(os.environ.get("LARGE_REPEAT", "20000"))
large_text = ("This is a test document. " * repeat).strip()

session = boto3.Session(profile_name=AWS_PROFILE)
brt = session.client("bedrock-runtime", region_name=AWS_REGION)

body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 200,
    "messages": [
        {
            "role": "user",
            "content": f"{large_text}\n\nSummarize the above in one sentence.",
        }
    ],
    "anthropic_beta": ["context-1m-2025-08-07"],
}

resp = brt.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
data = json.loads(resp["body"].read())
print("OK")
print(data["content"][0]["text"])
