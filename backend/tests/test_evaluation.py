import unittest

from app.api.models import InvestigationResponse
from app.services.evaluation import InvestigationEvaluator
from test_investigation_cases import INVESTIGATION_CASES


class TestInvestigationEvaluator(unittest.TestCase):

    def test_healthy_deployment_passes(self):
        case = self._get_case("healthy_deployment")

        response = self._build_response(
            status="Healthy",
            severity="Low",
            facts=[
                "Deployment has 2 desired replicas.",
                "Deployment has 2 ready replicas.",
                "Deployment has 2 available replicas.",
            ],
            root_cause="No unhealthy condition was identified.",
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.failures, [])

    def test_image_pull_failure_passes(self):
        case = self._get_case("image_pull_failure")

        response = self._build_response(
            status="Failed",
            severity="High",
            facts=[
                "Pod is affected by ErrImagePull.",
                "Pod is affected by ImagePullBackOff.",
            ],
            root_cause=(
                "The configured container image could not be pulled."
            ),
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(result.passed)

    def test_real_image_pull_failure_response_passes(self):
        """
        Evaluate the actual response returned by the live agent
        for the demo-api ImagePullBackOff scenario.
        """

        case = self._get_case("image_pull_failure")

        response = InvestigationResponse(
            resource={
                "type": "Pod",
                "name": "demo-api-7d66957847-k27s7",
                "namespace": "aiops-demo",
            },
            assessment={
                "status": "Failed",
                "severity": "High",
            },
            facts=[
                (
                    "The Pod demo-api-7d66957847-k27s7 "
                    "is in the 'Pending' phase."
                ),
                (
                    "Kubernetes events show 'Failed to pull image "
                    "\"nginx:this-image-does-not-exist\"'."
                ),
                (
                    "The Pod exhibits 'ErrImagePull' "
                    "and 'ImagePullBackOff' events."
                ),
            ],
            root_cause=(
                "The Pod is unable to start because Kubernetes "
                "cannot pull the configured container image "
                "'nginx:this-image-does-not-exist', as the image "
                "was not found in the registry."
            ),
            hypotheses=[],
            recommended_next_steps=[
                (
                    "Verify that the configured image name and tag "
                    "'nginx:this-image-does-not-exist' are correct."
                ),
                (
                    "Verify that the image exists in the intended "
                    "image registry."
                ),
            ],
            investigation={
                "tools_used": [
                    "get_resource_summary",
                    "get_resource_events",
                ],
                "evidence_summary": [
                    (
                        "Kubernetes events indicate 'ErrImagePull' "
                        "and 'ImagePullBackOff' due to the image "
                        "not being found in the registry."
                    ),
                ],
            },
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(
            result.passed,
            msg="\n".join(result.failures),
        )

    def test_image_pull_failure_fails_when_evidence_is_missing(self):
        case = self._get_case("image_pull_failure")

        response = self._build_response(
            status="Failed",
            severity="High",
            facts=[
                "Pod is not running.",
            ],
            root_cause="The Pod has a startup problem.",
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertFalse(result.passed)

        self.assertTrue(
            any(
                "ErrImagePull" in failure
                for failure in result.failures
            )
        )

    def test_deployment_rollout_requires_relationship_evidence(self):
        case = self._get_case(
            "deployment_rollout_failure"
        )

        response = self._build_response(
            status="Failed",
            severity="High",
            facts=[
                "Deployment rollout is unhealthy.",
                "Deployment demo-api manages ReplicaSet demo-api-7d66957847."
                "ReplicaSet demo-api-7d66957847 manages the affected Pod."
                "Pod is failing because the image cannot be pulled.",
            ],
            root_cause=(
                "The Deployment rollout is failing because the "
                "ReplicaSet manages a Pod with an image pull failure."
            ),
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(
            result.passed,
            msg="\n".join(result.failures),
    )   

    def test_wrong_status_fails(self):
        case = self._get_case("image_pull_failure")

        response = self._build_response(
            status="Healthy",
            severity="High",
            facts=[
                "ErrImagePull was observed.",
                "ImagePullBackOff was observed.",
            ],
            root_cause=(
                "The configured image could not be pulled."
            ),
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertFalse(result.passed)

        self.assertTrue(
            any(
                "Expected status" in failure
                for failure in result.failures
            )
        )

    def test_cpu_case_does_not_require_throttling(self):
        case = self._get_case("cpu_pressure")

        response = self._build_response(
            status="Degraded",
            severity="Medium",
            facts=[
                "CPU usage is elevated.",
                "Prometheus metrics show high CPU consumption.",
            ],
            root_cause=(
                "The workload is experiencing high CPU usage."
            ),
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(result.passed)

    @staticmethod
    def _get_case(name: str) -> dict:
        for case in INVESTIGATION_CASES:
            if case["name"] == name:
                return case

        raise AssertionError(
            f"Investigation case not found: {name}"
        )

    @staticmethod
    def _build_response(
        status: str,
        severity: str,
        facts: list[str],
        root_cause: str,
    ) -> InvestigationResponse:
        return InvestigationResponse(
            resource={
                "type": "Pod",
                "name": "test-resource",
                "namespace": "aiops-demo",
            },
            assessment={
                "status": status,
                "severity": severity,
            },
            facts=facts,
            root_cause=root_cause,
            hypotheses=[],
            recommended_next_steps=[],
            investigation={
                "tools_used": [],
                "evidence_summary": [],
            },
        )


if __name__ == "__main__":
    unittest.main()