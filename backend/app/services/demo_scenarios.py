from kubernetes import client, config


class DemoScenarioService:
    """
    Creates controlled Kubernetes failure scenarios for
    demonstrations and local testing.

    This service is intentionally separate from the AI
    troubleshooting agent.

    The troubleshooting agent remains strictly read-only.
    """

    NAMESPACE = "aiops-demo"

    def __init__(self):
        try:
            config.load_kube_config()
        except Exception:
            config.load_incluster_config()

        self.core_api = client.CoreV1Api()

    def list_scenarios(self) -> list[dict]:
        return [
            {
                "id": "image-pull",
                "name": "Image Pull Failure",
                "description": (
                    "Pod cannot start because the configured "
                    "container image cannot be pulled."
                ),
                "resource_type": "Pod",
                "resource_name": "demo-image-pull",
                "question": "Why is this pod failing to start?",
            },
            {
                "id": "crash-loop",
                "name": "CrashLoopBackOff",
                "description": (
                    "Container repeatedly exits with a non-zero "
                    "exit code."
                ),
                "resource_type": "Pod",
                "resource_name": "demo-crashloop",
                "question": (
                    "Why is this pod repeatedly restarting?"
                ),
            },
            {
                "id": "pending",
                "name": "Pending Pod",
                "description": (
                    "Pod cannot be scheduled because its resource "
                    "requirements cannot be satisfied."
                ),
                "resource_type": "Pod",
                "resource_name": "demo-pending",
                "question": (
                    "Why is this pod stuck in Pending?"
                ),
            },
            {
                "id": "oom-killed",
                "name": "OOMKilled",
                "description": (
                    "Container exceeds its memory limit and is "
                    "terminated by Kubernetes."
                ),
                "resource_type": "Pod",
                "resource_name": "demo-oom",
                "question": (
                    "Why is this container being terminated?"
                ),
            },
            {
                "id": "readiness",
                "name": "Readiness Probe Failure",
                "description": (
                    "The container is running but the readiness "
                    "probe continuously fails."
                ),
                "resource_type": "Pod",
                "resource_name": "demo-readiness",
                "question": (
                    "Why is this pod running but not Ready?"
                ),
            },
            {
                "id": "liveness",
                "name": "Liveness Probe Failure",
                "description": (
                    "The liveness probe fails and Kubernetes "
                    "restarts the container."
                ),
                "resource_type": "Pod",
                "resource_name": "demo-liveness",
                "question": (
                    "Why is this pod repeatedly restarting?"
                ),
            },
            {
                "id": "service-selector",
                "name": "Service Selector Mismatch",
                "description": (
                    "The Service selector does not match the "
                    "available application Pods."
                ),
                "resource_type": "Service",
                "resource_name": "demo-broken-service",
                "question": (
                    "Why is this Service not routing traffic?"
                ),
            },
            {
                "id": "cpu-pressure",
                "name": "High CPU Usage",
                "description": (
                    "A container continuously consumes CPU and "
                    "approaches its configured CPU limit."
                ),
                "resource_type": "Pod",
                "resource_name": "demo-cpu",
                "question": (
                    "Why is this pod consuming high CPU?"
                ),
            },
        ]

    def prepare_scenario(
        self,
        scenario_id: str,
    ) -> dict:
        scenarios = {
            scenario["id"]: scenario
            for scenario in self.list_scenarios()
        }

        scenario = scenarios.get(scenario_id)

        if scenario is None:
            raise ValueError(
                f"Unknown scenario: {scenario_id}"
            )

        if scenario_id == "image-pull":
            self._create_image_pull_failure()

        elif scenario_id == "crash-loop":
            self._create_crash_loop()

        elif scenario_id == "pending":
            self._create_pending_pod()

        elif scenario_id == "oom-killed":
            self._create_oom_pod()

        elif scenario_id == "readiness":
            self._create_readiness_failure()

        elif scenario_id == "liveness":
            self._create_liveness_failure()

        elif scenario_id == "service-selector":
            self._create_service_selector_failure()

        elif scenario_id == "cpu-pressure":
            self._create_cpu_pressure()

        return {
            **scenario,
            "namespace": self.NAMESPACE,
            "status": "prepared",
        }

    def _delete_pod_if_exists(
        self,
        name: str,
    ) -> None:
        try:
            self.core_api.delete_namespaced_pod(
                name=name,
                namespace=self.NAMESPACE,
                body=client.V1DeleteOptions(),
            )
        except client.exceptions.ApiException as exc:
            if exc.status != 404:
                raise

    def _delete_service_if_exists(
        self,
        name: str,
    ) -> None:
        try:
            self.core_api.delete_namespaced_service(
                name=name,
                namespace=self.NAMESPACE,
                body=client.V1DeleteOptions(),
            )
        except client.exceptions.ApiException as exc:
            if exc.status != 404:
                raise

    def _create_pod(
        self,
        pod: client.V1Pod,
    ) -> None:
        self._delete_pod_if_exists(
            pod.metadata.name
        )

        self.core_api.create_namespaced_pod(
            namespace=self.NAMESPACE,
            body=pod,
        )

    def _create_image_pull_failure(self) -> None:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name="demo-image-pull",
                labels={
                    "app": "demo-image-pull"
                },
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="demo",
                        image=(
                            "nginx:"
                            "this-image-does-not-exist"
                        ),
                    )
                ],
            ),
        )

        self._create_pod(pod)

    def _create_crash_loop(self) -> None:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name="demo-crashloop",
                labels={
                    "app": "demo-crashloop"
                },
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="demo",
                        image="busybox:1.36",
                        command=[
                            "sh",
                            "-c",
                            (
                                "echo 'Database connection "
                                "failed'; exit 1"
                            ),
                        ],
                    )
                ],
            ),
        )

        self._create_pod(pod)

    def _create_pending_pod(self) -> None:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name="demo-pending",
                labels={
                    "app": "demo-pending"
                },
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="demo",
                        image="nginx:1.27-alpine",
                        resources=client.V1ResourceRequirements(
                            requests={
                                "cpu": "100"
                            }
                        ),
                    )
                ],
            ),
        )

        self._create_pod(pod)

    def _create_oom_pod(self) -> None:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name="demo-oom",
                labels={
                    "app": "demo-oom"
                },
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="demo",
                        image="python:3.12-alpine",
                        command=[
                            "python",
                            "-c",
                            (
                                "x=[]; "
                                "while True: "
                                "x.append('x' * 1024 * 1024)"
                            ),
                        ],
                        resources=client.V1ResourceRequirements(
                            requests={
                                "memory": "16Mi"
                            },
                            limits={
                                "memory": "32Mi"
                            },
                        ),
                    )
                ],
            ),
        )

        self._create_pod(pod)

    def _create_readiness_failure(self) -> None:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name="demo-readiness",
                labels={
                    "app": "demo-readiness"
                },
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="demo",
                        image="nginx:1.27-alpine",
                        readiness_probe=client.V1Probe(
                            http_get=client.V1HTTPGetAction(
                                path="/does-not-exist",
                                port=80,
                            ),
                            initial_delay_seconds=2,
                            period_seconds=5,
                        ),
                    )
                ],
            ),
        )

        self._create_pod(pod)

    def _create_liveness_failure(self) -> None:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name="demo-liveness",
                labels={
                    "app": "demo-liveness"
                },
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="demo",
                        image="nginx:1.27-alpine",
                        liveness_probe=client.V1Probe(
                            http_get=client.V1HTTPGetAction(
                                path="/does-not-exist",
                                port=80,
                            ),
                            initial_delay_seconds=2,
                            period_seconds=5,
                        ),
                    )
                ],
            ),
        )

        self._create_pod(pod)

    def _create_service_selector_failure(self) -> None:
        self._delete_service_if_exists(
            "demo-broken-service"
        )

        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name="demo-broken-service"
            ),
            spec=client.V1ServiceSpec(
                selector={
                    "app": "does-not-exist"
                },
                ports=[
                    client.V1ServicePort(
                        port=80,
                        target_port=80,
                    )
                ],
            ),
        )

        self.core_api.create_namespaced_service(
            namespace=self.NAMESPACE,
            body=service,
        )

    def _create_cpu_pressure(self) -> None:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name="demo-cpu",
                labels={
                    "app": "demo-cpu"
                },
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="demo",
                        image="busybox:1.36",
                        command=[
                            "sh",
                            "-c",
                            "while true; do :; done",
                        ],
                        resources=client.V1ResourceRequirements(
                            requests={
                                "cpu": "100m"
                            },
                            limits={
                                "cpu": "500m"
                            },
                        ),
                    )
                ],
            ),
        )

        self._create_pod(pod)


demo_scenario_service = DemoScenarioService()