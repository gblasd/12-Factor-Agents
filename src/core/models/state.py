from typing import List, Any, Optional
from pydantic import BaseModel, Field


class State(BaseModel):
    # Unique identifier for tracking and persistence
    id: str
    
    # Execution state: processing step count
    steps: int = 0
    status: str = "running"
    
    # Business state: conversation history
    # Using default_factory ensures each instance gets its own list
    context: List[Any] = Field(default_factory=list)
    
    # Execution state: tool calls queued for the next step
    pending_tool_calls: List[Any] = Field(default_factory=list)
    
    # Optional fields populated during execution
    error: Optional[str] = None
    final_answer: Optional[str] = None