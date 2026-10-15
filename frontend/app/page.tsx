"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

type InvestigationResponse = {
  investigation_id?: string | null;

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

type InvestigationHistoryItem = {
  id: string;

  created_at: string;

  question: string;

  resource: {
    type: string;
    name: string;
    namespace: string | null;
  } | null;

  assessment: {
    status: string;
    severity: string;
  };
};

type InvestigationHistoryResponse = {
  id: string;

  created_at: string;

  question: string;

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
  const [namespace, setNamespace] =
    useState("aiops-demo");

  const [resourceType, setResourceType] =
    useState("Deployment");

  const [resourceName, setResourceName] =
    useState("demo-api");

  const [question, setQuestion] = useState(
    "Why is the demo-api deployment unhealthy?"
  );

  const [result, setResult] =
    useState<InvestigationResponse | null>(null);

  const [history, setHistory] =
    useState<InvestigationHistoryItem[]>([]);

  const [selectedInvestigationId, setSelectedInvestigationId] =
    useState<string | null>(null);

  const [loading, setLoading] = useState(false);

  const [historyLoading, setHistoryLoading] =
    useState(true);

  const [historyItemLoading, setHistoryItemLoading] =
    useState(false);

  const [error, setError] = useState("");

  const [historyError, setHistoryError] =
    useState("");

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    setHistoryLoading(true);
    setHistoryError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/investigations`
      );

      if (!response.ok) {
        const errorBody = await response.text();

        throw new Error(
          `Unable to load investigation history: ${response.status} ${errorBody}`
        );
      }

      const data: InvestigationHistoryItem[] =
        await response.json();

      setHistory(data);
    } catch (err) {
      setHistoryError(
        err instanceof Error
          ? err.message
          : "Unable to load investigation history."
      );
    } finally {
      setHistoryLoading(false);
    }
  }

  async function loadInvestigation(
    investigationId: string
  ) {
    setHistoryItemLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/investigations/${investigationId}`
      );

      if (!response.ok) {
        const errorBody = await response.text();

        throw new Error(
          `Unable to load investigation: ${response.status} ${errorBody}`
        );
      }

      const data: InvestigationHistoryResponse =
        await response.json();

      setResult({
        investigation_id: data.id,
        resource: data.resource,
        assessment: data.assessment,
        facts: data.facts,
        root_cause: data.root_cause,
        hypotheses: data.hypotheses,
        recommended_next_steps:
          data.recommended_next_steps,
        investigation: data.investigation,
      });

      setSelectedInvestigationId(data.id);

      if (data.resource) {
        setNamespace(
          data.resource.namespace ?? ""
        );

        setResourceType(
          data.resource.type
        );

        setResourceName(
          data.resource.name
        );
      }

      setQuestion(data.question);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load the selected investigation."
      );
    } finally {
      setHistoryItemLoading(false);
    }
  }

  async function investigate(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/investigate`,
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

      const investigationId =
        data.investigation_id;

      if (investigationId) {
        setSelectedInvestigationId(
          investigationId
        );

        await loadHistory();
      }
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

  function formatDate(
    timestamp: string
  ): string {
    const date = new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
      return timestamp;
    }

    return date.toLocaleString();
  }

  function getStatusClasses(
    status: string
  ): string {
    switch (status.toLowerCase()) {
      case "failed":
        return "bg-red-500/10 text-red-400";

      case "degraded":
        return "bg-yellow-500/10 text-yellow-400";

      case "healthy":
        return "bg-green-500/10 text-green-400";

      default:
        return "bg-slate-800 text-slate-300";
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-10">
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

        <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="h-fit rounded-xl border border-slate-800 bg-slate-900">
            <div className="border-b border-slate-800 px-4 py-4">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">
                  Investigation History
                </h2>

                <button
                  type="button"
                  onClick={loadHistory}
                  disabled={historyLoading}
                  className="text-xs text-blue-400 transition hover:text-blue-300 disabled:opacity-50"
                >
                  {historyLoading
                    ? "Loading..."
                    : "Refresh"}
                </button>
              </div>
            </div>

            <div className="max-h-[calc(100vh-220px)] overflow-y-auto p-2">
              {historyError && (
                <div className="m-2 rounded-lg border border-red-900 bg-red-950/40 p-3 text-xs text-red-300">
                  {historyError}
                </div>
              )}

              {historyLoading && (
                <div className="px-3 py-6 text-center text-sm text-slate-500">
                  Loading history...
                </div>
              )}

              {!historyLoading &&
                !historyError &&
                history.length === 0 && (
                  <div className="px-3 py-6 text-center text-sm text-slate-500">
                    No investigations yet.
                  </div>
                )}

              {!historyLoading &&
                history.map((item) => {
                  const isSelected =
                    selectedInvestigationId ===
                    item.id;

                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() =>
                        loadInvestigation(item.id)
                      }
                      disabled={historyItemLoading}
                      className={`mb-2 w-full rounded-lg border p-3 text-left transition ${
                        isSelected
                          ? "border-blue-500/50 bg-blue-500/10"
                          : "border-transparent bg-slate-950 hover:border-slate-700 hover:bg-slate-800"
                      } disabled:cursor-not-allowed disabled:opacity-60`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">
                            {item.resource
                              ? `${item.resource.type}/${item.resource.name}`
                              : "Unknown resource"}
                          </p>

                          <p className="mt-1 truncate text-xs text-slate-500">
                            {item.question}
                          </p>
                        </div>

                        <span
                          className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${getStatusClasses(
                            item.assessment.status
                          )}`}
                        >
                          {item.assessment.status}
                        </span>
                      </div>

                      <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                        <span>
                          {item.assessment.severity}
                        </span>

                        <span>
                          {formatDate(
                            item.created_at
                          )}
                        </span>
                      </div>
                    </button>
                  );
                })}
            </div>
          </aside>

          <div className="min-w-0">
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
                      setNamespace(
                        event.target.value
                      )
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
                      setResourceType(
                        event.target.value
                      )
                    }
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-blue-500"
                  >
                    <option>
                      Deployment
                    </option>

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
                      setResourceName(
                        event.target.value
                      )
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
                    setQuestion(
                      event.target.value
                    )
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
                  {loading
                    ? "Investigating..."
                    : "Investigate"}
                </button>
              </div>
            </form>

            {historyItemLoading && (
              <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-5 text-sm text-slate-400">
                Loading historical investigation...
              </div>
            )}

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

            {result && !historyItemLoading && (
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

                      {result.resource
                        ?.namespace && (
                        <p className="mt-1 text-sm text-slate-400">
                          Namespace:{" "}
                          {result.resource.namespace}
                        </p>
                      )}
                    </div>

                    <div className="flex gap-3">
                      <span
                        className={`rounded-full px-3 py-1 text-sm font-medium ${getStatusClasses(
                          result.assessment.status
                        )}`}
                      >
                        {result.assessment.status}
                      </span>

                      <span className="rounded-full bg-orange-500/10 px-3 py-1 text-sm font-medium text-orange-400">
                        Severity:{" "}
                        {result.assessment.severity}
                      </span>
                    </div>
                  </div>

                  {result.investigation_id && (
                    <div className="mt-4 border-t border-slate-800 pt-4">
                      <p className="text-xs text-slate-500">
                        Investigation ID
                      </p>

                      <p className="mt-1 break-all font-mono text-xs text-slate-400">
                        {result.investigation_id}
                      </p>
                    </div>
                  )}
                </section>

                <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                  <h2 className="text-lg font-semibold">
                    Facts
                  </h2>

                  <ul className="mt-4 space-y-3">
                    {result.facts.map(
                      (fact, index) => (
                        <li
                          key={index}
                          className="flex gap-3 text-slate-300"
                        >
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />

                          <span>{fact}</span>
                        </li>
                      )
                    )}
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

                  {result.hypotheses.length ===
                  0 ? (
                    <p className="mt-4 text-sm text-slate-500">
                      No additional hypotheses were
                      identified.
                    </p>
                  ) : (
                    <ul className="mt-4 space-y-3">
                      {result.hypotheses.map(
                        (
                          hypothesis,
                          index
                        ) => (
                          <li
                            key={index}
                            className="flex gap-3 text-slate-300"
                          >
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-400" />

                            <span>
                              {hypothesis}
                            </span>
                          </li>
                        )
                      )}
                    </ul>
                  )}
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
                          (
                            evidence,
                            index
                          ) => (
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
        </div>
      </div>
    </main>
  );
}