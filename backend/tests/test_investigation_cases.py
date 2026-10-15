import unittest


INVESTIGATION_CASES = [
    {
        "name": "healthy_deployment",
        "description": "Deployment is healthy and all replicas are available.",
        "resource_type": "Deployment",
        "expected_status": "Healthy",
        "expected_severity": "Low",
        "required_evidence": [
            "desired replicas",
            "ready replicas",
            "available replicas",
        ],
        "root_cause_keywords": [],
    },
    {
        "name": "image_pull_failure",
        "description": "Pod cannot pull the configured container image.",
        "resource_type": "Pod",
        "expected_status": "Failed",
        "expected_severity": "High",
        "required_evidence": [
            "ErrImagePull",
            "ImagePullBackOff",
        ],
        "root_cause_keywords": [
            "image",
            "pull",
        ],
    },
    {
        "name": "crash_loop_backoff",
        "description": "Container repeatedly starts and terminates with a non-zero exit.",
        "resource_type": "Pod",
        "expected_status": "Failed",
        "expected_severity": None,
        "required_evidence": [
            "CrashLoopBackOff",
            "container termination",
        ],
        "root_cause_keywords": [
            "container",
            "terminate",
        ],
    },
    {
        "name": "oom_killed",
        "description": "Container is terminated after exceeding its memory limit.",
        "resource_type": "Pod",
        "expected_status": "Failed",
        "expected_severity": None,
        "required_evidence": [
            "OOMKilled",
            "memory",
        ],
        "root_cause_keywords": [
            "memory",
        ],
    },
    {
        "name": "readiness_failure",
        "description": "Pod is running but fails its readiness probe.",
        "resource_type": "Pod",
        "expected_status": "Failed",
        "expected_severity": None,
        "required_evidence": [
            "readiness",
            "NotReady",
        ],
        "root_cause_keywords": [
            "readiness",
            "probe",
        ],
    },
    {
        "name": "liveness_failure",
        "description": "Kubernetes terminates the container after repeated liveness probe failures.",
        "resource_type": "Pod",
        "expected_status": "Failed",
        "expected_severity": None,
        "required_evidence": [
            "liveness",
            "container termination",
        ],
        "root_cause_keywords": [
            "liveness",
            "probe",
        ],
    },
    {
        "name": "pending_pod",
        "description": "Pod cannot be scheduled because its resource requirements cannot be satisfied.",
        "resource_type": "Pod",
        "expected_status": "Failed",
        "expected_severity": None,
        "required_evidence": [
            "Pending",
            "scheduling",
        ],
        "root_cause_keywords": [
            "schedule",
        ],
    },
    {
        "name": "service_selector_mismatch",
        "description": "Service selector does not match the intended application Pods.",
        "resource_type": "Service",
        "expected_status": "Failed",
        "expected_severity": None,
        "required_evidence": [
            "selector",
            "endpoints",
        ],
        "root_cause_keywords": [
            "selector",
        ],
    },
    {
        "name": "cpu_pressure",
        "description": "Pod is consuming high CPU without assuming CPU throttling without evidence.",
        "resource_type": "Pod",
        "expected_status": "Degraded",
        "expected_severity": None,
        "required_evidence": [
            "CPU",
            "metrics",
        ],
        "root_cause_keywords": [
            "CPU",
        ],
    },
    {
        "name": "deployment_rollout_failure",
        "description": (
            "Deployment rollout is unhealthy and the failure must be traced "
            "through ReplicaSet ownership to the affected Pod."
        ),
        "resource_type": "Deployment",
        "expected_status": "Failed",
        "expected_severity": "High",
        "required_evidence": [
            "Deployment",
            "ReplicaSet",
            "Pod",
        ],
        "root_cause_keywords": [
            "ReplicaSet",
            "Pod",
        ],
    },
]


class TestInvestigationCaseDefinitions(unittest.TestCase):
    """
    Validate the formal investigation evaluation matrix.

    These tests intentionally validate the test specification itself.
    They do not invoke Gemini or Kubernetes. Live agent evaluation is
    kept separate so the normal unit-test suite remains deterministic.
    """

    def test_expected_number_of_investigation_cases(self):
        self.assertEqual(
            len(INVESTIGATION_CASES),
            10,
        )

    def test_all_cases_have_required_fields(self):
        required_fields = {
            "name",
            "description",
            "resource_type",
            "expected_status",
            "expected_severity",
            "required_evidence",
            "root_cause_keywords",
        }

        for case in INVESTIGATION_CASES:
            with self.subTest(case=case["name"]):
                self.assertTrue(
                    required_fields.issubset(case.keys())
                )

    def test_case_names_are_unique(self):
        names = [
            case["name"]
            for case in INVESTIGATION_CASES
        ]

        self.assertEqual(
            len(names),
            len(set(names)),
        )

    def test_expected_status_values_are_valid(self):
        valid_statuses = {
            "Healthy",
            "Degraded",
            "Failed",
        }

        for case in INVESTIGATION_CASES:
            with self.subTest(case=case["name"]):
                self.assertIn(
                    case["expected_status"],
                    valid_statuses,
                )

    def test_high_severity_cases_are_explicit(self):
        high_severity_cases = {
            case["name"]
            for case in INVESTIGATION_CASES
            if case["expected_severity"] == "High"
        }

        self.assertEqual(
            high_severity_cases,
            {
                "image_pull_failure",
                "deployment_rollout_failure",
            },
        )

    def test_each_case_requires_evidence(self):
        for case in INVESTIGATION_CASES:
            with self.subTest(case=case["name"]):
                self.assertGreater(
                    len(case["required_evidence"]),
                    0,
                )

    def test_deployment_rollout_case_requires_relationship_evidence(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "deployment_rollout_failure"
        )

        self.assertIn(
            "ReplicaSet",
            case["required_evidence"],
        )

        self.assertIn(
            "Pod",
            case["required_evidence"],
        )

    def test_cpu_case_does_not_require_throttling_claim(self):
        case = next(
            case
            for case in INVESTIGATION_CASES
            if case["name"] == "cpu_pressure"
        )

        self.assertNotIn(
            "throttling",
            case["required_evidence"],
        )

    def test_all_cases_use_supported_resource_types(self):
        supported_resource_types = {
            "Deployment",
            "Pod",
            "Service",
        }

        for case in INVESTIGATION_CASES:
            with self.subTest(case=case["name"]):
                self.assertIn(
                    case["resource_type"],
                    supported_resource_types,
                )


if __name__ == "__main__":
    unittest.main()