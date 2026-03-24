#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import boto3
import json

# Simple test
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1000,
    "messages": [{"role": "user", "content": "Hello! Can you confirm you're Claude Opus 4.6 with 1M context?"}],
    "anthropic_beta": ["context-1m-2025-08-07"]  # This enables 1M context
}

try:
    response = bedrock.invoke_model(
        modelId="us.anthropic.claude-opus-4-6-20260205-v1:0",
        body=json.dumps(body)
    )
    
    result = json.loads(response["body"].read())
    print(result["content"][0]["text"])
    
except Exception as e:
    print(f"Error: {e}")