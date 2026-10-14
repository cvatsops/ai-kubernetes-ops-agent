import requests


class PrometheusInvestigator:
    """Read-only Prometheus investigation tools."""

    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url.rstrip("/")

    def query(self, promql: str):
        response = requests.get(
            f"{self.base_url}/api/v1/query",
            params={"query": promql},
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if data["status"] != "success":
            raise RuntimeError(
                f"Prometheus query failed: {data}"
            )

        return data["data"]["result"]

    def get_pod_restarts(self, namespace: str):
        query = f"""
        kube_pod_container_status_restarts_total{{
            namespace="{namespace}"
        }}
        """

        return self.query(query)

    def get_pod_info(self, namespace: str):
        query = f"""
        kube_pod_info{{
            namespace="{namespace}"
        }}
        """

        return self.query(query)

    def get_pod_readiness(self, namespace: str):
        query = f"""
        kube_pod_container_status_ready{{
            namespace="{namespace}"
        }}
        """

        return self.query(query)

    def get_pod_memory_usage(self, namespace: str):
        query = f"""
        sum by (pod) (
            container_memory_working_set_bytes{{
                namespace="{namespace}",
                container!="",
                container!="POD"
            }}
        )
        """

        return self.query(query)

    def get_pod_cpu_usage(self, namespace: str):
        query = f"""
        sum by (pod) (
            rate(
                container_cpu_usage_seconds_total{{
                    namespace="{namespace}",
                    container!="",
                    container!="POD"
                }}[5m]
            )
        )
        """

        return self.query(query)

    def get_pod_metrics(
        self,
        namespace: str,
        pod_name: str,
    ):
        """
        Return focused Prometheus metrics for a single Pod.

        This is a read-only evidence collection operation.
        """

        pod_selector = f'namespace="{namespace}",pod="{pod_name}"'

        restarts = self.query(
            f"""
            kube_pod_container_status_restarts_total{{
                {pod_selector}
            }}
            """
        )

        readiness = self.query(
            f"""
            kube_pod_container_status_ready{{
                {pod_selector}
            }}
            """
        )

        memory = self.query(
            f"""
            sum(
                container_memory_working_set_bytes{{
                    {pod_selector},
                    container!="",
                    container!="POD"
                }}
            )
            """
        )

        cpu = self.query(
            f"""
            sum(
                rate(
                    container_cpu_usage_seconds_total{{
                        {pod_selector},
                        container!="",
                        container!="POD"
                    }}[5m]
                )
            )
            """
        )

        return {
            "pod": pod_name,
            "namespace": namespace,
            "restarts": self._normalize_metric_results(
                restarts
            ),
            "readiness": self._normalize_metric_results(
                readiness
            ),
            "memory_bytes": self._normalize_scalar_result(
                memory
            ),
            "cpu_cores": self._normalize_scalar_result(
                cpu
            ),
        }

    def get_pod_restarts_for_pods(
        self,
        namespace: str,
        pod_names: list[str],
    ):
        return self._filter_by_pods(
            self.get_pod_restarts(namespace),
            pod_names,
        )

    def get_pod_readiness_for_pods(
        self,
        namespace: str,
        pod_names: list[str],
    ):
        return self._filter_by_pods(
            self.get_pod_readiness(namespace),
            pod_names,
        )

    def get_pod_memory_for_pods(
        self,
        namespace: str,
        pod_names: list[str],
    ):
        return self._filter_by_pods(
            self.get_pod_memory_usage(namespace),
            pod_names,
        )

    def get_pod_cpu_for_pods(
        self,
        namespace: str,
        pod_names: list[str],
    ):
        return self._filter_by_pods(
            self.get_pod_cpu_usage(namespace),
            pod_names,
        )

    @staticmethod
    def _filter_by_pods(
        results: list[dict],
        pod_names: list[str],
    ):
        pod_names_set = set(pod_names)

        return [
            result
            for result in results
            if result.get("metric", {}).get("pod")
            in pod_names_set
        ]

    @staticmethod
    def _normalize_metric_results(
        results: list[dict],
    ):
        normalized = []

        for result in results:
            metric = result.get(
                "metric",
                {},
            )

            value = result.get(
                "value",
                [],
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
                    "container": metric.get(
                        "container"
                    ),
                    "value": numeric_value,
                }
            )

        return normalized

    @staticmethod
    def _normalize_scalar_result(
        results: list[dict],
    ):
        if not results:
            return None

        value = results[0].get(
            "value",
            [],
        )

        if len(value) < 2:
            return None

        try:
            return float(value[1])
        except (
            TypeError,
            ValueError,
        ):
            return None