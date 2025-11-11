#Import necessary libraries
import requests
import os
from dotenv import load_dotenv
from agents import (Agent,
Runner, 
set_tracing_disabled,
ModelSettings, 
function_tool,
OpenAIChatCompletionsModel, 
set_tracing_export_api_key,
trace,
ItemHelpers
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from openai.types.responses import ResponseTextDeltaEvent
from openai import AsyncOpenAI
import asyncio
from customer_support.shared import client, ollama_client
import re
from bs4 import BeautifulSoup

set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))
load_dotenv()
wc_base_url = os.getenv("WC_BASE_URL")
wc_consumer_key = os.getenv("WC_CONSUMER_KEY")  
wc_consumer_secret = os.getenv("WC_CONSUMER_SECRET")

auth = (wc_consumer_key, wc_consumer_secret)



def clean_description(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove all unwanted tags like <style>, <script>, etc.
    for tag in soup(["script", "style", "img", "a", "hr"]):
        tag.decompose()

    # Replace <li> with bullet points
    for li in soup.find_all("li"):
        li.insert_before("• ")

    # Add newlines after headers and paragraphs
    for tag in soup.find_all(["h1", "h2", "h3", "p", "ul"]):
        tag.append("\n")

    # Get clean text
    text = soup.get_text(separator=" ", strip=True)

    # Remove multiple spaces and trim
    cleaned_text = ' '.join(text.split())

    # Optional: format bullet points and paragraphs better
    cleaned_text = cleaned_text.replace("•", "\n•")

    return cleaned_text.strip()

set_tracing_disabled(True)
@function_tool(strict_mode=True)
async def get_product_details(product_name: str) -> dict:
    """
    Fetch product details from WooCommerce by product name with exact name matching.
    Returns a dictionary containing product info or an error message.
    """
    try:
        url = f"{wc_base_url}/products?search={product_name}"
        response = requests.get(
            url,
            auth=(wc_consumer_key, wc_consumer_secret,),
            timeout=10
        )

        if response.status_code == 200:
            products = response.json()

            # Match product name exactly (case-insensitive)
            exact_match = next(
                (p for p in products if p["name"].strip().lower() == product_name.strip().lower()),
                None
            )

            
            if exact_match:
                raw_desc = exact_match.get("description", "")

                # Remove all <a> tags
                cleaned_desc = re.sub(r'<a\s+href="[^"]*">(.*?)</a>', r'\1', raw_desc[:8000], flags=re.IGNORECASE)

                # Remove all <img ...> tags
                cleaned_desc = re.sub(r'<img[^>]*>', '', cleaned_desc, flags=re.IGNORECASE)

                # Clean the description using BeautifulSoup
                cleaned_desc = clean_description(cleaned_desc)

                return {
                    "id": exact_match["id"],
                    "name": exact_match["name"],
                    "price": exact_match["price"],
                    "stock_status": exact_match["stock_status"],
                    "description": cleaned_desc[:2000],
                    
                }
                
            else:
                return {"error": f"No exact match found for '{product_name}'."}

        elif response.status_code == 404:
            return {"error": "Product not found (404)."}
        elif response.status_code == 401:
            return {"error": "Authentication failed. Check your WooCommerce API keys (401)."}
        else:
            return {"error": f"Error fetching product: {response.status_code} - {response.text}"}

    except requests.exceptions.Timeout:
        return {"error": "Request timed out while fetching product. Please try again later."}
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while fetching product: {str(e)}"}

SYSTEM_INSRUCTIONS_PRODUCT_AGENT = f"""{RECOMMENDED_PROMPT_PREFIX}

# ROLE:
You’re a Muslim Digital Link support agent. Help customers efficiently while following all rules.

# Instructions:
- Use tools for any product-related queries like stock, specs, features (e.g. get_product_details()). Never guess — only respond using tool output. price will be in PKR.
- Avoid topics like politics, religion, legal/medical advice, internal matters.
- Be concise, professional, and polite and little Muslim touch— add emojis between sentences.
- after discussing the official price if it is mentioned in description, otherwise tell them what we are offering. remember that the price which you get as tool output is ours
- Help the users to make decisions by comparing products if they ask for it. or if they ask for a recommendation, give them the best recommendation based on the product description.
#if tool fails:
- "I couldn't find that product. Can you check the name and try again?"

# PHRASES:
## For prohibited/irrelevent topics:
- "That’s outside my scope — happy to help with anything else."
- "I'm sorry, I can't discuss that. Can I help with something else?"


"""
product_agent = Agent(
    name= "Product Agent",
    instructions= SYSTEM_INSRUCTIONS_PRODUCT_AGENT,
    tools = [get_product_details],
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
    model_settings=ModelSettings(
        temperature=0.5,
        top_p=0.9,
        tool_choice="auto",
        max_tokens=1000
    ),
    handoff_description="Handles all product information queries."
)
    

