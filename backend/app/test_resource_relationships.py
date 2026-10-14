import json

from app.services.investigation import (
    KubernetesInvestigationService,
)


service = KubernetesInvestigationService()


result = service.get_resource_relationships(
    resource_type="deployment",
    name="demo-api",
    namespace="aiops-demo",
)


print(json.dumps(result, indent=2))