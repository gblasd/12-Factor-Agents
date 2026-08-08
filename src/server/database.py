from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Build an absolute path to the database file inside the data/ directory
db_path = Path(__file__).resolve().parent.parent / "data" / "agent_states.db"

# Create the directory if it doesn't already exist
db_path.parent.mkdir(parents=True, exist_ok=True)

# Connect to the SQLite database at the given path
engine = create_engine(f"sqlite:///{db_path}", echo=False)

# Base class that all SQLAlchemy models will inherit from
Base = declarative_base()

# Factory that creates new database sessions for each transaction
SessionLocal = sessionmaker(bind=engine)


from sqlalchemy import Column, String, Integer, Text, JSON

class StateModel(Base):
    __tablename__ = "states"  # Name of the table in the database
    
    id = Column(String, primary_key=True)           # Unique identifier for each state
    steps = Column(Integer, default=0)              # Number of steps completed so far
    status = Column(String, default="running")      # Current status of the agent
    context = Column(JSON, default=list)            # Full conversation history
    pending_tool_calls = Column(JSON, default=list) # Tool calls waiting to be executed
    error = Column(Text, nullable=True)             # Error message if the agent failed
    final_answer = Column(Text, nullable=True)      # Agent's final answer when complete

# Create all tables defined by models that inherit from Base
Base.metadata.create_all(engine)


from src.core.models.state import State

def pydantic_to_db(state: State) -> StateModel:
    """Convert Pydantic State to database model"""
    # Copy each field from the Pydantic model into a new SQLAlchemy model instance
    return StateModel(
        id=state.id,
        steps=state.steps,
        status=state.status,
        context=state.context,
        pending_tool_calls=state.pending_tool_calls,
        error=state.error,
        final_answer=state.final_answer,
    )


def db_to_pydantic(db_state: StateModel) -> State:
    """Convert database model to Pydantic State"""
    return State(
        id=db_state.id,
        steps=db_state.steps,
        status=db_state.status,
        context=db_state.context or [],            # Default to empty list if None
        pending_tool_calls=db_state.pending_tool_calls or [],  # Default to empty list if None
        error=db_state.error,
        final_answer=db_state.final_answer,
    )


from contextlib import contextmanager

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session          # Hand the session to the calling code
        session.commit()       # Save all changes if no exception was raised
    except Exception:
        session.rollback()     # Undo all changes if something went wrong
        raise
    finally:
        session.close()        # Always release the connection when done