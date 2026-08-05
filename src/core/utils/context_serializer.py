import json
from typing import List, Dict, Any
from pathlib import Path

# Load the context format template from the markdown file
_template_path = Path(__file__).resolve().parent.parent / "prompts" / "context_format.md"
_CONTEXT_TEMPLATE = _template_path.read_text(encoding="utf-8")

def serialize_context_to_text(context: List[Dict[str, Any]]) -> str:
    """
    Transform the raw context list into structured markdown text.
    Returns a formatted string ready to send to the model.
    """
    if not context:
        return ""

    # Extracting the User Message
    user_message = ""
    for item in context:
        if item.get("role") == "user":
            user_message = item.get("content", "")
            break

    # Build a mapping of function call IDs to their formatted signatures
    call_map = {}
    for item in context:
        if item.get("type") == "function_call":
            call_id = item.get("call_id")
            call_name = item.get("name")
            call_args = item.get("arguments", "{}")

            # Parse arguments if they're a JSON string
            if isinstance(call_args, str):
                try:
                    call_args = json.loads(call_args)
                except:
                    pass

            # Format arguments as readable key=value pairs
            if isinstance(call_args, dict):
                args_str = ", ".join(f"{k}={repr(v)}" for k, v in call_args.items())
            else:
                args_str = str(call_args)

            # Store the formatted call signature
            call_map[call_id] = f"{call_name}({args_str})"

    # Formatting Completed Actions
    lines = []
    for item in context:
        if item.get("type") == "function_call_output":
            call_id = item.get("call_id")
            output = item.get("output", "{}")
            
            # Look up the formatted function call
            call_formatted = call_map.get(call_id, f"unknown_call({call_id})")
            
            # Create a readable line showing what was completed
            lines.append(f"✓ COMPLETED: {call_formatted} → Result: {output}")

    # Combine into execution history string
    execution_history = "\n".join(lines) if lines else "(No actions completed yet)"

    return _CONTEXT_TEMPLATE.format(
        user_message=user_message,
        execution_history=execution_history
    )