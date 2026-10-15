import json
from typing import Any

from google.adk.runners import InMemoryRunner

from app.agents.kubernetes_agent import root_agent
from app.api.models import InvestigationRequest, InvestigationResponse
from app.repositories.investigation_repository import InvestigationRepository


class AgentService:
    def __init__(
        self,
        repository: InvestigationRepository | None = None,
    ):
        self.runner = InMemoryRunner(
            agent=root_agent,
            app_name="ai-kubernetes-ops-agent",
        )
        self.repository = repository

    async def investigate(
        self,
        request: InvestigationRequest,
    ) -> InvestigationResponse:
        investigation_context = self._build_investigation_context(
            request
        )

        response = await self.runner.run_debug(
            investigation_context
        )

        investigation_response = self._extract_response(
            response
        )

        if self.repository is not None:
            investigation_id = self.repository.save(
                request=request,
                response=investigation_response,
            )

            investigation_response.investigation_id = (
                investigation_id
            )

        return investigation_response

    @staticmethod
    def _build_investigation_context(
        request: InvestigationRequest,
    ) -> str:
        return (
            "INVESTIGATION CONTEXT\n"
            "\n"
            f"User question: {request.question}\n"
            f"Resource type: {request.resource_type}\n"
            f"Resource name: {request.resource_name}\n"
            f"Namespace: {request.namespace}\n"
        )

    @staticmethod
    def _extract_response(
        response: list[Any],
    ) -> InvestigationResponse:
        for event in reversed(response):
            content = getattr(event, "content", None)

            if not content:
                continue

            parts = getattr(content, "parts", None)

            if not parts:
                continue

            for part in parts:
                text = getattr(part, "text", None)

                if not text:
                    continue

                parsed = AgentService._parse_json(text)

                if parsed is None:
                    continue

                try:
                    return InvestigationResponse.model_validate(
                        parsed
                    )
                except Exception:
                    continue

        raise ValueError(
            "The Kubernetes agent did not return a valid "
            "InvestigationResponse."
        )

    @staticmethod
    def _parse_json(
        text: str,
    ) -> dict | None:
        cleaned = text.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

            if cleaned.startswith("json"):
                cleaned = cleaned[4:].lstrip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        return parsed