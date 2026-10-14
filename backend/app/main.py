from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.models import (
    InvestigationRequest,
    InvestigationResponse,
)

from app.services.agent_service import AgentService


app = FastAPI(
    title="AI Kubernetes Ops Agent",
    description=(
        "AI-powered Kubernetes troubleshooting agent "
        "using Google ADK and Vertex AI."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent_service = AgentService()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai-kubernetes-ops-agent",
    }


@app.post(
    "/investigate",
    response_model=InvestigationResponse,
)
async def investigate(
    request: InvestigationRequest,
):
    return await agent_service.investigate(
        question=request.question,
        resource_type=request.resource_type,
        resource_name=request.resource_name,
        namespace=request.namespace,
    )