import time
import json
import requests

# Set the base URL for the FastAPI server
BASE_URL = "http://localhost:8000"

# Send a POST request to launch the agent
response = requests.post(
    f"{BASE_URL}/agent/launch",
    json={"input_prompt": "Solve the root of this equation: x^2 - 5x + 6 = 0"}
)
# Parse the response JSON to get the initial state object
state = response.json()
# Print the unique state ID for reference
print(f"Launched agent with ID: {state['id']}")

# Start polling loop that continues until agent completes
while True:
    # Fetch the current state from the server
    response = requests.get(f"{BASE_URL}/agent/state/{state['id']}")
    # Parse the response to get the latest state object
    current_state = response.json()

    # Check if the agent has finished processing
    if current_state['status'] in ["complete", "max_steps_reached", "failed"]:
        print("Final State:")
        print(json.dumps(current_state, indent=2))

        # Exit the polling loop
        break
    
    # Wait 1 second before polling again to avoid overwhelming the server
    time.sleep(1)