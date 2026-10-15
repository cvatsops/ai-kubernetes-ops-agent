import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from app.api.models import InvestigationRequest, InvestigationResponse
from app.repositories.firestore_investigation_repository import (
    FirestoreInvestigationRepository,
)


class TestFirestoreInvestigationRepository(unittest.TestCase):

    def test_save_creates_investigation_document(self):
        collection = Mock()
        document = Mock()

        collection.document.return_value = document

        client = Mock()
        client.collection.return_value = collection

        repository = FirestoreInvestigationRepository(
            client=client
        )

        request = InvestigationRequest(
            question="Why is this Pod failing?",
            resource_type="Pod",
            resource_name="imagepull-demo",
            namespace="aiops-demo",
        )

        response = self._build_response()

        investigation_id = repository.save(
            request,
            response,
        )

        self.assertIsNotNone(
            investigation_id
        )

        collection.document.assert_called_once_with(
            investigation_id
        )

        document.set.assert_called_once()

        saved_document = document.set.call_args.args[0]

        self.assertEqual(
            saved_document["id"],
            investigation_id,
        )

        self.assertEqual(
            saved_document["question"],
            "Why is this Pod failing?",
        )

        self.assertEqual(
            saved_document["resource"]["type"],
            "Pod",
        )

        self.assertEqual(
            saved_document["resource"]["name"],
            "imagepull-demo",
        )

        self.assertEqual(
            saved_document["assessment"]["status"],
            "Failed",
        )

        self.assertEqual(
            saved_document["assessment"]["severity"],
            "High",
        )

        self.assertEqual(
            saved_document["root_cause"],
            "The configured image could not be pulled.",
        )

        self.assertIsInstance(
            saved_document["created_at"],
            datetime,
        )

        self.assertEqual(
            saved_document["created_at"].tzinfo,
            timezone.utc,
        )

    def test_get_returns_saved_document(self):
        document = Mock()
        document.exists = True

        expected_document = {
            "id": "investigation-123",
            "question": "Why is this Pod failing?",
            "assessment": {
                "status": "Failed",
                "severity": "High",
            },
        }

        document.to_dict.return_value = (
            expected_document
        )

        collection = Mock()

        collection.document.return_value.get.return_value = (
            document
        )

        client = Mock()
        client.collection.return_value = collection

        repository = FirestoreInvestigationRepository(
            client=client
        )

        result = repository.get(
            "investigation-123"
        )

        self.assertEqual(
            result,
            expected_document,
        )

        collection.document.assert_called_once_with(
            "investigation-123"
        )

    def test_get_returns_none_when_document_does_not_exist(self):
        document = Mock()
        document.exists = False

        collection = Mock()

        collection.document.return_value.get.return_value = (
            document
        )

        client = Mock()
        client.collection.return_value = collection

        repository = FirestoreInvestigationRepository(
            client=client
        )

        result = repository.get(
            "missing-investigation"
        )

        self.assertIsNone(result)

    def test_list_recent_returns_documents(self):
        first_document = Mock()
        first_document.to_dict.return_value = {
            "id": "investigation-1",
            "question": "Why is Pod A failing?",
        }

        second_document = Mock()
        second_document.to_dict.return_value = {
            "id": "investigation-2",
            "question": "Why is Pod B restarting?",
        }

        query = Mock()

        query.limit.return_value.stream.return_value = [
            first_document,
            second_document,
        ]

        collection = Mock()

        collection.order_by.return_value = query

        client = Mock()
        client.collection.return_value = collection

        repository = FirestoreInvestigationRepository(
            client=client
        )

        result = repository.list_recent(
            limit=10
        )

        self.assertEqual(
            result,
            [
                {
                    "id": "investigation-1",
                    "question": "Why is Pod A failing?",
                },
                {
                    "id": "investigation-2",
                    "question": "Why is Pod B restarting?",
                },
            ],
        )

        collection.order_by.assert_called_once()

        query.limit.assert_called_once_with(10)

    @staticmethod
    def _build_response() -> InvestigationResponse:
        return InvestigationResponse(
            resource={
                "type": "Pod",
                "name": "imagepull-demo",
                "namespace": "aiops-demo",
            },
            assessment={
                "status": "Failed",
                "severity": "High",
            },
            facts=[
                "Pod is in Pending state.",
                "ErrImagePull was observed.",
                "ImagePullBackOff was observed.",
            ],
            root_cause=(
                "The configured image could not be pulled."
            ),
            hypotheses=[],
            recommended_next_steps=[
                "Verify the configured image."
            ],
            investigation={
                "tools_used": [
                    "get_resource_summary",
                    "get_resource_events",
                ],
                "evidence_summary": [
                    "ImagePullBackOff was observed."
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()