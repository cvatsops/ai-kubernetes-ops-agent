import asyncio

from google.adk.runners import InMemoryRunner

from app.agents.kubernetes_agent import root_agent


async def main():
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="ai-kubernetes-ops-agent",
    )

    response = await runner.run_debug(
    """
    Investigate the demo-api deployment in the aiops-demo namespace.

    Is it healthy?

    Look at the deployment, ReplicaSets, Pods, events,
    Pod logs and available metrics.

    Explain your conclusion using the evidence.
    """
)

    print(response)


if __name__ == "__main__":
    asyncio.run(main())