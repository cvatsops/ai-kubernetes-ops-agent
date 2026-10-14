import json

from app.tools.kubernetes import KubernetesInvestigator


investigator = KubernetesInvestigator()


pod_name = input("Enter a Pod name: ").strip()

result = investigator.investigate_resource(
    resource_type="deployment",
    name="demo-api",
    namespace="aiops-demo",
)

print(json.dumps(result, indent=2))