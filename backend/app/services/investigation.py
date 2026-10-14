from typing import Any

from app.tools.kubernetes import KubernetesInvestigator
from app.tools.prometheus import PrometheusInvestigator

from app.services.evidence import EvidenceBuilder

from app.tools.pod_configuration import get_pod_configuration


class KubernetesInvestigationService:

    def __init__(self):
        self.kubernetes = KubernetesInvestigator()
        self.prometheus = PrometheusInvestigator()
        self.evidence_builder = EvidenceBuilder()

    def investigate_namespace(
        self,
        namespace: str,
    ):

        kubernetes_data = {
            "pods": self.kubernetes.get_pods(namespace),
            "deployments": self.kubernetes.get_deployments(namespace),
            "services": self.kubernetes.get_services(namespace),
            "events": self.kubernetes.get_events(namespace),
        }

        metrics_data = {
            "pod_info": self.prometheus.get_pod_info(namespace),
            "pod_restarts": self.prometheus.get_pod_restarts(namespace),
            "pod_readiness": self.prometheus.get_pod_readiness(namespace),
            "pod_memory": self.prometheus.get_pod_memory_usage(namespace),
            "pod_cpu": self.prometheus.get_pod_cpu_usage(namespace),
        }

        evidence = self.evidence_builder.build(
            kubernetes_data,
            metrics_data,
        )

        return {
            "namespace": namespace,
            "evidence": evidence,
        }

    def get_resource_summary(
        self,
        resource_type: str,
        name: str,
        namespace: str | None = None,
    ) -> dict[str, Any]:

        return self.kubernetes.get_resource_summary(
            resource_type=resource_type,
            name=name,
            namespace=namespace,
        )

    def get_pod_configuration(
        self,
        namespace: str,
        pod_name: str,
    ) -> dict[str, Any]:

        return get_pod_configuration(
            namespace=namespace,
            pod_name=pod_name,
        )

    def get_resource_events(
        self,
        resource_type: str,
        name: str,
        namespace: str | None = None,
    ) -> list[dict[str, Any]]:

        return self.kubernetes.get_resource_events(
            resource_type=resource_type,
            name=name,
            namespace=namespace,
        )

    def get_resource_relationships(
        self,
        resource_type: str,
        name: str,
        namespace: str | None = None,
    ) -> dict[str, Any]:

        return self.kubernetes.get_resource_relationships(
            resource_type=resource_type,
            name=name,
            namespace=namespace,
        )

    def get_pod_metrics(
        self,
        namespace: str,
        pod_name: str,
    ) -> dict[str, Any]:

        return self.prometheus.get_pod_metrics(
            namespace=namespace,
            pod_name=pod_name,
        )

    def get_container_logs(
        self,
        namespace: str,
        pod_name: str,
        container_name: str,
        previous: bool = False,
        tail_lines: int = 100,
    ) -> str:

        return self.kubernetes.get_container_logs(
            namespace=namespace,
            pod_name=pod_name,
            container_name=container_name,
            previous=previous,
            tail_lines=tail_lines,
        )

    def get_pod_container_status(
        self,
        namespace: str,
        pod_name: str,
    ) -> dict[str, Any]:

        return self.kubernetes.get_pod_container_status(
            namespace=namespace,
            pod_name=pod_name,
        )

    def investigate_workload(
        self,
        namespace: str,
        workload: str,
    ):

        return self.investigate_resource(
            resource_type="deployment",
            name=workload,
            namespace=namespace,
        )

    def investigate_resource(
        self,
        resource_type: str,
        name: str,
        namespace: str | None = None,
    ) -> dict[str, Any]:

        result = self.kubernetes.investigate_resource(
            resource_type=resource_type,
            name=name,
            namespace=namespace,
        )

        if not namespace:
            return self.evidence_builder.build_resource_evidence(
                result
            )

        pod_names = self._get_related_pod_names(
            result
        )

        if pod_names:
            result["metrics"] = {
                "pod_restarts": (
                    self.prometheus.get_pod_restarts_for_pods(
                        namespace,
                        pod_names,
                    )
                ),
                "pod_readiness": (
                    self.prometheus.get_pod_readiness_for_pods(
                        namespace,
                        pod_names,
                    )
                ),
                "pod_memory": (
                    self.prometheus.get_pod_memory_for_pods(
                        namespace,
                        pod_names,
                    )
                ),
                "pod_cpu": (
                    self.prometheus.get_pod_cpu_for_pods(
                        namespace,
                        pod_names,
                    )
                ),
            }

        return self.evidence_builder.build_resource_evidence(
            result
        )

    @staticmethod
    def _get_related_pod_names(
        investigation_result: dict[str, Any],
    ) -> list[str]:

        relationships = investigation_result.get(
            "relationships",
            {},
        )

        pods = relationships.get(
            "pods",
            [],
        )

        return [
            pod["name"]
            for pod in pods
            if pod.get("name")
        ]