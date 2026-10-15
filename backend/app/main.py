from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.models import (
    InvestigationHistoryItem,
    InvestigationHistoryResponse,
    InvestigationRequest,
    InvestigationResponse,
)
from app.repositories.firestore_investigation_repository import (
    FirestoreInvestigationRepository,
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


investigation_repository = (
    FirestoreInvestigationRepository()
)

agent_service = AgentService(
    repository=investigation_repository
)


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
        request
    )


@app.get(
    "/investigations",
    response_model=list[InvestigationHistoryItem],
)
async def list_investigations(
    limit: int = 20,
):
    """
    Return the most recent investigation history items.

    This endpoint is intended for the investigation history
    list/sidebar in the frontend.
    """

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100",
        )

    investigations = (
        investigation_repository.list_recent(
            limit=limit
        )
    )

    return [
        InvestigationHistoryItem.model_validate(
            investigation
        )
        for investigation in investigations
    ]


@app.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationHistoryResponse,
)
async def get_investigation(
    investigation_id: str,
):
    """
    Return one complete historical investigation.

    Opening a historical investigation does not execute
    Gemini or query Kubernetes.
    """

    investigation = investigation_repository.get(
        investigation_id
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Investigation '{investigation_id}' "
                "was not found."
            ),
        )

    return InvestigationHistoryResponse.model_validate(
        investigation
    )