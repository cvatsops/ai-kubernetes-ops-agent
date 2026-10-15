from unittest import TestCase

from app.api.models import (
    Assessment,
    InvestigationMetadata,
    InvestigationResponse,
    ResourceReference,
)
from app.services.evaluation import InvestigationEvaluator
from tests.test_investigation_cases import INVESTIGATION_CASES


class TestInvestigationEvaluator(TestCase):

    @staticmethod
    def _build_response(
        *,
        status: str = "Healthy",
        severity: str = "Low",
        facts: list[str] | None = None,
        root_cause: str = "No confirmed issue.",
        hypotheses: list[str] | None = None,
        recommended_next_steps: list[str] | None = None,
        tools_used: list[str] | None = None,
        evidence_summary: list[str] | None = None,
    ) -> InvestigationResponse:
        """
        Build a simple deterministic InvestigationResponse.

        This helper is used by focused evaluator tests where the
        complete investigation matrix is not required.
        """

        return InvestigationResponse(
            resource=ResourceReference(
                type="Deployment",
                name="demo-api",
                namespace="aiops-demo",
            ),
            assessment=Assessment(
                status=status,
                severity=severity,
            ),
            facts=facts or [],
            root_cause=root_cause,
            hypotheses=hypotheses or [],
            recommended_next_steps=recommended_next_steps or [],
            investigation=InvestigationMetadata(
                tools_used=tools_used or [],
                evidence_summary=evidence_summary or [],
            ),
        )

    @staticmethod
    def _build_matrix_response(
        case: dict,
        omit_evidence: str | None = None,
        omit_root_cause_keyword: str | None = None,
    ) -> InvestigationResponse:
        """
        Build a deterministic synthetic response for a case.

        The investigation case definitions describe evaluation
        expectations rather than a specific Kubernetes resource
        name or namespace, so this helper uses fixed test values.

        omit_evidence:
            Removes the selected evidence from all generated response
            fields so the evaluator should reject the response.

        omit_root_cause_keyword:
            Removes the selected root-cause keyword from the root
            cause so the evaluator should reject the response.
        """

        def contains_term(text: str, term: str) -> bool:
            return term.lower() in text.lower()

        facts = []

        for evidence in case["required_evidence"]:
            if (
                omit_evidence is not None
                and contains_term(evidence, omit_evidence)
            ):
                continue

            facts.append(evidence)

        root_cause_keywords = []

        for keyword in case["root_cause_keywords"]:
            if (
                omit_root_cause_keyword is not None
                and contains_term(
                    keyword,
                    omit_root_cause_keyword,
                )
            ):
                continue

            if (
                omit_evidence is not None
                and contains_term(
                    keyword,
                    omit_evidence,
                )
            ):
                continue

            root_cause_keywords.append(keyword)

        if root_cause_keywords:
            root_cause = (
                "The investigation confirms "
                + ", ".join(root_cause_keywords)
                + "."
            )
        else:
            root_cause = (
                "The investigation found no confirmed root cause."
            )

        evidence_summary = list(facts)

        return InvestigationResponse(
            resource=ResourceReference(
                type=case["resource_type"],
                name="test-resource",
                namespace="aiops-demo",
            ),
            assessment=Assessment(
                status=case["expected_status"],
                severity=(
                    case["expected_severity"]
                    if case["expected_severity"] is not None
                    else "Medium"
                ),
            ),
            facts=facts,
            root_cause=root_cause,
            hypotheses=[],
            recommended_next_steps=[
                (
                    "Review the confirmed evidence and validate "
                    "the affected configuration."
                )
            ],
            investigation=InvestigationMetadata(
                tools_used=[
                    "get_resource_summary",
                ],
                evidence_summary=evidence_summary,
            ),
        )

    def test_healthy_deployment_passes(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "healthy_deployment"
        )

        response = self._build_matrix_response(case)

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(
            result.passed,
            msg=result.failures,
        )

        self.assertEqual(
            result.failures,
            [],
        )

    def test_image_pull_failure_passes(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "image_pull_failure"
        )

        response = self._build_matrix_response(case)

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(
            result.passed,
            msg=result.failures,
        )

        self.assertEqual(
            result.failures,
            [],
        )

    def test_image_pull_failure_fails_when_evidence_is_missing(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "image_pull_failure"
        )

        evidence = case["required_evidence"][0]

        response = self._build_matrix_response(
            case,
            omit_evidence=evidence,
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertFalse(result.passed)

        self.assertIn(
            f"Required evidence not found: '{evidence}'.",
            result.failures,
        )

    def test_readiness_failure_uses_degraded_status(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "readiness_failure"
        )

        response = self._build_matrix_response(case)

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(
            result.passed,
            msg=result.failures,
        )

        self.assertEqual(
            response.assessment.status,
            "Degraded",
        )

    def test_readiness_failure_rejects_failed_status(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "readiness_failure"
        )

        response = self._build_matrix_response(case)

        response.assessment.status = "Failed"

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertFalse(result.passed)

        self.assertIn(
            "Expected status 'Degraded', got 'Failed'.",
            result.failures,
        )

    def test_wrong_status_fails(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "healthy_deployment"
        )

        response = self._build_matrix_response(case)

        response.assessment.status = "Failed"

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertFalse(result.passed)

        self.assertIn(
            "Expected status 'Healthy', got 'Failed'.",
            result.failures,
        )

    def test_every_investigation_case_has_a_passing_response(self):
        """
        Every case in the formal evaluation matrix must be satisfied
        by its corresponding deterministic response.
        """

        for case in INVESTIGATION_CASES:
            with self.subTest(case=case["name"]):
                response = self._build_matrix_response(case)

                result = InvestigationEvaluator.evaluate(
                    case,
                    response,
                )

                self.assertTrue(
                    result.passed,
                    msg=(
                        f"Case '{case['name']}' failed evaluation: "
                        f"{result.failures}"
                    ),
                )

    def test_every_case_requires_expected_status(self):
        """
        Verify that the evaluator rejects a response when the
        expected status is changed to an incorrect value.
        """

        for case in INVESTIGATION_CASES:
            with self.subTest(case=case["name"]):
                response = self._build_matrix_response(case)

                original_status = case["expected_status"]

                wrong_status = {
                    "Healthy": "Degraded",
                    "Degraded": "Failed",
                    "Failed": "Healthy",
                }[original_status]

                response.assessment.status = wrong_status

                result = InvestigationEvaluator.evaluate(
                    case,
                    response,
                )

                self.assertFalse(result.passed)

                self.assertIn(
                    (
                        f"Expected status '{original_status}', "
                        f"got '{wrong_status}'."
                    ),
                    result.failures,
                )

    def test_required_evidence_is_checked_for_every_case(self):
        """
        Remove each case's first required evidence item from the
        generated response and verify that the evaluator detects
        the missing evidence.

        The selected evidence is removed from all generated fields,
        including the synthetic root cause.
        """

        for case in INVESTIGATION_CASES:
            with self.subTest(case=case["name"]):
                evidence = case["required_evidence"][0]

                response = self._build_matrix_response(
                    case,
                    omit_evidence=evidence,
                )

                result = InvestigationEvaluator.evaluate(
                    case,
                    response,
                )

                self.assertFalse(
                    result.passed,
                    msg=(
                        f"Evaluator incorrectly passed case "
                        f"'{case['name']}' after removing required "
                        f"evidence '{evidence}'."
                    ),
                )

                self.assertIn(
                    f"Required evidence not found: '{evidence}'.",
                    result.failures,
                )

    def test_root_cause_keywords_are_checked_for_every_case(self):
        """
        For cases that define root-cause keywords, remove the first
        keyword and verify that the evaluator detects the missing
        root-cause keyword.
        """

        for case in INVESTIGATION_CASES:
            if not case["root_cause_keywords"]:
                continue

            with self.subTest(case=case["name"]):
                keyword = case["root_cause_keywords"][0]

                response = self._build_matrix_response(
                    case,
                    omit_root_cause_keyword=keyword,
                )

                result = InvestigationEvaluator.evaluate(
                    case,
                    response,
                )

                self.assertFalse(
                    result.passed,
                    msg=(
                        f"Evaluator incorrectly passed case "
                        f"'{case['name']}' after removing root-cause "
                        f"keyword '{keyword}'."
                    ),
                )

                self.assertIn(
                    (
                        "Expected root-cause keyword not found: "
                        f"'{keyword}'."
                    ),
                    result.failures,
                )

    def test_deployment_rollout_requires_relationship_evidence(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "deployment_rollout_failure"
        )

        response = self._build_matrix_response(case)

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(
            result.passed,
            msg=result.failures,
        )

        relationship_evidence = next(
            (
                evidence
                for evidence in case["required_evidence"]
                if "replicaset" in evidence.lower()
            ),
            None,
        )

        self.assertIsNotNone(
            relationship_evidence,
            msg=(
                "Deployment rollout failure case must require "
                "ReplicaSet relationship evidence."
            ),
        )

        response_without_relationship_evidence = (
            self._build_matrix_response(
                case,
                omit_evidence=relationship_evidence,
            )
        )

        result_without_relationship_evidence = (
            InvestigationEvaluator.evaluate(
                case,
                response_without_relationship_evidence,
            )
        )

        self.assertFalse(
            result_without_relationship_evidence.passed
        )

        self.assertIn(
            (
                "Required evidence not found: "
                f"'{relationship_evidence}'."
            ),
            result_without_relationship_evidence.failures,
        )

    def test_cpu_case_does_not_require_throttling(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "cpu_pressure"
        )

        response = self._build_matrix_response(case)

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(
            result.passed,
            msg=result.failures,
        )

        required_evidence_text = " ".join(
            case["required_evidence"]
        ).lower()

        root_cause_text = " ".join(
            case["root_cause_keywords"]
        ).lower()

        self.assertNotIn(
            "throttling",
            required_evidence_text,
        )

        self.assertNotIn(
            "throttling",
            root_cause_text,
        )

    def test_real_image_pull_failure_response_passes(self):
        """
        Evaluate the validated ImagePullBackOff response returned
        by the live Kubernetes investigation.

        This test intentionally uses a fixed response so that the
        evaluation test suite remains deterministic and does not
        require a live Kubernetes cluster or Gemini call.
        """

        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "image_pull_failure"
        )

        response = InvestigationResponse(
            resource=ResourceReference(
                type="Pod",
                name="demo-api-7d66957847-k27s7",
                namespace="aiops-demo",
            ),
            assessment=Assessment(
                status="Failed",
                severity="High",
            ),
            facts=[
                (
                    "The Pod demo-api-7d66957847-k27s7 "
                    "is in Pending phase."
                ),
                (
                    "The Pod is not Ready."
                ),
                (
                    "Kubernetes events show "
                    "'ErrImagePull' for the configured image."
                ),
                (
                    "Kubernetes events show "
                    "'Back-off pulling image "
                    "\"nginx:this-image-does-not-exist\"'."
                ),
                (
                    "Kubernetes events show "
                    "'Error: ImagePullBackOff'."
                ),
            ],
            root_cause=(
                "The Pod is unavailable because Kubernetes "
                "cannot pull the configured container image "
                "'nginx:this-image-does-not-exist', as directly "
                "reported by the ErrImagePull, ImagePullBackOff, "
                "and BackOff events."
            ),
            hypotheses=[],
            recommended_next_steps=[
                (
                    "Verify that the configured image name and tag "
                    "'nginx:this-image-does-not-exist' are correct."
                ),
                (
                    "Verify that the image exists in the intended "
                    "container registry."
                ),
            ],
            investigation=InvestigationMetadata(
                tools_used=[
                    "get_resource_summary",
                    "get_resource_events",
                ],
                evidence_summary=[
                    (
                        "Pod demo-api-7d66957847-k27s7 is in "
                        "Pending phase and not Ready."
                    ),
                    (
                        "Kubernetes events indicate "
                        "ErrImagePull, ImagePullBackOff, and "
                        "Back-off pulling image "
                        "'nginx:this-image-does-not-exist'."
                    ),
                ],
            ),
        )

        result = InvestigationEvaluator.evaluate(
            case,
            response,
        )

        self.assertTrue(
            result.passed,
            msg=result.failures,
        )