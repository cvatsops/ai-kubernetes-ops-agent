"use client";

import { FormEvent, useState } from "react";

type InvestigationResponse = {
  resource: {
    type: string;
    name: string;
    namespace: string | null;
  } | null;

  assessment: {
    status: string;
    severity: string;
  };

  facts: string[];

  root_cause: string;

  hypotheses: string[];

  recommended_next_steps: string[];

  investigation: {
    tools_used: string[];
    evidence_summary: string[];
  };
};

export default function Home() {
  const [namespace, setNamespace] = useState("aiops-demo");

  const [resourceType, setResourceType] =
    useState("Deployment");

  const [resourceName, setResourceName] =
    useState("demo-api");

  const [question, setQuestion] = useState(
    "Why is the demo-api deployment unhealthy?"
  );

  const [result, setResult] =
    useState<InvestigationResponse | null>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  async function investigate(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/investigate",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            question,
            resource_type: resourceType,
            resource_name: resourceName,
            namespace,
          }),
        }
      );

      if (!response.ok) {
        const errorBody = await response.text();

        throw new Error(
          `Investigation failed with status ${response.status}: ${errorBody}`
        );
      }

      const data: InvestigationResponse =
        await response.json();

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to investigate the Kubernetes resource."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <header className="mb-8">
          <p className="mb-2 text-sm font-medium text-blue-400">
            AI Kubernetes Ops Agent
          </p>

          <h1 className="text-3xl font-bold tracking-tight">
            Kubernetes Troubleshooting
          </h1>

          <p className="mt-2 max-w-2xl text-slate-400">
            Investigate Kubernetes workloads using current
            cluster evidence, progressive tool calls, and
            AI-assisted reasoning.
          </p>
        </header>

        <form
          onSubmit={investigate}
          className="rounded-xl border border-slate-800 bg-slate-900 p-6"
        >
          <div className="grid gap-5 md:grid-cols-3">
            <div>
              <label
                htmlFor="namespace"
                className="mb-2 block text-sm font-medium"
              >
                Namespace
              </label>

              <input
                id="namespace"
                value={namespace}
                onChange={(event) =>
                  setNamespace(event.target.value)
                }
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label
                htmlFor="resourceType"
                className="mb-2 block text-sm font-medium"
              >
                Resource Type
              </label>

              <select
                id="resourceType"
                value={resourceType}
                onChange={(event) =>
                  setResourceType(event.target.value)
                }
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              >
                <option>Deployment</option>
                <option>Pod</option>
                <option>Service</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="resourceName"
                className="mb-2 block text-sm font-medium"
              >
                Resource Name
              </label>

              <input
                id="resourceName"
                value={resourceName}
                onChange={(event) =>
                  setResourceName(event.target.value)
                }
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="mt-5">
            <label
              htmlFor="question"
              className="mb-2 block text-sm font-medium"
            >
              Investigation Question
            </label>

            <textarea
              id="question"
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              rows={4}
              className="w-full resize-none rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 outline-none focus:border-blue-500"
              placeholder="Why is this workload unhealthy?"
            />
          </div>

          <div className="mt-5 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-blue-600 px-5 py-2.5 font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Investigating..." : "Investigate"}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-6 rounded-xl border border-red-900 bg-red-950/40 p-5 text-red-300">
            <p className="font-medium">
              Investigation failed
            </p>

            <p className="mt-1 text-sm">
              {error}
            </p>
          </div>
        )}

        {result && (
          <div className="mt-8 space-y-6">
            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm text-slate-400">
                    Resource
                  </p>

                  <h2 className="mt-1 text-xl font-semibold">
                    {result.resource
                      ? `${result.resource.type}/${result.resource.name}`
                      : "Resource not identified"}
                  </h2>

                  {result.resource?.namespace && (
                    <p className="mt-1 text-sm text-slate-400">
                      Namespace:{" "}
                      {result.resource.namespace}
                    </p>
                  )}
                </div>

                <div className="flex gap-3">
                  <span className="rounded-full bg-red-500/10 px-3 py-1 text-sm font-medium text-red-400">
                    {result.assessment.status}
                  </span>

                  <span className="rounded-full bg-orange-500/10 px-3 py-1 text-sm font-medium text-orange-400">
                    Severity:{" "}
                    {result.assessment.severity}
                  </span>
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h2 className="text-lg font-semibold">
                Facts
              </h2>

              <ul className="mt-4 space-y-3">
                {result.facts.map((fact, index) => (
                  <li
                    key={index}
                    className="flex gap-3 text-slate-300"
                  >
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />

                    <span>{fact}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h2 className="text-lg font-semibold">
                Root Cause
              </h2>

              <p className="mt-4 leading-7 text-slate-300">
                {result.root_cause}
              </p>
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h2 className="text-lg font-semibold">
                Hypotheses
              </h2>

              <ul className="mt-4 space-y-3">
                {result.hypotheses.map(
                  (hypothesis, index) => (
                    <li
                      key={index}
                      className="flex gap-3 text-slate-300"
                    >
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-400" />

                      <span>{hypothesis}</span>
                    </li>
                  )
                )}
              </ul>
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h2 className="text-lg font-semibold">
                Recommended Next Steps
              </h2>

              <ol className="mt-4 space-y-3">
                {result.recommended_next_steps.map(
                  (step, index) => (
                    <li
                      key={index}
                      className="flex gap-3 text-slate-300"
                    >
                      <span className="font-semibold text-blue-400">
                        {index + 1}.
                      </span>

                      <span>{step}</span>
                    </li>
                  )
                )}
              </ol>
            </section>

            <details className="rounded-xl border border-slate-800 bg-slate-900">
              <summary className="cursor-pointer px-6 py-5 font-semibold">
                Investigation Evidence
              </summary>

              <div className="border-t border-slate-800 px-6 py-5">
                <div>
                  <h3 className="text-sm font-medium text-slate-400">
                    Tools Used
                  </h3>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {result.investigation.tools_used.map(
                      (tool) => (
                        <span
                          key={tool}
                          className="rounded-md bg-slate-800 px-2.5 py-1 text-xs text-slate-300"
                        >
                          {tool}
                        </span>
                      )
                    )}
                  </div>
                </div>

                <div className="mt-6">
                  <h3 className="text-sm font-medium text-slate-400">
                    Evidence Summary
                  </h3>

                  <ul className="mt-3 space-y-2">
                    {result.investigation.evidence_summary.map(
                      (evidence, index) => (
                        <li
                          key={index}
                          className="text-sm text-slate-300"
                        >
                          • {evidence}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              </div>
            </details>
          </div>
        )}
      </div>
    </main>
  );
}