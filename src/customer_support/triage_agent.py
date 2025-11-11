from agents import (
    Agent,
    Runner,
    set_tracing_disabled,
    ModelSettings,
    function_tool,
    OpenAIChatCompletionsModel,
    handoff
)
from agents.extensions import handoff_filters

from customer_support.order_agent import order_agent
from customer_support.product_agent import product_agent
from customer_support.Basic_query_agent import basic_query_agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio
from customer_support.shared import client, ollama_client

load_dotenv()

def dynamic_instructions() -> str:
    return f"""{RECOMMENDED_PROMPT_PREFIX}You are a customer support agent for digital link.
    #Role
    You are a triage agent that categorizes customer queries and hands them off to the appropriate
    specialized agent.
   
    #Goal
    Your goal is to categorize the user's query into one of the following categories:
   
    1. Order Related
    2. Product Information
    3. Basic Business details(like return policy, delivery related queries, courier information, About Digitallink etc.)
    ##After categorizing
    after you categorize the query, you will handoff the query to the appropriate agent.
    #Handoff:
    You have the following agents available to handoff the query to:
    1. Order Agent: Handles all order related queries.
    2. Product Agent: Handles all product information queries.
    3. Basic business query Agent: Handles all Basic business queries like return, warranty of the products, about digital link, courier, delivery time.
    Handoff greetings and general complements, feedback, or complaints to the Basic business query Agent.
    #instructions
    First analyze the query what the user is asking and then think which agent has the capability to answer the query.
    Handoff the query to the appropriate agent effectively.
    Do not reply by your own, always handoff to the appropriate agent.
    Do not hallucinate or make up information.
    ##example
    User: What is digitallink?.
    Triage Agent:(action) Handoff to Basic query Agent.
    ##another example
    User: I want to know about the status of my order.
    Triage Agent:(action) Handoff to Order Agent."""



triage_agent = Agent(
    name="Triage Agent",
    instructions= dynamic_instructions(),
    model = OpenAIChatCompletionsModel(model = "gemini-2.0-flash",openai_client=client),
    handoffs= [handoff(order_agent,input_filter=handoff_filters.remove_all_tools)
               ,handoff(product_agent,input_filter=handoff_filters.remove_all_tools)
               ,handoff(basic_query_agent,input_filter=handoff_filters.remove_all_tools)],
    model_settings=ModelSettings(temperature=0.4,
                                  top_p=0.9)
)



set_tracing_disabled(True)
   