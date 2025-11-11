import asyncio
import os
from dotenv import load_dotenv

# Import agent definitions
from customer_support.triage_agent import triage_agent
from agents import Runner, RunContextWrapper, set_tracing_disabled
load_dotenv()
set_tracing_disabled(False)
openai_api_key = os.getenv("OPENAI_API_KEY")
async def route_query(user_input: str, run_context: RunContextWrapper):
    """
    Run the triage agent — it will automatically hand off to specialists
    using the SDK's built-in handoff mechanism.
    """
    result = await Runner.run(triage_agent, user_input, context=run_context)

    # SDK automatically handles:
    # - Deciding which agent to call
    # - Transferring conversation context
    # - Returning the final specialist response

    if getattr(result, "handoff", None):
        print(f"🤝 Handoff occurred: {result.handoff.source_agent.name} → {result.handoff.target_agent.name}")

    # The final_output always contains the specialist’s response
    final_response = result.final_output.strip() if result.final_output else "[No response]"
    return final_response



async def main_loop():
    # Initialize shared context (persisted across turns)
    run_context = RunContextWrapper(context={})

    print("Digital Link Customer Support (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye 👋")
            break

        try:
            response = await route_query(user_input, run_context)
            print("Agent:", response)
        except Exception as e:
            print("⚠️ Error:", e)


if __name__ == "__main__":
    asyncio.run(main_loop())
