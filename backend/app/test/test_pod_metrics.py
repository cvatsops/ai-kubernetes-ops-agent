import json

from app.services.investigation import (
    KubernetesInvestigationService,
)


service = KubernetesInvestigationService()


result = service.get_pod_metrics(
    namespace="aiops-demo",
    pod_name="demo-api-976db9d5f-7pb5m",
)


print(json.dumps(result, indent=2))