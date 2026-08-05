import json
import os
import openai
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# get your API key from an environment variable or secret management system
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise EnvironmentError("OPENAI_API_KEY not found. Set it in environment or .env")

# import tool functions from core/tools/functions/math.py
from core.tools.functions.math import (
    sum_numbers,
    multiply_numbers,
    subtract_numbers,
    divide_numbers
)

from core.utils.context_serializer import serialize_context_to_text

class Agent:
    def __init__(
        self,
        model: str = "gpt-5",
        reasoning_effort: str = "low",
        extra_instructions: Optional[str] = None,
        max_steps: int = 10
    ):
        # Store model configuration
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_steps = max_steps

        # Define the base system prompt
        # Load system prompt from file. (Factor 2)
        prompt_path = Path(__file__).resolve().parent / "prompts" / "base_system.md"
        self.system_prompt = prompt_path.read_text(encoding="utf-8") + extra_instructions if extra_instructions else ""

        # Load tool schemas from JSON files
        # Using Path makes this portable across different environments
        schemas_dir = Path(__file__).resolve().parent / "tools" / "schemas"

        with open(schemas_dir / "math.json", "r", encoding="utf-8") as f:
            math_schemas = json.load(f)

        with open(schemas_dir / "final_answer.json", "r", encoding="utf-8") as f:
            final_answer_schema = json.load(f)

        # Combine all schemas into a single list for the agent to use
        self.tool_schemas = [
            *math_schemas,
            final_answer_schema
        ]

    def _call_llm(self, context: List[Any]):
        """
        Call the LLM with the current context.
        Returns the model's response, which will include tool calls.
        """
        # Serialize context to control what the model sees (Factor 3)
        serialized_content = serialize_context_to_text(context)

        response = openai.responses.create(
            model=self.model,
            instructions=self.system_prompt,
            input=serialized_content,  # The full conversation history: clean, formatted text
            tools=self.tool_schemas,  # Available tools
            tool_choice="required",  # Force the model to use a tool
            reasoning={"effort": self.reasoning_effort} if self.model == "gpt-5" else None
        )
        return response

    def _next_step(self, context: List[Any]):
        """
        Execute one step of the agent loop:
        1. Call the LLM
        2. Extract function calls
        3. Execute tools
        4. Update context
        Returns: (updated_context, status, final_answer)
        """
        # Get the model's response
        response = self._call_llm(context)
        
        # Extract all function calls from the response
        function_calls = [item for item in response.output if item.type == "function_call"]

        # Process each function call
        for fc in function_calls:
            call_name = fc.name
            call_arguments = json.loads(fc.arguments)

            # Record the function call in context
            context.append({
                "type": "function_call",
                "name": call_name,
                "arguments": fc.arguments,
                "call_id": fc.call_id
            })

            # Check if this is the final answer
            if call_name == "final_answer":
                # Stop the loop and return the answer
                return context, "complete", call_arguments.get("answer")

                        # Execute the tool based on its name
            match call_name:
                case "sum_numbers":
                    try:
                        result = sum_numbers(**call_arguments)
                        output = json.dumps({"result": result})
                    except Exception as e:
                        output = json.dumps({"result": f"Error: {str(e)}"})
                
                # Similar cases for multiply_numbers, subtract_numbers, divide_numbers, power, and square_root...
                case "multiply_numbers":
                    try:
                        result = multiply_numbers(**call_arguments)
                        output = json.dumps({"result": result})
                    except Exception as e:
                        output = json.dumps({"result": f"Error: {str(e)}"})

                case "subtract_numbers":
                    try:
                        result = subtract_numbers(**call_arguments)
                        output = json.dumps({"result": result})
                    except Exception as e:
                        output = json.dumps({"result": f"Error: {str(e)}"})

                case "divide_numbers":
                    try:
                        result = divide_numbers(**call_arguments)
                        output = json.dumps({"result": result})
                    except Exception as e:
                        output = json.dumps({"result": f"Error: {str(e)}"}) 
                        
                case _:
                    # Unknown tool name
                    output = json.dumps({"result": f"Error: Tool {call_name} not found"})

            # Record the tool output in context, linked to the original call
            context.append({
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": output
            })

        # All tools executed, continue the loop
        return context, "running", None

    def run(self, context: List[Any]):
        """
        Run the agent loop until completion or max_steps.
        Returns: (final_context, status, final_answer)
        """
        step = 0
        status = "running"
        final_answer = None

        # Keep running until we complete or hit the step limit
        while status == "running" and step < self.max_steps:
            step += 1
            # Each step returns updated context, status, and potentially an answer
            context, status, final_answer = self._next_step(context)

        # If we hit the step limit without completing, update status
        if status == "running":
            status = "max_steps_reached"

        # Return the final state
        return context, status, final_answer