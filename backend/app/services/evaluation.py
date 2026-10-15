from dataclasses import dataclass

from app.api.models import InvestigationResponse


@dataclass
class EvaluationResult:
    case_name: str
    passed: bool
    checks: dict[str, bool]
    failures: list[str]


class InvestigationEvaluator:
    """
    Deterministic evaluator for Kubernetes investigation responses.

    The evaluator compares a structured InvestigationResponse against
    explicitly defined expectations from the investigation case matrix.

    It does not use an LLM and does not execute Kubernetes operations.
    """

    @staticmethod
    def evaluate(
        case: dict,
        response: InvestigationResponse,
    ) -> EvaluationResult:
        checks: dict[str, bool] = {}
        failures: list[str] = []

        checks["status"] = (
            response.assessment.status
            == case["expected_status"]
        )

        if not checks["status"]:
            failures.append(
                "Expected status "
                f"'{case['expected_status']}', "
                f"got '{response.assessment.status}'."
            )

        expected_severity = case["expected_severity"]

        if expected_severity is None:
            checks["severity"] = True
        else:
            checks["severity"] = (
                response.assessment.severity
                == expected_severity
            )

            if not checks["severity"]:
                failures.append(
                    "Expected severity "
                    f"'{expected_severity}', "
                    f"got '{response.assessment.severity}'."
                )

        response_text = InvestigationEvaluator._response_text(
            response
        )

        for evidence in case["required_evidence"]:
            key = (
                "evidence:"
                + evidence.lower().replace(" ", "_")
            )

            found = evidence.lower() in response_text
            checks[key] = found

            if not found:
                failures.append(
                    "Required evidence not found: "
                    f"'{evidence}'."
                )

        for keyword in case["root_cause_keywords"]:
            key = (
                "root_cause:"
                + keyword.lower().replace(" ", "_")
            )

            found = (
                keyword.lower()
                in response.root_cause.lower()
            )

            checks[key] = found

            if not found:
                failures.append(
                    "Expected root-cause keyword not found: "
                    f"'{keyword}'."
                )

        passed = all(checks.values())

        return EvaluationResult(
            case_name=case["name"],
            passed=passed,
            checks=checks,
            failures=failures,
        )

    @staticmethod
    def _response_text(
        response: InvestigationResponse,
    ) -> str:
        """
        Build searchable evidence text from the structured response.

        This intentionally includes facts, hypotheses,
        root cause, recommended steps, and investigation
        evidence.
        """

        values = [
            response.root_cause,
            *response.facts,
            *response.hypotheses,
            *response.recommended_next_steps,
            *response.investigation.tools_used,
            *response.investigation.evidence_summary,
        ]

        return " ".join(
            value
            for value in values
            if value
        ).lower()