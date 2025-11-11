# Customer Support Agent

A multi-agent chatbot designed to handle customer queries for an e-commerce store. This project uses the `openai-agents` SDK and FastAPI to create a robust support system that can be accessed via a command-line interface or a web API.

## Overview

The application is structured around a "triage" agent that first categorizes incoming user queries. Based on the category, the query is then routed to a specialized agent for handling:
- **Order Agent:** Handles questions about order status.
- **Product Agent:** Answers questions about product details.
- **Basic Query Agent:** Manages general questions about the business.

The Order and Product agents are equipped with tools to fetch live data from a WooCommerce store.

## Features

- **Multi-Agent Architecture:** Intelligently routes queries to the correct agent.
- **WooCommerce Integration:** Fetches real-time order and product data.
- **Dual Interface:** Can be run as a local command-line application or as a web API.
- **Asynchronous API:** The FastAPI backend supports streaming responses, suitable for real-time chatbot UIs.
- **Extensible:** New agents and tools can be easily added to expand functionality.

## Architecture

1.  **Triage Agent:** The entry point for all user queries. It determines if the query is about an order, a product, or a general question.
2.  **Specialized Agents:**
    - `order_agent`: Uses a `get_order_status` tool connected to the WooCommerce API.
    - `product_agent`: Uses a `get_product_details` tool connected to the WooCommerce API.
    - `basic_query_agent`: Handles all other queries.
3.  **Tooling:** Agents use functions that call the WooCommerce REST API to retrieve information.

## Getting Started

### Prerequisites

- Python 3.13 or higher
- `uv` (or `pip`) for package management

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hassanirshad-1/Customer_support_agent.git
    cd Customer_support_agent
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    The project uses `uv` for build management. You can install the project and its dependencies with:
    ```bash
    pip install .
    ```

4.  **Configure Environment Variables:**
    Create a file named `.env` in the root of the project directory. This file will store your secret keys. Copy the example below and replace the placeholder values.

    **.env.example**
    ```
    OPENAI_API_KEY="sk-..."
    WC_BASE_URL="https://your-store.com"
    WC_CONSUMER_KEY="ck_..."
    WC_CONSUMER_SECRET="cs_..."
    ```

## Usage

You can interact with the customer support agent in two ways:

### 1. Command-Line Interface (CLI)

To start a chat session in your terminal, run:

```bash
python src/customer_support/main.py
```

The application will prompt you for input, and you can chat directly with the agent.

### 2. Web API

The project includes a FastAPI server to expose the agent via an HTTP API.

1.  **Start the server:**
    ```bash
    uvicorn src.customer_support.api:app --reload
    ```

2.  **Interact with the API:**
    You can send a POST request to the `/chat` endpoint to get a response from the agent.

    - **URL:** `http://127.0.0.1:8000/chat`
    - **Method:** `POST`
    - **Body (JSON):**
      ```json
      {
        "query": "What is the status of order 123?"
      }
      ```
    The API will stream the agent's response back.
