from kubernetes import client, config


class KubernetesInvestigator:
    """Read-only Kubernetes investigation tools."""

    def __init__(self):
        config.load_kube_config()

        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()
        self.batch_api = client.BatchV1Api()

    def get_pods(self, namespace: str):
        pods = self.core_api.list_namespaced_pod(namespace)

        return [
            {
                "name": pod.metadata.name,
                "phase": pod.status.phase,
                "ready": self._pod_ready(pod),
                "restarts": self._restart_count(pod),
                "labels": pod.metadata.labels or {},
                "node": pod.spec.node_name,
            }
            for pod in pods.items
        ]

    def get_deployments(self, namespace: str):
        deployments = self.apps_api.list_namespaced_deployment(namespace)

        return [
            {
                "name": deployment.metadata.name,
                "desired_replicas": deployment.spec.replicas,
                "available_replicas": (
                    deployment.status.available_replicas or 0
                ),
                "ready_replicas": (
                    deployment.status.ready_replicas or 0
                ),
                "selector": (
                    deployment.spec.selector.match_labels
                    if deployment.spec.selector
                    else {}
                ),
            }
            for deployment in deployments.items
        ]

    def get_events(self, namespace: str):
        events = self.core_api.list_namespaced_event(namespace)

        return [
            {
                "reason": event.reason,
                "message": event.message,
                "type": event.type,
                "object": event.involved_object.name,
                "kind": event.involved_object.kind,
                "timestamp": (
                    event.last_timestamp.isoformat()
                    if event.last_timestamp
                    else None
                ),
            }
            for event in events.items
        ]

    def get_resource_events(
        self,
        resource_type: str,
        name: str,
        namespace: str | None = None,
    ):
        if not namespace:
            raise ValueError(
                "Namespace is required when retrieving resource events"
            )

        events = self.core_api.list_namespaced_event(
            namespace
        )

        return [
            {
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "object": event.involved_object.name,
                "kind": event.involved_object.kind,
                "timestamp": (
                    event.last_timestamp.isoformat()
                    if event.last_timestamp
                    else None
                ),
            }
            for event in events.items
            if (
                event.involved_object.name == name
                and (
                    not resource_type
                    or event.involved_object.kind.lower()
                    == resource_type.lower()
                )
            )
        ]

    def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
    ):
        return self.core_api.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=100,
        )

    def get_container_logs(
        self,
        namespace: str,
        pod_name: str,
        container_name: str,
        previous: bool = False,
        tail_lines: int = 100,
    ):
        """
        Return logs for a specific container in a Pod.

        This is a read-only evidence collection operation.
        """

        return self.core_api.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            previous=previous,
            tail_lines=tail_lines,
        )

    def get_pod_container_status(
        self,
        namespace: str,
        pod_name: str,
    ):
        """
        Return focused status information for every container
        in a Pod.

        This is a read-only evidence collection operation.
        """

        pod = self.core_api.read_namespaced_pod(
            name=pod_name,
            namespace=namespace,
        )

        container_statuses = (
            pod.status.container_statuses or []
        )

        results = []

        for status in container_statuses:
            current_state = status.state
            last_state = status.last_state

            current_state_name = None
            current_state_reason = None
            current_state_message = None

            if current_state:
                if current_state.running:
                    current_state_name = "running"
                    current_state_reason = None
                    current_state_message = (
                        getattr(
                            current_state.running,
                            "message",
                            None,
                        )
                    )

                elif current_state.waiting:
                    current_state_name = "waiting"
                    current_state_reason = (
                        current_state.waiting.reason
                    )
                    current_state_message = (
                        current_state.waiting.message
                    )

                elif current_state.terminated:
                    current_state_name = "terminated"
                    current_state_reason = (
                        current_state.terminated.reason
                    )
                    current_state_message = (
                        current_state.terminated.message
                    )

            last_state_name = None
            last_state_reason = None
            last_state_message = None
            last_exit_code = None
            last_signal = None

            if last_state:
                if last_state.running:
                    last_state_name = "running"
                    last_state_message = (
                        getattr(
                            last_state.running,
                            "message",
                            None,
                        )
                    )

                elif last_state.waiting:
                    last_state_name = "waiting"
                    last_state_reason = (
                        last_state.waiting.reason
                    )
                    last_state_message = (
                        last_state.waiting.message
                    )

                elif last_state.terminated:
                    last_state_name = "terminated"
                    last_state_reason = (
                        last_state.terminated.reason
                    )
                    last_state_message = (
                        last_state.terminated.message
                    )
                    last_exit_code = (
                        last_state.terminated.exit_code
                    )
                    last_signal = (
                        last_state.terminated.signal
                    )

            results.append(
                {
                    "name": status.name,
                    "ready": status.ready,
                    "restart_count": status.restart_count,
                    "current_state": current_state_name,
                    "current_reason": current_state_reason,
                    "current_message": current_state_message,
                    "last_state": last_state_name,
                    "last_reason": last_state_reason,
                    "last_message": last_state_message,
                    "last_exit_code": last_exit_code,
                    "last_signal": last_signal,
                }
            )

        return {
            "pod": pod_name,
            "namespace": namespace,
            "containers": results,
        }

    def get_services(self, namespace: str):
        services = self.core_api.list_namespaced_service(namespace)

        return [
            {
                "name": service.metadata.name,
                "type": service.spec.type,
                "cluster_ip": service.spec.cluster_ip,
                "selector": service.spec.selector or {},
                "ports": [
                    {
                        "port": port.port,
                        "target_port": str(port.target_port),
                        "protocol": port.protocol,
                    }
                    for port in service.spec.ports
                ],
            }
            for service in services.items
        ]

    def get_pod_details(self, namespace: str, pod_name: str):
        pod = self.core_api.read_namespaced_pod(
            name=pod_name,
            namespace=namespace,
        )

        containers = []

        for container in pod.spec.containers:
            containers.append(
                {
                    "name": container.name,
                    "image": container.image,
                    "ports": [
                        port.container_port
                        for port in (container.ports or [])
                    ],
                    "resources": (
                        container.resources.to_dict()
                        if container.resources
                        else {}
                    ),
                }
            )

        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "node": pod.spec.node_name,
            "phase": pod.status.phase,
            "labels": pod.metadata.labels or {},
            "owner_references": [
                {
                    "kind": owner.kind,
                    "name": owner.name,
                    "uid": owner.uid,
                }
                for owner in (pod.metadata.owner_references or [])
            ],
            "containers": containers,
        }

    def investigate_pod(self, namespace: str, pod_name: str):
        pod_details = self.get_pod_details(
            namespace,
            pod_name,
        )

        events = self.get_events(namespace)

        pod_events = [
            event
            for event in events
            if event["object"] == pod_name
        ]

        try:
            logs = self.get_pod_logs(
                namespace,
                pod_name,
            )
        except Exception as exc:
            logs = f"Unable to retrieve logs: {exc}"

        return {
            "pod": pod_details,
            "events": pod_events,
            "logs": logs,
        }

    def get_related_replicasets(
        self,
        namespace: str,
        deployment_name: str,
    ):
        replicasets = (
            self.apps_api.list_namespaced_replica_set(namespace)
        )

        related = []

        for replicaset in replicasets.items:
            owner_references = (
                replicaset.metadata.owner_references or []
            )

            is_owned_by_deployment = any(
                owner.kind == "Deployment"
                and owner.name == deployment_name
                for owner in owner_references
            )

            if not is_owned_by_deployment:
                continue

            related.append(
                {
                    "name": replicaset.metadata.name,
                    "desired_replicas": (
                        replicaset.spec.replicas or 0
                    ),
                    "ready_replicas": (
                        replicaset.status.ready_replicas or 0
                    ),
                    "available_replicas": (
                        replicaset.status.available_replicas or 0
                    ),
                    "labels": replicaset.metadata.labels or {},
                }
            )

        return related

    def get_pods_for_selector(
        self,
        namespace: str,
        selector: dict,
    ):
        if not selector:
            return []

        label_selector = ",".join(
            f"{key}={value}"
            for key, value in selector.items()
        )

        pods = self.core_api.list_namespaced_pod(
            namespace,
            label_selector=label_selector,
        )

        return [
            {
                "name": pod.metadata.name,
                "phase": pod.status.phase,
                "ready": self._pod_ready(pod),
                "restarts": self._restart_count(pod),
                "labels": pod.metadata.labels or {},
                "node": pod.spec.node_name,
            }
            for pod in pods.items
        ]

    def get_resource_relationships(
        self,
        resource_type: str,
        name: str,
        namespace: str | None = None,
    ):
        resource_type = resource_type.lower()

        if not namespace:
            raise ValueError(
                "Namespace is required for resource relationships"
            )

        if resource_type == "deployment":
            deployment = (
                self.apps_api.read_namespaced_deployment(
                    name=name,
                    namespace=namespace,
                )
            )

            selector = (
                deployment.spec.selector.match_labels
                if deployment.spec.selector
                else {}
            )

            replicasets = self.get_related_replicasets(
                namespace,
                name,
            )

            pods = self.get_pods_for_selector(
                namespace,
                selector,
            )

            return {
                "resource_type": "deployment",
                "name": name,
                "namespace": namespace,
                "relationships": {
                    "replicasets": replicasets,
                    "pods": pods,
                },
            }

        if resource_type == "service":
            service = (
                self.core_api.read_namespaced_service(
                    name=name,
                    namespace=namespace,
                )
            )

            selector = service.spec.selector or {}

            pods = self.get_pods_for_selector(
                namespace,
                selector,
            )

            return {
                "resource_type": "service",
                "name": name,
                "namespace": namespace,
                "relationships": {
                    "selector": selector,
                    "pods": pods,
                },
            }

        raise ValueError(
            f"Relationships are not supported for resource type: "
            f"{resource_type}"
        )

    def get_resource_summary(
        self,
        resource_type: str,
        name: str,
        namespace: str | None = None,
    ):
        resource_type = resource_type.lower()

        if resource_type == "pod":
            if not namespace:
                raise ValueError(
                    "Namespace is required for pod"
                )

            resource = self.core_api.read_namespaced_pod(
                name=name,
                namespace=namespace,
            )

            return {
                "resource_type": "pod",
                "name": name,
                "namespace": namespace,
                "phase": resource.status.phase,
                "ready": self._pod_ready(resource),
                "restarts": self._restart_count(resource),
            }

        if resource_type == "deployment":
            if not namespace:
                raise ValueError(
                    "Namespace is required for deployment"
                )

            resource = (
                self.apps_api.read_namespaced_deployment(
                    name=name,
                    namespace=namespace,
                )
            )

            status = resource.status
            spec = resource.spec

            return {
                "resource_type": "deployment",
                "name": name,
                "namespace": namespace,
                "desired_replicas": spec.replicas or 0,
                "current_replicas": status.replicas or 0,
                "updated_replicas": (
                    status.updated_replicas or 0
                ),
                "ready_replicas": (
                    status.ready_replicas or 0
                ),
                "available_replicas": (
                    status.available_replicas or 0
                ),
                "unavailable_replicas": (
                    status.unavailable_replicas or 0
                ),
            }

        if resource_type == "service":
            if not namespace:
                raise ValueError(
                    "Namespace is required for service"
                )

            resource = (
                self.core_api.read_namespaced_service(
                    name=name,
                    namespace=namespace,
                )
            )

            return {
                "resource_type": "service",
                "name": name,
                "namespace": namespace,
                "type": resource.spec.type,
                "selector": (
                    resource.spec.selector or {}
                ),
            }

        if resource_type == "node":
            resource = self.core_api.read_node(
                name=name,
            )

            conditions = resource.status.conditions or []

            ready_condition = next(
                (
                    condition
                    for condition in conditions
                    if condition.type == "Ready"
                ),
                None,
            )

            return {
                "resource_type": "node",
                "name": name,
                "ready": (
                    ready_condition.status == "True"
                    if ready_condition
                    else False
                ),
            }

        raise ValueError(
            f"Unsupported resource type: {resource_type}"
        )

    def investigate_resource(
        self,
        resource_type: str,
        name: str,
        namespace: str | None = None,
    ):
        resource_type = resource_type.lower()

        supported_namespaced_resources = {
            "pod",
            "deployment",
            "service",
            "replicaset",
            "statefulset",
            "daemonset",
            "job",
            "cronjob",
        }

        supported_cluster_resources = {
            "node",
        }

        supported_resources = (
            supported_namespaced_resources
            | supported_cluster_resources
        )

        if resource_type not in supported_resources:
            raise ValueError(
                f"Unsupported resource type: {resource_type}"
            )

        if (
            resource_type in supported_namespaced_resources
            and not namespace
        ):
            raise ValueError(
                f"Namespace is required for resource type: {resource_type}"
            )

        if resource_type == "pod":
            resource = self.core_api.read_namespaced_pod(
                name=name,
                namespace=namespace,
            )

        elif resource_type == "service":
            resource = self.core_api.read_namespaced_service(
                name=name,
                namespace=namespace,
            )

        elif resource_type == "deployment":
            resource = self.apps_api.read_namespaced_deployment(
                name=name,
                namespace=namespace,
            )

        elif resource_type == "replicaset":
            resource = self.apps_api.read_namespaced_replica_set(
                name=name,
                namespace=namespace,
            )

        elif resource_type == "statefulset":
            resource = self.apps_api.read_namespaced_stateful_set(
                name=name,
                namespace=namespace,
            )

        elif resource_type == "daemonset":
            resource = self.apps_api.read_namespaced_daemon_set(
                name=name,
                namespace=namespace,
            )

        elif resource_type == "job":
            resource = self.batch_api.read_namespaced_job(
                name=name,
                namespace=namespace,
            )

        elif resource_type == "cronjob":
            resource = self.batch_api.read_namespaced_cron_job(
                name=name,
                namespace=namespace,
            )

        elif resource_type == "node":
            resource = self.core_api.read_node(
                name=name,
            )

        result = {
            "resource_type": resource_type,
            "name": name,
            "namespace": namespace,
            "resource": self._make_json_serializable(
                resource.to_dict()
            ),
        }

        if namespace:
            events = self.get_events(namespace)

            result["events"] = [
                event
                for event in events
                if event["object"] == name
            ]

        if resource_type == "pod":
            try:
                result["logs"] = self.get_pod_logs(
                    namespace,
                    name,
                )
            except Exception as exc:
                result["logs"] = (
                    f"Unable to retrieve logs: {exc}"
                )

        elif resource_type == "deployment":
            deployment = resource

            selector = (
                deployment.spec.selector.match_labels
                if deployment.spec.selector
                else {}
            )

            result["relationships"] = {
                "replicasets": self.get_related_replicasets(
                    namespace,
                    name,
                ),
                "pods": self.get_pods_for_selector(
                    namespace,
                    selector,
                ),
            }

            result["pod_logs"] = {}

            pods = result["relationships"]["pods"]

            for pod in pods:
                pod_name = pod["name"]

                try:
                    result["pod_logs"][pod_name] = (
                        self.get_pod_logs(
                            namespace,
                            pod_name,
                        )
                    )
                except Exception as exc:
                    result["pod_logs"][pod_name] = (
                        f"Unable to retrieve logs: {exc}"
                    )

        elif resource_type == "service":
            service = resource

            selector = service.spec.selector or {}

            result["relationships"] = {
                "selector": selector,
                "pods": self.get_pods_for_selector(
                    namespace,
                    selector,
                ),
            }

        return self._make_json_serializable(result)

    @staticmethod
    def _pod_ready(pod):
        if not pod.status.container_statuses:
            return False

        return all(
            container.ready
            for container in pod.status.container_statuses
        )

    @staticmethod
    def _restart_count(pod):
        if not pod.status.container_statuses:
            return 0

        return sum(
            container.restart_count
            for container in pod.status.container_statuses
        )

    @staticmethod
    def _make_json_serializable(value):
        if isinstance(value, dict):
            return {
                key: KubernetesInvestigator._make_json_serializable(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                KubernetesInvestigator._make_json_serializable(item)
                for item in value
            ]

        if hasattr(value, "isoformat"):
            return value.isoformat()

        return value
