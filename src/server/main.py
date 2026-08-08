import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict

from src.core.models.state import State
from src.core.agent import Agent
from src.server.database import get_db_session, StateModel, pydantic_to_db, db_to_pydantic

# Create agent
agent = Agent()

# In-memory storage
states: Dict[str, State] = {}

# Create a FastAPI app instance
app = FastAPI()

class LaunchRequest(BaseModel):
    input_prompt: str

def _create_progress_callback(state_id: str):
    """Create a progress callback function that saves state after each step"""
    def save_progress(state: State):
        with get_db_session() as session:
            # Look up the existing record to update it in place
            db_state = session.query(StateModel).filter(StateModel.id == state_id).first()
            if db_state:
                # Overwrite every field with the latest values from the agent
                db_state.steps = state.steps
                db_state.status = state.status
                db_state.context = state.context
                db_state.pending_tool_calls = state.pending_tool_calls
                db_state.error = state.error
                db_state.final_answer = state.final_answer
    return save_progress    

# Implementing Background Task Execution
def _run_agent_in_background(state_id: str):
    """Run the agent in a background thread (non-blocking)"""
    with get_db_session() as session:
        db_state = session.query(StateModel).filter(StateModel.id == state_id).first()
        if not db_state:
            return
        working_state = db_to_pydantic(db_state)

    # Create a progress callback by calling _create_progress_callback(state_id)
    save_progress = _create_progress_callback(state_id)
    # Run the agent with agent.run(working_state, progress_callback=save_progress)
    final_state = agent.run(working_state, progress_callback=save_progress)

    with get_db_session() as session:
        db_state = session.query(StateModel).filter(StateModel.id == state_id).first()
        if db_state:
            db_state.steps = final_state.steps
            db_state.status = final_state.status
            db_state.context = final_state.context
            db_state.pending_tool_calls = final_state.pending_tool_calls
            db_state.error = final_state.error
            db_state.final_answer = final_state.final_answer

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

    with get_db_session() as session:
        db_state = pydantic_to_db(initial_state)
        session.add(db_state)

    background_tasks.add_task(_run_agent_in_background, initial_state.id)

    return initial_state

# Creating the State Retrieval Endpoint
@app.get("/agent/state/{state_id}", response_model=State)
def get_state(state_id: str):
    """Get the current state by ID"""
    with get_db_session() as session:
        db_state = session.query(StateModel).filter(StateModel.id == state_id).first()
        if not db_state:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="State not found")
        return db_to_pydantic(db_state)