from app.tools.prometheus import PrometheusInvestigator


def main():
    namespace = "aiops-demo"

    investigator = PrometheusInvestigator()

    print("\n=== POD INFO ===")

    for result in investigator.get_pod_info(namespace):
        print(result)

    print("\n=== POD RESTARTS ===")

    for result in investigator.get_pod_restarts(namespace):
        print(result)

    print("\n=== POD READINESS ===")

    for result in investigator.get_pod_readiness(namespace):
        print(result)

    print("\n=== POD MEMORY ===")

    for result in investigator.get_pod_memory_usage(namespace):
        print(result)

    print("\n=== POD CPU ===")

    for result in investigator.get_pod_cpu_usage(namespace):
        print(result)


if __name__ == "__main__":
    main()