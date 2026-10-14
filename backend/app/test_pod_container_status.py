import json

from app.services.investigation import (
    KubernetesInvestigationService,
)


service = KubernetesInvestigationService()


result = service.get_pod_container_status(
    namespace="aiops-demo",
    pod_name="demo-api-84ccd46854-c5rhs",
)


print(json.dumps(result, indent=2))