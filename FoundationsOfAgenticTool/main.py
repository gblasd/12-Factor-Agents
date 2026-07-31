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
            "content": "Compute ((((2 * 3) + 4) * 5) + 6) * 7"
        }
    ]

    # Set up loop control variables
    max_steps = 5
    step = 0
    done = False
    final_answer = None

    # Main agent loop: continue until done or max steps reached
    while not done and step < max_steps:
        step += 1
        print(f"\n--- Step {step} ---")

        # Call the LLM with current context
        response = openai.responses.create(
            model="gpt-5",
            instructions=system_prompt,
            input=context,
            tools=tool_schemas,
            tool_choice="required",
            reasoning={"effort": "low"}
        )

        # Process watch item in the response
        # Parse the output to extract the JSON answer
        for item in response.output:
            # Check if this item is a message
            if getattr(item, "type", None) == "function_call" :
                function_name = item.name
                # Parse the arguments from JSON string to Python dict, parse errors in context of the function call
                try:
                    args = json.loads(item.arguments)
                except json.JSONDecodeError as e:
                    print(f"Error parsing arguments for function {function_name}: {e}")
                    continue

                print(f"Calling function: {function_name} ({args})")

                # Add function call to context
                context.append({
                    "type": "function_call",
                    "name": item.name,
                    "arguments": item.arguments,
                    "call_id": item.call_id
                })

                # Execute tools and capture result for printing
                try:
                    match function_name:
                        case "final_answer":
                            result = args.get("answer")
                            final_answer = result
                            output = json.dumps({"status": "reported"})
                            done = True
                        case "add":
                            result = add(**args)
                            output = json.dumps({"result": result})
                        case "multiply":
                            result = multiply(**args)
                            output = json.dumps({"result": result})
                        case _:
                            result = f"Tool {function_name} not found"
                            output = json.dumps({"error": result})
                except Exception as e:
                    result = f"Error: {e}"
                    output = json.dumps({"error": result})

                print(f"Result {result}")

                # Add function output to context
                context.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": output
                })

                # Exit processing if final answer reached
                if done:
                    break

    if step >= max_steps:
        print(f"\nReached maximum steps ({max_steps})")

    print(f"\nCompleted in {step} steps")
    if final_answer:
        print(f"Final answer: {final_answer}")

if __name__ == "__main__":
    print("Start")
    run_example()
    print("End")