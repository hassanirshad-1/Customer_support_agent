#Import necessary libraries
import requests
import os
from dotenv import load_dotenv
from agents import Agent, Runner, set_tracing_disabled, ModelSettings, function_tool, OpenAIChatCompletionsModel
from customer_support.shared import client, ollama_client
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

load_dotenv()
wc_base_url = os.getenv("WC_BASE_URL")
wc_consumer_key = os.getenv("WC_CONSUMER_KEY")
wc_consumer_secret = os.getenv("WC_CONSUMER_SECRET")
# Function to fetch order status from WooCommerce
@function_tool()
async def get_order_status(order_id : str) -> str:
    """Fetches the status of an order from WooCommerce.
    Args: order_id (str): The ID of the order to fetch the status for.
    Returns: str: The status of the order.e.g. "completed", "processing", "on-hold", etc."""
    try:
        url = f"{wc_base_url}/orders/{order_id}"
        response = requests.get(url, auth=(wc_consumer_key, wc_consumer_secret), timeout=10)
        if response.status_code == 200:
            order_data = response.json()
            status = order_data.get('status')
            return f"Order {order_id} status: {order_data['status']}" if status else "Status not available."
        elif response.status_code == 404:
            return f"Order {order_id} not found."
        elif response.status_code == 401:
            return "Authentication failed. Check your WooCommerce API keys."
        else:
            return f"Error fetching order {order_id}: {response.status_code} - {response.text}"
    except requests.exceptions.Timeout as e:
        return f"Request timed out while fetching order {order_id}. Please try again later."
    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching order {order_id}: {str(e)}"

SYSTEM_PROMPT_ORDER_AGENT = """

# ROLE:
You’re a Muslim Digital Link support agent. Help customers efficiently while following all rules.

# Instructions:
- Use tools for any order-related queries (e.g. order status). Never guess — only respond using tool output.
- Avoid topics like politics, religion, legal/medical advice, internal matters, or personal opinions.
- Be professional, and polite and little Muslim touch — add emojis between sentences.



# PHRASES:
## For prohibited/irrelevent topics:
- "I'm sorry, I can't discuss that. Can I help with something else?"
- "That’s outside my scope — happy to help with anything else."

 

"""

#define the order agent
order_agent = Agent(
    name="Order Agent",
    instructions=SYSTEM_PROMPT_ORDER_AGENT,
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    tools=[get_order_status],
    model_settings=ModelSettings(
        temperature=0.6,
        top_p=0.9,
        tool_choice="required",
        max_tokens=1000),
    handoff_description="Handles all order related queries."
    
)
set_tracing_disabled(False)


        

