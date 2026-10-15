import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.models import InvestigationRequest
from app.services.agent_service import AgentService


class FakeRepository:
    def __init__(self):
        self.saved_request = None
        self.saved_response = None

    def save(self, request, response):
        self.saved_request = request
        self.saved_response = response
        return "test-investigation-id"

    def get(self, investigation_id):
        return None

    def list_recent(self, limit=20):
        return []


class TestAgentService(unittest.TestCase):
    def test_build_investigation_context_preserves_resource_context(self):
        request = InvestigationRequest(
            question="Why is this Pod failing?",
            resource_type="Pod",
            resource_name="imagepull-demo",
            namespace="aiops-demo",
        )

        context = AgentService._build_investigation_context(
            request
        )

        self.assertIn(
            "User question: Why is this Pod failing?",
            context,
        )

        self.assertIn(
            "Resource type: Pod",
            context,
        )

        self.assertIn(
            "Resource name: imagepull-demo",
            context,
        )

        self.assertIn(
            "Namespace: aiops-demo",
            context,
        )

    def test_build_investigation_context_handles_missing_resource_context(
        self,
    ):
        request = InvestigationRequest(
            question="Why is my cluster unhealthy?",
        )

        context = AgentService._build_investigation_context(
            request
        )

        self.assertIn(
            "User question: Why is my cluster unhealthy?",
            context,
        )

        self.assertIn(
            "Resource type: None",
            context,
        )

        self.assertIn(
            "Resource name: None",
            context,
        )

        self.assertIn(
            "Namespace: None",
            context,
        )

    def test_parse_json_accepts_plain_json(self):
        text = """
        {
            "status": "Failed",
            "severity": "High"
        }
        """

        result = AgentService._parse_json(text)

        self.assertEqual(
            result,
            {
                "status": "Failed",
                "severity": "High",
            },
        )

    def test_parse_json_accepts_json_code_fence(self):
        text = """```json
{
    "status": "Failed",
    "severity": "High"
}
```"""

        result = AgentService._parse_json(text)

        self.assertEqual(
            result,
            {
                "status": "Failed",
                "severity": "High",
            },
        )

    def test_parse_json_returns_none_for_invalid_json(self):
        text = """
        {
            "status": "Failed",
            "severity":
        }
        """

        result = AgentService._parse_json(text)

        self.assertIsNone(result)

    def test_extract_response_returns_valid_response(self):
        response_json = """
        {
            "resource": {
                "type": "Pod",
                "name": "imagepull-demo",
                "namespace": "aiops-demo"
            },
            "assessment": {
                "status": "Failed",
                "severity": "High"
            },
            "facts": [
                "The Pod is in Pending state."
            ],
            "root_cause": "The configured image could not be pulled.",
            "hypotheses": [],
            "recommended_next_steps": [
                "Verify the configured image."
            ],
            "investigation": {
                "tools_used": [
                    "get_resource_summary",
                    "get_resource_events"
                ],
                "evidence_summary": [
                    "ImagePullBackOff was observed."
                ]
            }
        }
        """

        response = self._build_event(
            response_json
        )

        result = AgentService._extract_response(
            [response]
        )

        self.assertEqual(
            result.resource.type,
            "Pod",
        )

        self.assertEqual(
            result.resource.name,
            "imagepull-demo",
        )

        self.assertEqual(
            result.resource.namespace,
            "aiops-demo",
        )

        self.assertEqual(
            result.assessment.status,
            "Failed",
        )

        self.assertEqual(
            result.assessment.severity,
            "High",
        )

        self.assertEqual(
            result.root_cause,
            "The configured image could not be pulled.",
        )

    def test_extract_response_skips_invalid_json_and_accepts_later_valid_response(
        self,
    ):
        invalid_event = self._build_event(
            """
            {
                "resource":
            }
            """
        )

        valid_event = self._build_event(
            """
            {
                "resource": {
                    "type": "Pod",
                    "name": "imagepull-demo",
                    "namespace": "aiops-demo"
                },
                "assessment": {
                    "status": "Failed",
                    "severity": "High"
                },
                "facts": [],
                "root_cause": "Image could not be pulled.",
                "hypotheses": [],
                "recommended_next_steps": [],
                "investigation": {
                    "tools_used": [],
                    "evidence_summary": []
                }
            }
            """
        )

        result = AgentService._extract_response(
            [
                invalid_event,
                valid_event,
            ]
        )

        self.assertEqual(
            result.resource.name,
            "imagepull-demo",
        )

        self.assertEqual(
            result.root_cause,
            "Image could not be pulled.",
        )

    def test_extract_response_skips_invalid_schema_and_accepts_later_valid_response(
        self,
    ):
        invalid_schema_event = self._build_event(
            """
            {
                "resource": {
                    "type": "Pod",
                    "name": "imagepull-demo",
                    "namespace": "aiops-demo"
                },
                "assessment": {
                    "status": "Failed"
                },
                "facts": [],
                "root_cause": "Image could not be pulled.",
                "hypotheses": [],
                "recommended_next_steps": [],
                "investigation": {
                    "tools_used": [],
                    "evidence_summary": []
                }
            }
            """
        )

        valid_event = self._build_event(
            """
            {
                "resource": {
                    "type": "Pod",
                    "name": "imagepull-demo",
                    "namespace": "aiops-demo"
                },
                "assessment": {
                    "status": "Failed",
                    "severity": "High"
                },
                "facts": [],
                "root_cause": "Image could not be pulled.",
                "hypotheses": [],
                "recommended_next_steps": [],
                "investigation": {
                    "tools_used": [],
                    "evidence_summary": []
                }
            }
            """
        )

        result = AgentService._extract_response(
            [
                invalid_schema_event,
                valid_event,
            ]
        )

        self.assertEqual(
            result.assessment.severity,
            "High",
        )

    def test_extract_response_raises_when_no_valid_response_exists(
        self,
    ):
        invalid_event = self._build_event(
            """
            {
                "resource":
            }
            """
        )

        with self.assertRaisesRegex(
            ValueError,
            "The Kubernetes agent did not return a valid "
            "InvestigationResponse.",
        ):
            AgentService._extract_response(
                [invalid_event]
            )

    def test_investigate_attaches_persisted_investigation_id(
        self,
    ):
        repository = FakeRepository()

        service = AgentService(
            repository=repository
        )

        response_json = """
        {
            "resource": {
                "type": "Pod",
                "name": "imagepull-demo",
                "namespace": "aiops-demo"
            },
            "assessment": {
                "status": "Failed",
                "severity": "High"
            },
            "facts": [
                "ImagePullBackOff was observed."
            ],
            "root_cause": "The configured image could not be pulled.",
            "hypotheses": [],
            "recommended_next_steps": [
                "Verify the configured image."
            ],
            "investigation": {
                "tools_used": [
                    "get_resource_summary",
                    "get_resource_events"
                ],
                "evidence_summary": [
                    "ImagePullBackOff was observed."
                ]
            }
        }
        """

        service.runner.run_debug = AsyncMock(
            return_value=[
                self._build_event(response_json)
            ]
        )

        request = InvestigationRequest(
            question="Why is this Pod failing?",
            resource_type="Pod",
            resource_name="imagepull-demo",
            namespace="aiops-demo",
        )

        result = self._run_async(
            service.investigate(request)
        )

        self.assertEqual(
            result.investigation_id,
            "test-investigation-id",
        )

        self.assertIs(
            repository.saved_request,
            request,
        )

        self.assertIsNotNone(
            repository.saved_response,
        )

        self.assertEqual(
            repository.saved_response.root_cause,
            "The configured image could not be pulled.",
        )

    @staticmethod
    def _build_event(text: str):
        """
        Build a minimal object that resembles the ADK Event
        structure required by AgentService._extract_response().
        """

        part = SimpleNamespace(
            text=text
        )

        content = SimpleNamespace(
            parts=[part]
        )

        return SimpleNamespace(
            content=content
        )

    @staticmethod
    def _run_async(coroutine):
        import asyncio

        return asyncio.run(coroutine)


if __name__ == "__main__":
    unittest.main()