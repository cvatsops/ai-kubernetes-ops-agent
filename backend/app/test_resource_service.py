import json

from app.services.investigation import KubernetesInvestigationService


service = KubernetesInvestigationService()

result = service.investigate_resource(
    resource_type="deployment",
    name="demo-api",
    namespace="aiops-demo",
)

print(json.dumps(result, indent=2))