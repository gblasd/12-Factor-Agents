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
from src.core.models import state
from src.core.tools.functions.math import (
    sum_numbers,
    multiply_numbers,
    subtract_numbers,
    divide_numbers
)

from src.core.utils.context_serializer import serialize_context_to_text
from src.core.models.state import State

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

    def _next_step(self, state: State):

        # State carries both executiona and business data (Factor 5)
        state.steps += 1

        # Processed all queued tool calls
        for function_call in state.pending_tool_calls:
            call_name  = function_call["name"]
            call_args  = function_call["arguments"]
            call_id    = function_call["call_id"]

            # Persist the tool call in the same state object
            state.context.append({
                "type": "function_call",
                "name": call_name,
                "arguments": json.dumps(call_args),
                "call_id": call_id
            })

            # Execute the tool based on its name
            match call_name:
                case "final_answer":
                    # Agent is done - transition to complete status
                    state.pending_tool_calls = []
                    state.status = "complete"
                    state.final_answer = call_args.get("answer")
                    return state
                    
                case "sum_numbers":
                    # Execute tool with error handling
                    try:
                        result = sum_numbers(**call_args)
                        output = json.dumps({"result": result})
                    except Exception as e:
                        output = json.dumps({"result": f"Error: {str(e)}"})

                case "multiply_numbers":
                    try:
                        result = multiply_numbers(**call_args)
                        output = json.dumps({"result": result})
                    except Exception as e:
                        output = json.dumps({"result": f"Error: {str(e)}"})
                case "subtract_numbers":
                    try:
                        result = subtract_numbers(**call_args)
                        output = json.dumps({"result": result})
                    except Exception as e:
                        output = json.dumps({"result": f"Error: {str(e)}"})
                case "divide_numbers":
                    try:
                        result = divide_numbers(**call_args)
                        output = json.dumps({"result": result})
                    except Exception as e:
                        output = json.dumps({"result": f"Error: {str(e)}"})
                case _:
                    # Unknown tool name
                    output = json.dumps({"result": f"Error: Tool {call_name} not found"})

            # Remove processed call and store output
            state.pending_tool_calls.remove(function_call)
            # Store tool output in the same state object
            state.context.append({
                "type": "function_call_output",
                "call_id": call_id,
                "output": output
            })

        # Call LLM with updated context including tool results
        response = self._call_llm(state.context)
        
        # Extract all function calls from the response
        function_calls = [item for item in response.output if item.type == "function_call"]

        # Convert to dictionaries for easier manipulation
        function_call_dicts = [
            {
                "name": fc.name,
                "arguments": json.loads(fc.arguments),
                "call_id": fc.call_id,
                "type": fc.type
            }
            for fc in function_calls
        ]

        # Queue new tool calls for the next step
        state.pending_tool_calls.extend(function_call_dicts)
        return state

    def run(self, state: State, progress_callback=None):
        """Execute agent steps on a given state and persist progress"""
        # Create a deep copy to avoid mutating the original
        state = state.model_copy(deep=True)

        # Initialize execution status and clear stale errors
        state.status = "running"
        state.error = None

        # Check if the agent is resuming 
        is_resuming = state.steps > 0
        max_steps_allowed = (self.max_steps + state.steps) if is_resuming else self.max_steps

        try:
            # Process steps until completion or max_steps reached
            while state.status == "running" and state.steps < self.max_steps:
                state = self._next_step(state)

                if progress_callback:
                    progress_callback(state)

            if state.status == "running" and state.steps >= max_steps_allowed:
                state.status = "max_steps_reached"

            return state
                
        except Exception as e:
            # Capture fatal errors in the state object
            state.status = "failed"
            state.error = str(e)
        
            state.pending_tool_calls = []
            if progress_callback:
                progress_callback(state) # Save the failed state as well

            return state