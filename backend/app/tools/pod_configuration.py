from kubernetes import client, config


class PodConfigurationTool:
    """
    Read-only Kubernetes Pod configuration inspection.

    This tool focuses on configuration that is useful during
    troubleshooting, especially probes, resources, images,
    commands, arguments, and ports.
    """

    def __init__(self):
        try:
            config.load_kube_config()
        except Exception:
            config.load_incluster_config()

        self.core_api = client.CoreV1Api()

    def get_pod_configuration(
        self,
        namespace: str,
        pod_name: str,
    ) -> dict:
        """
        Return relevant configuration for all containers
        in a Pod.

        This is strictly read-only.
        """

        pod = self.core_api.read_namespaced_pod(
            name=pod_name,
            namespace=namespace,
        )

        containers = []

        for container in pod.spec.containers or []:
            containers.append(
                {
                    "name": container.name,
                    "image": container.image,
                    "ports": self._get_ports(container),
                    "command": container.command or [],
                    "args": container.args or [],
                    "resources": self._get_resources(
                        container.resources
                    ),
                    "readiness_probe": self._get_probe(
                        container.readiness_probe
                    ),
                    "liveness_probe": self._get_probe(
                        container.liveness_probe
                    ),
                    "startup_probe": self._get_probe(
                        container.startup_probe
                    ),
                }
            )

        return {
            "pod": pod_name,
            "namespace": namespace,
            "containers": containers,
        }

    @staticmethod
    def _get_ports(container) -> list[dict]:
        ports = []

        for port in container.ports or []:
            ports.append(
                {
                    "name": port.name,
                    "container_port": port.container_port,
                    "protocol": port.protocol,
                    "host_port": port.host_port,
                }
            )

        return ports

    @staticmethod
    def _get_resources(resources) -> dict:
        if resources is None:
            return {
                "requests": {},
                "limits": {},
            }

        return {
            "requests": resources.requests or {},
            "limits": resources.limits or {},
        }

    @staticmethod
    def _get_probe(probe) -> dict | None:
        if probe is None:
            return None

        result = {
            "initial_delay_seconds": probe.initial_delay_seconds,
            "timeout_seconds": probe.timeout_seconds,
            "period_seconds": probe.period_seconds,
            "success_threshold": probe.success_threshold,
            "failure_threshold": probe.failure_threshold,
        }

        if probe.http_get:
            result["http_get"] = {
                "path": probe.http_get.path,
                "port": probe.http_get.port,
                "host": probe.http_get.host,
                "scheme": probe.http_get.scheme,
                "http_headers": [
                    {
                        "name": header.name,
                        "value": header.value,
                    }
                    for header in probe.http_get.http_headers or []
                ],
            }

        if probe.tcp_socket:
            result["tcp_socket"] = {
                "port": probe.tcp_socket.port,
                "host": probe.tcp_socket.host,
            }

        if probe.exec:
            result["exec"] = {
                "command": probe.exec.command or [],
            }

        if probe.grpc:
            result["grpc"] = {
                "port": probe.grpc.port,
                "service": probe.grpc.service,
            }

        return result


pod_configuration_tool = PodConfigurationTool()


def get_pod_configuration(
    namespace: str,
    pod_name: str,
) -> dict:
    """
    Read-only wrapper used by the AI agent.
    """

    return pod_configuration_tool.get_pod_configuration(
        namespace=namespace,
        pod_name=pod_name,
    )