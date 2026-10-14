from typing import Any


class EvidenceBuilder:
    """Convert raw Kubernetes and Prometheus data into AI-friendly evidence."""

    def build(
        self,
        kubernetes_data: dict[str, Any],
        metrics_data: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "pods": self._build_pods(
                kubernetes_data.get("pods", [])
            ),
            "deployments": kubernetes_data.get(
                "deployments",
                [],
            ),
            "services": kubernetes_data.get(
                "services",
                [],
            ),
            "events": self._build_events(
                kubernetes_data.get("events", [])
            ),
            "logs": kubernetes_data.get(
                "logs",
                {},
            ),
            "metrics": {
                "restarts": self._normalize_metric(
                    metrics_data.get("pod_restarts", [])
                ),
                "readiness": self._normalize_metric(
                    metrics_data.get("pod_readiness", [])
                ),
                "memory": self._normalize_metric(
                    metrics_data.get("pod_memory", [])
                ),
                "cpu": self._normalize_metric(
                    metrics_data.get("pod_cpu", [])
                ),
            },
        }

    def build_resource_evidence(
        self,
        investigation: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert a resource investigation into concise,
        AI-friendly troubleshooting evidence.
        """

        resource_type = investigation.get(
            "resource_type"
        )

        evidence = {
            "resource": {
                "type": resource_type,
                "name": investigation.get("name"),
                "namespace": investigation.get(
                    "namespace"
                ),
            },
            "facts": [],
            "events": investigation.get(
                "events",
                [],
            ),
            "relationships": investigation.get(
                "relationships",
                {},
            ),
            "metrics": investigation.get(
                "metrics",
                {},
            ),
        }

        resource = investigation.get(
            "resource",
            {},
        )

        if resource_type == "deployment":
            evidence["deployment"] = (
                self._build_deployment_evidence(
                    resource
                )
            )

            evidence["facts"].extend(
                self._deployment_facts(
                    evidence["deployment"]
                )
            )

            evidence["facts"].extend(
                self._pod_facts(
                    evidence["relationships"].get(
                        "pods",
                        [],
                    )
                )
            )

        elif resource_type == "pod":
            evidence["pod"] = (
                self._build_pod_evidence(
                    resource
                )
            )

            evidence["facts"].extend(
                self._pod_resource_facts(
                    evidence["pod"]
                )
            )

        elif resource_type == "service":
            evidence["service"] = (
                self._build_service_evidence(
                    resource
                )
            )

            evidence["facts"].extend(
                self._service_facts(
                    evidence["service"]
                )
            )

        return evidence

    @staticmethod
    def _build_deployment_evidence(
        resource: dict[str, Any],
    ) -> dict[str, Any]:

        spec = resource.get("spec", {})
        status = resource.get("status", {})

        template = spec.get(
            "template",
            {},
        )

        pod_spec = template.get(
            "spec",
            {},
        )

        containers = []

        for container in pod_spec.get(
            "containers",
            [],
        ):
            containers.append(
                {
                    "name": container.get("name"),
                    "image": container.get("image"),
                }
            )

        conditions = []

        for condition in status.get(
            "conditions",
            [],
        ):
            conditions.append(
                {
                    "type": condition.get("type"),
                    "status": condition.get("status"),
                    "reason": condition.get("reason"),
                    "message": condition.get("message"),
                }
            )

        return {
            "desired_replicas": spec.get(
                "replicas",
                0,
            ),
            "current_replicas": status.get(
                "replicas",
                0,
            ),
            "updated_replicas": status.get(
                "updated_replicas",
                0,
            ),
            "ready_replicas": status.get(
                "ready_replicas",
                0,
            ),
            "available_replicas": status.get(
                "available_replicas",
                0,
            ),
            "unavailable_replicas": status.get(
                "unavailable_replicas"
            ) or 0,
            "containers": containers,
            "conditions": conditions,
        }

    @staticmethod
    def _build_pod_evidence(
        resource: dict[str, Any],
    ) -> dict[str, Any]:

        status = resource.get(
            "status",
            {}
        )

        spec = resource.get(
            "spec",
            {}
        )

        containers = []

        for container in spec.get(
            "containers",
            [],
        ):
            containers.append(
                {
                    "name": container.get("name"),
                    "image": container.get("image"),
                }
            )

        return {
            "phase": status.get("phase"),
            "containers": containers,
            "conditions": status.get(
                "conditions",
                [],
            ),
            "container_statuses": status.get(
                "container_statuses",
                [],
            ),
        }

    @staticmethod
    def _build_service_evidence(
        resource: dict[str, Any],
    ) -> dict[str, Any]:

        spec = resource.get(
            "spec",
            {}
        )

        return {
            "type": spec.get("type"),
            "cluster_ip": spec.get(
                "cluster_ip"
            ),
            "selector": spec.get(
                "selector",
                {},
            ),
            "ports": spec.get(
                "ports",
                [],
            ),
        }

    @staticmethod
    def _deployment_facts(
        deployment: dict[str, Any],
    ) -> list[str]:

        facts = []

        desired = deployment.get(
            "desired_replicas",
            0,
        )

        ready = deployment.get(
            "ready_replicas",
            0,
        )

        available = deployment.get(
            "available_replicas",
            0,
        )

        unavailable = deployment.get(
            "unavailable_replicas",
            0,
        )

        facts.append(
            f"Deployment has {desired} desired replicas."
        )

        facts.append(
            f"Deployment has {ready} ready replicas."
        )

        facts.append(
            f"Deployment has {available} available replicas."
        )

        if unavailable:
            facts.append(
                f"Deployment has {unavailable} unavailable replicas."
            )

        for container in deployment.get(
            "containers",
            [],
        ):
            facts.append(
                f"Container "
                f"{container.get('name')} "
                f"uses image "
                f"{container.get('image')}."
            )

        for condition in deployment.get(
            "conditions",
            [],
        ):
            message = (
                condition.get("message")
                or ""
            ).rstrip(".")

            facts.append(
                f"Deployment condition "
                f"{condition.get('type')}="
                f"{condition.get('status')}: "
                f"{message}."
            )

        return facts

    @staticmethod
    def _pod_facts(
        pods: list[dict[str, Any]],
    ) -> list[str]:

        facts = []

        for pod in pods:
            facts.append(
                f"Pod {pod.get('name')} is "
                f"{pod.get('phase')} and "
                f"ready={pod.get('ready')}."
            )

            if pod.get("restarts"):
                facts.append(
                    f"Pod {pod.get('name')} has "
                    f"{pod.get('restarts')} restarts."
                )

        return facts

    @staticmethod
    def _pod_resource_facts(
        pod: dict[str, Any],
    ) -> list[str]:

        facts = [
            f"Pod phase is {pod.get('phase')}."
        ]

        for container in pod.get(
            "containers",
            [],
        ):
            facts.append(
                f"Container "
                f"{container.get('name')} "
                f"uses image "
                f"{container.get('image')}."
            )

        return facts

    @staticmethod
    def _service_facts(
        service: dict[str, Any],
    ) -> list[str]:

        return [
            f"Service type is "
            f"{service.get('type')}.",
            f"Service selector is "
            f"{service.get('selector')}.",
        ]

    @staticmethod
    def _build_pods(
        pods: list[dict[str, Any]],
    ):

        return [
            {
                "name": pod.get("name"),
                "phase": pod.get("phase"),
                "ready": pod.get("ready"),
                "restarts": pod.get("restarts"),
            }
            for pod in pods
        ]

    @staticmethod
    def _build_events(
        events: list[dict[str, Any]],
    ):

        return [
            {
                "type": event.get("type"),
                "reason": event.get("reason"),
                "object": event.get("object"),
                "message": event.get("message"),
                "timestamp": event.get("timestamp"),
            }
            for event in events
        ]

    @staticmethod
    def _normalize_metric(
        results: list[dict[str, Any]],
    ):

        normalized = []

        for result in results:
            metric = result.get(
                "metric",
                {}
            )

            value = result.get(
                "value",
                []
            )

            if len(value) < 2:
                continue

            try:
                numeric_value = float(
                    value[1]
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            normalized.append(
                {
                    "pod": metric.get("pod"),
                    "container": metric.get(
                        "container"
                    ),
                    "value": numeric_value,
                }
            )

        return normalized