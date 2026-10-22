"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

type Tab =
  | "investigation"
  | "history"
  | "scenarios";

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

type DemoScenario = {
  id: string;
  name: string;
  description: string;
  resource_type: string;
  resource_name: string;
  question: string;
  namespace?: string;
  status?: string;
};

function getToolLabel(tool: string): string {
  const labels: Record<string, string> = {
    get_resource_summary: "Resource Summary",
    get_resource_relationships:
      "Resource Relationships",
    get_resource_events: "Kubernetes Events",
    get_pod_container_status: "Container Status",
    get_pod_configuration: "Pod Configuration",
    get_pod_metrics: "Prometheus Metrics",
    get_container_logs: "Container Logs",
    investigate_resource: "Deep Investigation",
  };

  return (
    labels[tool] ??
    tool.replaceAll("_", " ")
  );
}

function getStatusClasses(status: string): string {
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

export default function Home() {
  const [activeTab, setActiveTab] =
    useState<Tab>("investigation");

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

  const [scenarios, setScenarios] =
    useState<DemoScenario[]>([]);

  const [selectedScenarioId, setSelectedScenarioId] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [historyLoading, setHistoryLoading] =
    useState(false);

  const [historyItemLoading, setHistoryItemLoading] =
    useState(false);

  const [scenarioLoading, setScenarioLoading] =
    useState(false);

  const [error, setError] = useState("");
  const [historyError, setHistoryError] =
    useState("");
  const [scenarioError, setScenarioError] =
    useState("");

  const [scenarioPrepared, setScenarioPrepared] =
    useState(false);

  useEffect(() => {
    loadHistory();
    loadScenarios();
  }, []);

  async function loadHistory() {
    setHistoryLoading(true);
    setHistoryError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/investigations`
      );

      if (!response.ok) {
        const errorBody =
          await response.text();

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

  async function loadScenarios() {
    setScenarioError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios`
      );

      if (!response.ok) {
        const errorBody =
          await response.text();

        throw new Error(
          `Unable to load scenarios: ${response.status} ${errorBody}`
        );
      }

      const data: DemoScenario[] =
        await response.json();

      setScenarios(data);

      if (data.length > 0) {
        setSelectedScenarioId(data[0].id);
      }
    } catch (err) {
      setScenarioError(
        err instanceof Error
          ? err.message
          : "Unable to load demo scenarios."
      );
    }
  }

  async function prepareScenario() {
    if (!selectedScenarioId) {
      return;
    }

    setScenarioLoading(true);
    setScenarioError("");
    setScenarioPrepared(false);

    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${selectedScenarioId}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const errorBody =
          await response.text();

        throw new Error(
          `Unable to prepare scenario: ${response.status} ${errorBody}`
        );
      }

      const scenario: DemoScenario =
        await response.json();

      setNamespace(
        scenario.namespace ?? "aiops-demo"
      );

      setResourceType(
        scenario.resource_type
      );

      setResourceName(
        scenario.resource_name
      );

      setQuestion(
        scenario.question
      );

      setResult(null);
      setSelectedInvestigationId(null);
      setScenarioPrepared(true);
    } catch (err) {
      setScenarioError(
        err instanceof Error
          ? err.message
          : "Unable to prepare the selected scenario."
      );
    } finally {
      setScenarioLoading(false);
    }
  }

  function openPreparedScenario() {
    const scenario = scenarios.find(
      (item) =>
        item.id === selectedScenarioId
    );

    if (!scenario) {
      return;
    }

    setNamespace(
      scenario.namespace ?? "aiops-demo"
    );

    setResourceType(
      scenario.resource_type
    );

    setResourceName(
      scenario.resource_name
    );

    setQuestion(
      scenario.question
    );

    setResult(null);
    setSelectedInvestigationId(null);

    setActiveTab("investigation");
  }

  async function loadInvestigation(
    investigationId: string
  ) {
    setHistoryItemLoading(true);
    setHistoryError("");
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/investigations/${investigationId}`
      );

      if (!response.ok) {
        const errorBody =
          await response.text();

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

      setSelectedInvestigationId(
        data.id
      );

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

      setActiveTab("investigation");
    } catch (err) {
      setHistoryError(
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
    setResult(null);

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
        const errorBody =
          await response.text();

        throw new Error(
          `Investigation failed with status ${response.status}: ${errorBody}`
        );
      }

      const data: InvestigationResponse =
        await response.json();

      setResult(data);

      if (data.investigation_id) {
        setSelectedInvestigationId(
          data.investigation_id
        );
      }

      await loadHistory();
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

  const selectedScenario =
    scenarios.find(
      (scenario) =>
        scenario.id === selectedScenarioId
    );

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">

      {/* ====================================================== */}
      {/* TOP HEADER + NAVIGATION */}
      {/* ====================================================== */}

      <header className="border-b border-slate-800 bg-slate-950">

        <div className="mx-auto flex max-w-7xl items-center px-6">

          {/* Brand */}

          <div className="shrink-0 py-5 pr-12">
            <p className="text-lg font-semibold tracking-tight text-blue-400">
              AI Kubernetes Ops Agent
            </p>
          </div>

          {/* Tabs */}

          <nav className="flex h-full items-stretch gap-8">

            <button
              type="button"
              onClick={() =>
                setActiveTab("investigation")
              }
              className={`relative px-1 py-5 text-sm font-medium transition ${
                activeTab === "investigation"
                  ? "text-blue-400"
                  : "text-slate-400 hover:text-slate-100"
              }`}
            >
              New Investigation

              {activeTab === "investigation" && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-blue-500" />
              )}
            </button>

            <button
              type="button"
              onClick={() =>
                setActiveTab("history")
              }
              className={`relative px-1 py-5 text-sm font-medium transition ${
                activeTab === "history"
                  ? "text-blue-400"
                  : "text-slate-400 hover:text-slate-100"
              }`}
            >
              Investigation History

              {activeTab === "history" && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-blue-500" />
              )}
            </button>

            <button
              type="button"
              onClick={() =>
                setActiveTab("scenarios")
              }
              className={`relative px-1 py-5 text-sm font-medium transition ${
                activeTab === "scenarios"
                  ? "text-blue-400"
                  : "text-slate-400 hover:text-slate-100"
              }`}
            >
              Demo & Test Scenarios

              {activeTab === "scenarios" && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-blue-500" />
              )}
            </button>

          </nav>
        </div>
      </header>

      {/* ====================================================== */}
      {/* PAGE CONTENT */}
      {/* ====================================================== */}

      <div className="mx-auto max-w-7xl px-6 py-10">

        {/* Page heading */}

        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">
            Kubernetes Troubleshooting
          </h1>

          <p className="mt-2 max-w-3xl text-slate-400">
            Investigate Kubernetes workloads using current
            cluster evidence, progressive tool calls, and
            AI-assisted reasoning.
          </p>
        </div>

        {/* ================================================== */}
        {/* NEW INVESTIGATION */}
        {/* ================================================== */}

        {activeTab === "investigation" && (
          <section>

            <form
              onSubmit={investigate}
              className="rounded-xl border border-slate-800 bg-slate-900 p-6"
            >

              <div className="mb-6">
                <p className="text-sm font-medium text-blue-400">
                  Investigation
                </p>

                <h2 className="mt-1 text-xl font-semibold">
                  Investigate Kubernetes Resource
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Provide the resource and question you
                  want the agent to investigate.
                </p>
              </div>

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

                    <option>
                      Pod
                    </option>

                    <option>
                      Service
                    </option>
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
                  className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading
                    ? "Investigating..."
                    : "Investigate"}
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

                {/* Resource */}

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

                {/* Evidence */}

                <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                  <div className="flex items-center justify-between">

                    <div>

                      <h2 className="text-lg font-semibold">
                        Evidence Collected
                      </h2>

                      <p className="mt-1 text-sm text-slate-500">
                        Investigation completed using
                        evidence from the Kubernetes
                        environment.
                      </p>

                    </div>

                    <span className="rounded-full bg-green-500/10 px-3 py-1 text-xs font-medium text-green-400">
                      Complete
                    </span>

                  </div>

                  <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">

                    {result.investigation.tools_used.map(
                      (tool) => (
                        <div
                          key={tool}
                          className="rounded-lg border border-slate-800 bg-slate-950 p-4"
                        >

                          <div className="flex items-center gap-3">

                            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-green-500/10 text-xs text-green-400">
                              ✓
                            </span>

                            <span className="text-sm font-medium text-slate-300">
                              {getToolLabel(tool)}
                            </span>

                          </div>

                          <p className="mt-2 font-mono text-[10px] text-slate-600">
                            {tool}
                          </p>

                        </div>
                      )
                    )}

                  </div>

                  <div className="mt-6 border-t border-slate-800 pt-5">

                    <h3 className="text-sm font-medium text-slate-400">
                      Evidence Summary
                    </h3>

                    <ul className="mt-3 space-y-2">

                      {result.investigation.evidence_summary.map(
                        (evidence, index) => (
                          <li
                            key={index}
                            className="flex gap-3 text-sm text-slate-300"
                          >
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />

                            <span>
                              {evidence}
                            </span>
                          </li>
                        )
                      )}

                    </ul>

                  </div>

                </section>

                {/* Facts */}

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

                          <span>
                            {fact}
                          </span>
                        </li>
                      )
                    )}

                  </ul>

                </section>

                {/* Root Cause */}

                <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                  <h2 className="text-lg font-semibold">
                    Root Cause
                  </h2>

                  <p className="mt-4 leading-7 text-slate-300">
                    {result.root_cause}
                  </p>

                </section>

                {/* Hypotheses */}

                <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">

                  <h2 className="text-lg font-semibold">
                    Hypotheses
                  </h2>

                  {result.hypotheses.length === 0 ? (
                    <p className="mt-4 text-sm text-slate-500">
                      No additional hypotheses
                      were identified.
                    </p>
                  ) : (
                    <ul className="mt-4 space-y-3">

                      {result.hypotheses.map(
                        (hypothesis, index) => (
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

                {/* Recommended Next Steps */}

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

                          <span>
                            {step}
                          </span>
                        </li>
                      )
                    )}

                  </ol>

                </section>

              </div>
            )}
          </section>
        )}

        {/* ================================================== */}
        {/* HISTORY */}
        {/* ================================================== */}

        {activeTab === "history" && (
          <section>

            <div className="mb-6 flex items-end justify-between">

              <div>
                <p className="text-sm font-medium text-blue-400">
                  Investigations
                </p>

                <h2 className="mt-1 text-xl font-semibold">
                  Investigation History
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Review previous investigations stored in
                  Firestore.
                </p>
              </div>

              <button
                type="button"
                onClick={loadHistory}
                disabled={historyLoading}
                className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 transition hover:bg-slate-800 disabled:opacity-50"
              >
                {historyLoading
                  ? "Refreshing..."
                  : "Refresh"}
              </button>

            </div>

            {historyError && (
              <div className="mb-5 rounded-xl border border-red-900 bg-red-950/40 p-5 text-sm text-red-300">
                {historyError}
              </div>
            )}

            {historyLoading &&
              history.length === 0 && (
                <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center text-sm text-slate-500">
                  Loading investigation history...
                </div>
              )}

            {!historyLoading &&
              !historyError &&
              history.length === 0 && (
                <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center text-sm text-slate-500">
                  No investigations have been recorded yet.
                </div>
              )}

            {history.length > 0 && (
              <div className="space-y-3">

                {history.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() =>
                      loadInvestigation(
                        item.id
                      )
                    }
                    disabled={
                      historyItemLoading
                    }
                    className="w-full rounded-xl border border-slate-800 bg-slate-900 p-5 text-left transition hover:border-slate-700 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >

                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

                      <div className="min-w-0">

                        <div className="flex items-center gap-3">

                          <h3 className="truncate font-medium">
                            {item.resource
                              ? `${item.resource.type}/${item.resource.name}`
                              : "Unknown resource"}
                          </h3>

                          <span
                            className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${getStatusClasses(
                              item.assessment.status
                            )}`}
                          >
                            {item.assessment.status}
                          </span>

                        </div>

                        <p className="mt-2 truncate text-sm text-slate-400">
                          {item.question}
                        </p>

                        {item.resource?.namespace && (
                          <p className="mt-2 text-xs text-slate-600">
                            Namespace:{" "}
                            {item.resource.namespace}
                          </p>
                        )}

                      </div>

                      <div className="shrink-0 text-right">

                        <p className="text-sm text-orange-400">
                          {item.assessment.severity}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          {formatDate(
                            item.created_at
                          )}
                        </p>

                      </div>

                    </div>

                  </button>
                ))}

              </div>
            )}

          </section>
        )}

        {/* ================================================== */}
        {/* DEMO & TEST SCENARIOS */}
        {/* ================================================== */}

        {activeTab === "scenarios" && (
          <section>

            <div className="mb-6">

              <p className="text-sm font-medium text-blue-400">
                Developer & Demo Tools
              </p>

              <h2 className="mt-1 text-xl font-semibold">
                Demo & Test Scenarios
              </h2>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
                Reproduce controlled Kubernetes failure
                conditions for demonstrations and agent
                evaluation.
              </p>

            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">

              <div className="grid gap-8 lg:grid-cols-[1fr_320px]">

                <div>

                  <label
                    htmlFor="scenario"
                    className="mb-2 block text-sm font-medium"
                  >
                    Scenario
                  </label>

                  <select
                    id="scenario"
                    value={
                      selectedScenarioId
                    }
                    onChange={(event) => {
                      setSelectedScenarioId(
                        event.target.value
                      );

                      setScenarioPrepared(
                        false
                      );
                    }}
                    disabled={
                      scenarioLoading
                    }
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 outline-none focus:border-blue-500"
                  >
                    {scenarios.length === 0 ? (
                      <option value="">
                        No scenarios available
                      </option>
                    ) : (
                      scenarios.map(
                        (scenario) => (
                          <option
                            key={
                              scenario.id
                            }
                            value={
                              scenario.id
                            }
                          >
                            {scenario.name}
                          </option>
                        )
                      )
                    )}
                  </select>

                  {selectedScenario && (
                    <div className="mt-5 rounded-lg border border-slate-800 bg-slate-950 p-5">

                      <p className="text-sm font-medium text-slate-300">
                        {selectedScenario.name}
                      </p>

                      <p className="mt-2 text-sm leading-6 text-slate-500">
                        {selectedScenario.description}
                      </p>

                    </div>
                  )}

                  {scenarioError && (
                    <div className="mt-4 rounded-lg border border-red-900 bg-red-950/40 p-4 text-sm text-red-300">
                      {scenarioError}
                    </div>
                  )}

                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-950 p-5">

                  <p className="text-xs font-medium uppercase tracking-wider text-slate-600">
                    Scenario Target
                  </p>

                  {selectedScenario ? (
                    <div className="mt-4 space-y-3">

                      <div>
                        <p className="text-xs text-slate-600">
                          Resource Type
                        </p>

                        <p className="mt-1 text-sm text-slate-300">
                          {selectedScenario.resource_type}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-600">
                          Resource Name
                        </p>

                        <p className="mt-1 break-all text-sm text-slate-300">
                          {selectedScenario.resource_name}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-600">
                          Namespace
                        </p>

                        <p className="mt-1 text-sm text-slate-300">
                          {selectedScenario.namespace ??
                            "aiops-demo"}
                        </p>
                      </div>

                    </div>
                  ) : (
                    <p className="mt-4 text-sm text-slate-600">
                      Select a scenario.
                    </p>
                  )}

                </div>

              </div>

              <div className="mt-8 flex flex-col gap-3 border-t border-slate-800 pt-6 sm:flex-row sm:justify-end">

                <button
                  type="button"
                  onClick={
                    prepareScenario
                  }
                  disabled={
                    scenarioLoading ||
                    !selectedScenarioId
                  }
                  className="rounded-lg bg-slate-800 px-5 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {scenarioLoading
                    ? "Preparing..."
                    : "Prepare Scenario"}
                </button>

                {scenarioPrepared && (
                  <button
                    type="button"
                    onClick={
                      openPreparedScenario
                    }
                    className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-500"
                  >
                    Open Investigation
                  </button>
                )}

              </div>

            </div>

            {scenarioPrepared &&
              selectedScenario && (
                <div className="mt-5 rounded-xl border border-green-900/50 bg-green-950/20 p-5">

                  <div className="flex items-start gap-3">

                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-green-500/10 text-sm text-green-400">
                      ✓
                    </span>

                    <div>

                      <p className="font-medium text-green-400">
                        Scenario prepared
                      </p>

                      <p className="mt-1 text-sm text-slate-400">
                        Kubernetes has been prepared with the
                        selected failure condition.
                      </p>

                      <p className="mt-3 text-sm text-slate-500">
                        Click{" "}
                        <span className="text-slate-300">
                          Open Investigation
                        </span>{" "}
                        to investigate the prepared resource
                        using the AI agent.
                      </p>

                    </div>

                  </div>

                </div>
              )}

          </section>
        )}

      </div>
    </main>
  );
}