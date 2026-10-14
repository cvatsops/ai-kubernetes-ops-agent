from app.services.investigation import KubernetesInvestigationService
from app.tools.pod_configuration import get_pod_configuration


investigation_service = KubernetesInvestigationService()


def get_resource_summary(
    resource_type: str,
    name: str,
    namespace: str | None = None,
) -> dict:
    return investigation_service.get_resource_summary(
        resource_type=resource_type,
        name=name,
        namespace=namespace,
    )

def get_pod_configuration(
    namespace: str,
    pod_name: str,
) -> dict:
    return investigation_service.get_pod_configuration(
        namespace=namespace,
        pod_name=pod_name,
    )


def get_resource_events(
    resource_type: str,
    name: str,
    namespace: str | None = None,
) -> list[dict]:
    return investigation_service.get_resource_events(
        resource_type=resource_type,
        name=name,
        namespace=namespace,
    )


def get_resource_relationships(
    resource_type: str,
    name: str,
    namespace: str | None = None,
) -> dict:
    return investigation_service.get_resource_relationships(
        resource_type=resource_type,
        name=name,
        namespace=namespace,
    )


def get_pod_metrics(
    namespace: str,
    pod_name: str,
) -> dict:
    return investigation_service.get_pod_metrics(
        namespace=namespace,
        pod_name=pod_name,
    )


def get_container_logs(
    namespace: str,
    pod_name: str,
    container_name: str,
    previous: bool = False,
    tail_lines: int = 100,
) -> str:
    return investigation_service.get_container_logs(
        namespace=namespace,
        pod_name=pod_name,
        container_name=container_name,
        previous=previous,
        tail_lines=tail_lines,
    )


def get_pod_container_status(
    namespace: str,
    pod_name: str,
) -> dict:
    return investigation_service.get_pod_container_status(
        namespace=namespace,
        pod_name=pod_name,
    )


def investigate_resource(
    resource_type: str,
    name: str,
    namespace: str | None = None,
) -> dict:
    return investigation_service.investigate_resource(
        resource_type=resource_type,
        name=name,
        namespace=namespace,
    )