
from datetime import datetime, timezone
from uuid import uuid4

from google.cloud import firestore

from app.api.models import (
    InvestigationRequest,
    InvestigationResponse,
)
from app.config import (
    FIRESTORE_PROJECT_ID,
    FIRESTORE_DATABASE_ID,
    FIRESTORE_COLLECTION_NAME,
)
from app.repositories.investigation_repository import (
    InvestigationRepository,
)


class FirestoreInvestigationRepository(
    InvestigationRepository
):
    """
    Firestore implementation of investigation history.

    Collection structure:

        {collection_name}/{investigation_id}
    """

    def __init__(
        self,
        client: firestore.Client | None = None,
    ):
        self.client = client or firestore.Client(
            project=FIRESTORE_PROJECT_ID,
            database=FIRESTORE_DATABASE_ID,
        )

        self.collection = self.client.collection(
            FIRESTORE_COLLECTION_NAME
        )

    def save(
        self,
        request: InvestigationRequest,
        response: InvestigationResponse,
    ) -> str:
        investigation_id = str(uuid4())

        document = {
            "id": investigation_id,
            "created_at": datetime.now(timezone.utc),
            "question": request.question,
            "resource": (
                response.resource.model_dump()
                if response.resource
                else None
            ),
            "assessment": response.assessment.model_dump(),
            "facts": response.facts,
            "root_cause": response.root_cause,
            "hypotheses": response.hypotheses,
            "recommended_next_steps": (
                response.recommended_next_steps
            ),
            "investigation": (
                response.investigation.model_dump()
            ),
        }

        self.collection.document(
            investigation_id
        ).set(document)

        return investigation_id

    def get(
        self,
        investigation_id: str,
    ) -> dict | None:
        document = (
            self.collection
            .document(investigation_id)
            .get()
        )

        if not document.exists:
            return None

        return document.to_dict()

    def list_recent(
        self,
        limit: int = 20,
    ) -> list[dict]:
        documents = (
            self.collection
            .order_by(
                "created_at",
                direction=firestore.Query.DESCENDING,
            )
            .limit(limit)
            .stream()
        )

        return [
            document.to_dict()
            for document in documents
        ]