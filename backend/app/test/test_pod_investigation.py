import json

from app.tools.kubernetes import KubernetesInvestigator


investigator = KubernetesInvestigator()

result = investigator.investigate_pod(
    namespace="aiops-demo",
    pod_name="demo-api-976db9d5f-7pb5m",
)

print(json.dumps(result, indent=2))