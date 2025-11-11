from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
import time
from datetime import datetime
from collections import defaultdict
from openai.types.responses import ResponseTextDeltaEvent

import os
from agents import Runner, RunContextWrapper, set_tracing_disabled, ItemHelpers
from customer_support.triage_agent import triage_agent
set_tracing_disabled(False)
openai_api_key = os.getenv("OPENAI_API_KEY")
# -----------------------------------
# 🔒 Rate limiting configuration
# -----------------------------------
RATE_LIMIT_DURATION = 60  # seconds
MAX_REQUESTS = 30         # per IP per duration
rate_limit_store: Dict[str, List[float]] = defaultdict(list)

def get_request_rate(client_ip: str) -> int:
    now = time.time()
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if now - t < RATE_LIMIT_DURATION
    ]
    return len(rate_limit_store[client_ip])

async def rate_limit(request: Request):
    client_ip = request.client.host
    count = get_request_rate(client_ip)
    if count >= MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many requests, try again later.")
    rate_limit_store[client_ip].append(time.time())


# -----------------------------------
# ⚙️ FastAPI initialization
# -----------------------------------
app = FastAPI(
    title="Digital Link Customer Support (Streaming)",
    description="Multi-agent AI support system using OpenAI Agents SDK (streaming mode)",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# shared runtime context (keeps conversation across requests)
run_context = RunContextWrapper(context={})


# -----------------------------------
# 📦 Request validation
# -----------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    user_id: Optional[str] = Field(None, description="User/session identifier")

    @validator("message")
    def sanitize(cls, v):
        v = v.replace("\x00", "")
        if any(x in v.lower() for x in ["<script>", "javascript:", "data:"]):
            raise ValueError("Message contains disallowed content")
        return v.strip()


# -----------------------------------
# 💬 Streaming endpoint (single)
# -----------------------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    async def event_stream():
        try:
            stream_result = Runner.run_streamed(
                triage_agent, request.message, context=run_context
            )
            async for event in stream_result.stream_events():
                # ✅ Bas streaming text bhejo - simple!
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    delta = event.data.delta
                    if delta:
                        yield delta
            
            yield "[DONE]"
        except Exception as e:
            yield f"[ERROR] {str(e)}"

    return StreamingResponse(event_stream(), media_type="text/plain")


# -----------------------------------
# 🩺 Health check
# -----------------------------------
@app.get("/")
async def health():
    return {
        "status": "ok",
        "service": "Digital Link Support API (Streaming)",
        "sdk_mode": "Agents SDK",
        "time": datetime.utcnow().isoformat()
    }
