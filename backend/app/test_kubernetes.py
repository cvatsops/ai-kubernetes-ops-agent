from app.tools.kubernetes import KubernetesInvestigator


def main():
    namespace = "aiops-demo"

    investigator = KubernetesInvestigator()

    print("\n=== PODS ===")

    pods = investigator.get_pods(namespace)

    for pod in pods:
        print(pod)

    print("\n=== DEPLOYMENTS ===")

    deployments = investigator.get_deployments(namespace)

    for deployment in deployments:
        print(deployment)

    print("\n=== EVENTS ===")

    events = investigator.get_events(namespace)

    for event in events:
        print(event)

    print("\n=== SERVICES ===")

    services = investigator.get_services(namespace)

    for service in services:
        print(service)

if __name__ == "__main__":
    main()