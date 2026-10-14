import json

from app.services.investigation import KubernetesInvestigationService


service = KubernetesInvestigationService()

result = service.investigate_workload(
    namespace="aiops-demo",
    workload="demo-api",
)

print(json.dumps(result, indent=2))