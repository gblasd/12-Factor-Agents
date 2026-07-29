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
if not openai.api_key:
    raise EnvironmentError("OPENAI_API_KEY not found. Set it in environment or .env")

# Define two tool schemas: final_answer and perform_math
tool_schemas = [
    {
        "type": "function",
        "name": "final_answer",
        "description": "Provide the final answer and stop.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "description": "The final answer for the user."}
            },
            "required": ["answer"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "perform_math",
        "description": "Perform a mathematical calculation.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "description": "The mathematical operation to perform."},
                "a": {"type": "number", "description": "The first number."},
                "b": {"type": "number", "description": "The second number."}
            },
            "required": ["operation", "a", "b"],
            "additionalProperties": False
        }
    }
]

# System prompt that instructs the model on its behavior
system_prompt = "You are a helpful assistant."

def run_example():
    # Make a request to the Responses API
    # The input is a list of messages, starting with the user's question
    response = openai.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=[
            {
                "role": "user",
                "content": "Calculate 47 multiplied by 23 and give the final answer."
            }
        ],
        tools=tool_schemas,
        tool_choice="required",
        reasoning={"effort": "low"}
    )
    # Parse the output to extract the JSON answer
    for item in response.output:
        # Check if this item is a message
        if getattr(item, "type", None) == "function_call" and getattr(item, "name", None) == "final_answer":
            args = json.loads(item.arguments)
            print(f"Answer: {args['answer']}")

if __name__ == "__main__":
    run_example()
