"""FastAPI server exposing the Romanian Tax Agents system as REST API."""

import uuid
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ro_tax_agents.graph import compile_graph

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global graph instance
_graph = None


def get_graph():
    """Get or create the compiled graph."""
    global _graph
    if _graph is None:
        _graph = compile_graph()
    return _graph


class RouteRequest(BaseModel):
    """Request model for routing."""
    query: str = Field(..., description="User query to route")


class RouteResponse(BaseModel):
    """Response model for routing."""
    response: str = Field(..., description="Agent response")
    detected_intent: str = Field(..., description="Detected intent")
    intent_confidence: float = Field(..., description="Confidence score (0-1)")
    workflow_status: str = Field(..., description="Workflow status")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize graph on startup."""
    print("Initializing Romanian Tax Agents system...")
    get_graph()
    print("System ready!")
    yield


app = FastAPI(
    title="Romanian Tax Agents API",
    description="Multi-agent system for Romanian tax services",
    version="0.1.2",
    lifespan=lifespan,
)

# Add CORS middleware to allow requests from the HTML frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/route", response_model=RouteResponse)
async def route_request(request: RouteRequest):
    """Route a user query to the appropriate agent.

    Args:
        request: RouteRequest with the user's query

    Returns:
        RouteResponse with agent's response and detected intent
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        logger.info(f"Processing query: {request.query}")
        graph = get_graph()
        session_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}

        result = graph.invoke({"query": request.query}, config)
        logger.info(f"Result: {result}")

        return RouteResponse(
            response=result.get("response", "No response generated"),
            detected_intent=result.get("detected_intent", "unknown"),
            intent_confidence=result.get("intent_confidence", 0.0),
            workflow_status=result.get("workflow_status", "completed"),
        )
    except Exception as e:
        logger.exception(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
