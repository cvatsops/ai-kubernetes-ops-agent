import json

from app.services.investigation import (
    KubernetesInvestigationService,
)


service = KubernetesInvestigationService()


result = service.get_resource_events(
    resource_type="deployment",
    name="demo-api",
    namespace="aiops-demo",
)


print(json.dumps(result, indent=2))