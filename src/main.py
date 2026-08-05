import uuid
from core.agent import Agent
from core.models.state import State

# Create an agent using default settings
agent = Agent()

# Create initial state with unique ID and user request
initial_state = State(
    id=str(uuid.uuid4()),
    context=[
        {
            "role": "user",
            "content": "Solve the root of this equation: x^2 - 5x + 6 = 0"
        }
    ],
    status="running"
)

# Run agent and receive a new state object (original is not mutated)
final_state = agent.run(initial_state)

print(f"Status: {final_state.status}")
if final_state.status == "failed":
    print(f"Error: {final_state.error}")
elif final_state.final_answer:
    print(f"Final answer: {final_state.final_answer}")