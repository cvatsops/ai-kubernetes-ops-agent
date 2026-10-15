import json

from app.services.investigation import (
    KubernetesInvestigationService,
)


service = KubernetesInvestigationService()


result = service.get_container_logs(
    namespace="aiops-demo",
    pod_name="demo-api-84ccd46854-c5rhs",
    container_name="nginx",
    previous=True,
)


print(json.dumps(result, indent=2))