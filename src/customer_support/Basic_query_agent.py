#Import necessary libraries
import requests
import os
from dotenv import load_dotenv
from agents import Agent, Runner, set_tracing_disabled, ModelSettings, function_tool, OpenAIChatCompletionsModel, set_tracing_export_api_key, trace, ItemHelpers
from openai import AsyncOpenAI
import asyncio
from customer_support.shared import client, ollama_client
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from openai.types.responses import ResponseTextDeltaEvent


set_tracing_disabled(False)
load_dotenv()
@function_tool(name_override="Basic_business_details", strict_mode=True,)
async def Basic_business_tool(details_query: str) -> str:
    """Fetches basic business details like return policy, delivery time, courier information, About Digitallink etc.
    Args: details_query (str): The query related to business details.
    details_query words can be "return_policy", "warranty", "delivery", "courier", "about_digitallink"
    Returns: str: The response to the business details query."""
    business_info = {
        "return_policy": "Once a product has been opened, it cannot be returned as it loses its value for us.",
        "warranty": "As Digitallink is an official partner of many brands, mobile warranties can be easily claimed. We provide a 3-day checking warranty — if any defect is found during this period, the device will be fully replaced. Additionally, all devices come with a 1-year official brand warranty.",
        "delivery": "Orders are delivered within 3-5 business days inshallah.",
        "courier":"M&P Courier service",
        "about_digitallink" : "Digitallink is one of Pakistan’s most trusted and reliable e-commerce platforms for purchasing latest mobile phones,committed to quality and customer satisfaction.",
        
    }
    details_query_lower = details_query.lower()
    for key in business_info:
        if key in details_query_lower:
            return business_info[key]
    return "I'm sorry, I don't have information on that topic. Please contact our support team for further assistance."

SYSTEM_PROMPT_BASIC_QUERY_AGENT = f"""{RECOMMENDED_PROMPT_PREFIX}

# ROLE:
You’re a Muslim Digital Link support agent. Help customers efficiently while following all rules.

# Instructions:
- Use tools for any business-related queries (e.g. Basic_business_tool). Never guess — only respond using tool output.
- Use the tool to get information about return_policy, warranty, delivery time, courier, about_digitallink
- Avoid topics like politics, religion, legal/medical advice, internal matters, or personal opinions.
- Be  professional, polite, and little Muslim touch — add emojis between sentences.
#Tools:
- Basic_business_tool:
   Use the words  "return_policy", "warranty", "delivery", "courier", "about_digitallink" to call this tool.
# PHRASES:
## For prohibited/irrelevent topics:
- "I'm sorry, I can't discuss that. Can I help with something else?"
- "That’s outside my scope — happy to help with anything else."

"""

basic_query_agent = Agent(
    name= "Basic Query Agent",
    instructions=SYSTEM_PROMPT_BASIC_QUERY_AGENT,
    tools=[
        Basic_business_tool
    ],
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    model_settings=ModelSettings(
        temperature=0.5,
        top_p =0.9,
        tool_choice="auto",),
    handoff_description="Handles all Basic business queries like return, warranty of the products, about digital link, courier, delivery."
)

set_tracing_disabled(False)
