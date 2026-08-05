import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict

from src.core.models.state import State
from src.core.agent import Agent

# Create agent
agent = Agent()

# In-memory storage
states: Dict[str, State] = {}

# Create a FastAPI app instance
app = FastAPI()

class LaunchRequest(BaseModel):
    input_prompt: str

# Implementing Background Task Execution
def _run_agent_in_background(state_id: str):
    """Run the agent in a background thread (non-blocking)"""
    state = states[state_id]
    state = agent.run(state)
    states[state_id] = state

# Building the Launch Endpoint Structure
@app.post("/agent/launch", response_model=State)
def agent_launch(payload: LaunchRequest, background_tasks: BackgroundTasks):
    """Launch a new agent workflow"""
    initial_state = State(
        id=str(uuid.uuid4()),
        context=[
            {
                "role": "user",
                "content": payload.input_prompt
            }
        ],
        status="running"
    )

    states[initial_state.id] = initial_state
    background_tasks.add_task(
        _run_agent_in_background,
        initial_state.id
    )

    return initial_state

# Creating the State Retrieval Endpoint
@app.get("/agent/state/{state_id}", response_model=State)
def get_state(state_id: str):
    # Return a 404 error if the state id doesn't exist
    if state_id not in states:
        raise HTTPException(status_code=404, detail="State not found")
    
    # Return the current state for this id
    return states[state_id]