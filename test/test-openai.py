#!/usr/bin/env python3
import os
import sys
sys.path.append('/Users/morlock/Morlock/scan/document-processor/backend')

from openai import OpenAI

# Test OpenAI connection
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)

print(f"Testing OpenAI API with key: {api_key[:10]}...")

try:
    client = OpenAI(api_key=api_key)
    
    # Simple test
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Say 'Hello, API is working!'"}
        ],
        max_tokens=50
    )
    
    print(f"Success! Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    sys.exit(1)