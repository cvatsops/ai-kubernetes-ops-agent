import json
from typing import Any

from google.adk.runners import InMemoryRunner

from app.agents.kubernetes_agent import root_agent
from app.api.models import InvestigationResponse


class AgentService:
    """Service responsible for executing the Kubernetes ADK agent."""

    def __init__(self):
        self.runner = InMemoryRunner(
            agent=root_agent,
            app_name="ai-kubernetes-ops-agent",
        )

    async def investigate(
        self,
        question: str,
        resource_type: str | None = None,
        resource_name: str | None = None,
        namespace: str | None = None,
    ) -> InvestigationResponse:
        """
        Execute a Kubernetes investigation using the user's
        question and optional resource context.
        """

        investigation_context = self._build_investigation_context(
            question=question,
            resource_type=resource_type,
            resource_name=resource_name,
            namespace=namespace,
        )

        response = await self.runner.run_debug(
            investigation_context
        )

        return self._extract_response(response)

    @staticmethod
    def _build_investigation_context(
        question: str,
        resource_type: str | None,
        resource_name: str | None,
        namespace: str | None,
    ) -> str:
        """
        Build explicit investigation context for the agent.

        Resource information supplied by the UI is treated as
        authoritative context rather than something the model
        needs to infer from the user's question.
        """

        context_lines = [
            "KUBERNETES INVESTIGATION CONTEXT:",
        ]

        if resource_type:
            context_lines.append(
                f"Resource type: {resource_type}"
            )

        if resource_name:
            context_lines.append(
                f"Resource name: {resource_name}"
            )

        if namespace:
            context_lines.append(
                f"Namespace: {namespace}"
            )

        context_lines.extend(
            [
                "",
                "USER QUESTION:",
                question,
            ]
        )

        return "\n".join(context_lines)

    @staticmethod
    def _extract_response(
        response: list[Any],
    ) -> InvestigationResponse:
        """
        Extract the structured InvestigationResponse from the
        final ADK event.

        ADK run_debug() returns a list of Event objects. With
        output_schema configured on the agent, the model's final
        response is expected to contain JSON matching the
        InvestigationResponse schema.
        """

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
    def _parse_json(text: str) -> dict | None:
        """
        Parse JSON returned by the structured-output agent.

        This accepts either:
        - plain JSON
        - JSON surrounded by whitespace
        - JSON inside a markdown code fence

        The normal expected format is plain JSON because the
        agent uses output_schema.
        """

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