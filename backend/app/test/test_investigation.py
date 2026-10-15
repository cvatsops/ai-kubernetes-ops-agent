import json

from app.services.investigation import KubernetesInvestigationService


def main():
    service = KubernetesInvestigationService()

    result = service.investigate_namespace("aiops-demo")

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()