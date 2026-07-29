"""
Prompting for Structured Output
"""

import json
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# get your API key from an environment variable or secret management system
openai.api_key = os.getenv("OPENAI_API_KEY")

# System prompt answer
# Define the system prompt that instructs the model on its behavior
system_prompt = """
You are a helpful assistant that only answer with the following JSON schema:
{
    "answer": "the answer to the question"
}
"""

# Make a request to the Responses API
# The input is a list of messages, starting with the user's question
response = openai.responses.create(
    model="gpt-5",
    instructions=system_prompt,
    input=[
        {
            "role": "user",
            "content": "What is 15 + 27?"
        }
    ]
)
# Navigating the Response Structure
# Parse the output to extract the JSON answer
for item in response.output:
    # check if this item is a message
    if item.type == "message":
        # Handling JSON Parse Failure
        try:
            # Extract raw text from the content
            text = item.content[0].text
            # Parse the JSON string from the content
            result = json.loads(text)
            # Extract and print the answer field
            print(f"Answer: {result['answer']}")
        except json.JSONDecodeError:
            # Handle cases where the model didn't return valid JSON
            print("Failed to parse JSON from response")
        # Extract raw text from the content
        text = item.content[0].text
        # Parse the JSON string from the content
        result = json.loads(text)
        # Extract and print the answer field
        print(f"Answer: {result['answer']}")