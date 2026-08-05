from core.agent import Agent

# Create an agent using default settings
agent = Agent()

# Start with a user question in the context
context = [
    {
        "role": "user",
        "content": "Solve the root of this equation: x^2 - 5x + 6 = 0"
    }
]

# Run the agent until it completes or hits max_steps
context, status, final_answer = agent.run(context)

# Display the results
print(f"Status: {status}")
print(f"Final answer: {final_answer}")

# Display the raw final context for auditing
print("\nFinal context:")
for item in context:
    print(item)