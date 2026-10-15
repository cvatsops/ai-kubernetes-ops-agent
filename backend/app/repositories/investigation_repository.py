from abc import ABC, abstractmethod

from app.api.models import InvestigationRequest, InvestigationResponse


class InvestigationRepository(ABC):
    """
    Repository interface for investigation history.

    The service layer depends on this abstraction rather than
    directly depending on Firestore.
    """

    @abstractmethod
    def save(
        self,
        request: InvestigationRequest,
        response: InvestigationResponse,
    ) -> str:
        """
        Persist a completed investigation and return its ID.
        """
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        investigation_id: str,
    ) -> dict | None:
        """
        Retrieve one saved investigation by ID.

        Returns None when the investigation does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def list_recent(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """
        Return the most recent investigations.
        """
        raise NotImplementedError