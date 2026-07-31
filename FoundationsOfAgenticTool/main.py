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

# Define the functions we want to make available to the model
def add(a: float, b:float) -> float:
    """Add two numbers together."""
    return a + b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

# Define two tool schemas for the mode (including final_answer)
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
        "name": "add",
        "description": "Add two numbers together.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "The first number."},
                "b": {"type": "number", "description": "The second number."}
            },
            "required": ["a", "b"],
            "additionalProperties": False
        }
    },
    {
            "type": "function",
            "name": "multiply",
            "description": "Multiply two numbers together.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "The first number."},
                    "b": {"type": "number", "description": "The second number."}
                },
                "required": ["a", "b"],
                "additionalProperties": False
            }
        }
]

# System prompt that instructs the model on its behavior
system_prompt = """
You are a helpful assistant that can perform calculations.
When asked to do math, you must use the provided tools.
When your work is done, call the final_answer tool.
"""

def run_example():
    # Make a request to the Responses API
    # The input is a list of messages, starting with the user's question

    context = [
        {
            "role": "user",
            "content": "Compute 15 + 27"
        }
    ]

    response = openai.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=context,
        tools=tool_schemas,
        tool_choice="required",
        reasoning={"effort": "low"}
    )
    # Parse the output to extract the JSON answer
    for item in response.output:
        # Check if this item is a message
        if getattr(item, "type", None) == "function_call" : # and getattr(item, "name", None) == "final_answer":

            context.append({
                "type": "function_call",
                "name": item.name,
                "arguments": item.arguments,
                "call_id": item.call_id
            })

            args = json.loads(item.arguments)

            match item.name:
                case "add":
                    result = add(**args)
                case "multiply":
                    result = multiply(**args)
                case _:
                    result = f"Error: Tool {item.name} not implemented"

            print(f"Executed {item.name} ({args}) = {result}")

            context.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps({"result": result})
            })

    response = openai.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=context,
        tools=tool_schemas,
        tool_choice="required",
        reasoning={"effort": "low"}
    )

    for item in response.output:
        if item.type == "function_call" and item.name == "final_answer":
            args = json.loads(item.arguments)
            print(f"Final response: {args['answer']}")

if __name__ == "__main__":
    print("Start")
    run_example()
    print("End")