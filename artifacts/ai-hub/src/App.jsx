import { useState } from 'react';
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
import { Route, Switch, Link, useLocation } from 'wouter';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Activity, ArrowDown, ArrowLeft, ArrowRight, BarChart3, Check, ChevronRight,
  CircleAlert, Clock3, Database, FlaskConical, Gauge, Menu, RefreshCw, Send,
  ShieldCheck, Sparkles, X
} from 'lucide-react';
import {
  getGetRequestsQueryKey, getGetStatisticsQueryKey, useGetApplicationInfo,
  useGetHealth, useGetRequests, useGetStatistics, useHealthCheck,
  useSendChatMessage
} from '@workspace/api-client-react';
import { ErrorBoundary } from '@/components/error-boundary';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 15000, retry: 1, refetchOnWindowFocus: false } },
});

function AppShell({ children }) {
  const [location] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data: appInfo } = useGetApplicationInfo();
  const { data: health } = useGetHealth();
  const { data: legacyHealth } = useHealthCheck();

  const healthy =
    health?.status === 'ok' ||
    health?.status === 'healthy' ||
    legacyHealth?.status === 'ok' ||
    legacyHealth?.status === 'healthy';

  const navItems = [
    { href: '/', label: 'Experiments', icon: FlaskConical },
    { href: '/dashboard', label: 'Research dashboard', icon: BarChart3 },
  ];

  const links = navItems.map(({ href, label, icon: Icon }) => (
    <Link
      key={href}
      href={href}
      className={`nav-link ${location === href ? 'active' : ''}`}
      onClick={() => setMobileOpen(false)}
      data-testid={`link-${href === '/' ? 'experiments' : 'dashboard'}`}
    >
      <Icon size={17} strokeWidth={1.8} />
      <span>{label}</span>
    </Link>
  ));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Activity size={19} strokeWidth={2.2} />
          </div>

          <div className="brand-copy">
            <div className="brand-name">AI Hub</div>
            <div className="brand-sub">Research workspace</div>
          </div>
        </div>

        <div className="nav-label">Workspace</div>

        <nav aria-label="Main navigation">
          {links}
        </nav>

        <div className="sidebar-foot">
          <div className="health-chip" data-testid="status-api-health">
            <span
              className={`health-dot ${
                health || legacyHealth ? (healthy ? '' : 'offline') : ''
              }`}
            />

            <span>
              {health || legacyHealth
                ? healthy
                  ? 'API operational'
                  : `API ${health?.status || legacyHealth?.status}`
                : 'Checking API'}
            </span>
          </div>

          <div className="sidebar-note">
            {appInfo?.name || 'AI Hub Research System'}
            {appInfo?.version ? ` · v${appInfo.version}` : ''}
            <br />
            Evidence-backed model evaluation
          </div>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="mobile-menu"
              aria-label="Toggle navigation"
              onClick={() => setMobileOpen(!mobileOpen)}
              data-testid="button-mobile-navigation"
            >
              {mobileOpen ? <X size={19} /> : <Menu size={19} />}
            </button>

            <div className="crumb">
              <span>AI Hub</span>
              <ChevronRight size={13} />
              <strong>
                {location === '/dashboard'
                  ? 'Research dashboard'
                  : 'Experiments'}
              </strong>
            </div>
          </div>

          <div className="top-meta">
            <span
              className={`top-indicator ${
                health || legacyHealth ? (healthy ? '' : 'offline') : ''
              }`}
            />
            LIVE RESEARCH ENVIRONMENT
          </div>
        </header>

        {mobileOpen && (
          <nav className="mobile-nav" aria-label="Mobile navigation">
            {links}
          </nav>
        )}

        {children}
      </div>
    </div>
  );
}

function PageHeading({ eyebrow, title, description, meta }) {
  return (
    <div className="page-heading fade-in">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>

      {meta && <div className="heading-meta">{meta}</div>}
    </div>
  );
}

function DataError({ text, onRetry }) {
  return (
    <div
      className="error-box"
      role="alert"
      data-testid="status-load-error"
    >
      <span>{text}</span>

      <button
        className="retry-button"
        onClick={onRetry}
        data-testid="button-retry"
      >
        Retry
      </button>
    </div>
  );
}

function Skeleton({ className = '' }) {
  return (
    <div
      className={`panel skeleton-card ${className}`}
      aria-label="Loading data"
    >
      <div
        className="loading-line"
        style={{ width: '45%', marginBottom: 20 }}
      />

      <div
        className="loading-line"
        style={{ width: '72%', marginBottom: 12 }}
      />

      <div
        className="loading-line"
        style={{ width: '55%' }}
      />
    </div>
  );
}


function MarkdownResponse({ content }) {
  return (
    <div className="result-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="markdown-h1">{children}</h1>
          ),

          h2: ({ children }) => (
            <h2 className="markdown-h2">{children}</h2>
          ),

          h3: ({ children }) => (
            <h3 className="markdown-h3">{children}</h3>
          ),

          p: ({ children }) => (
            <p className="markdown-paragraph">{children}</p>
          ),

          strong: ({ children }) => (
            <strong className="markdown-bold">{children}</strong>
          ),

          em: ({ children }) => (
            <em className="markdown-italic">{children}</em>
          ),

          ul: ({ children }) => (
            <ul className="markdown-list">{children}</ul>
          ),

          ol: ({ children }) => (
            <ol className="markdown-list markdown-ordered-list">
              {children}
            </ol>
          ),

          li: ({ children }) => (
            <li className="markdown-list-item">{children}</li>
          ),

          blockquote: ({ children }) => (
            <blockquote className="markdown-blockquote">
              {children}
            </blockquote>
          ),

          code({ inline, className, children, ...props }) {
            const language =
              className?.replace('language-', '') || '';

            if (inline) {
              return (
                <code className="markdown-inline-code" {...props}>
                  {children}
                </code>
              );
            }

            return (
              <div className="markdown-code-wrapper">
                {language && (
                  <div className="markdown-code-language">
                    {language}
                  </div>
                )}

                <pre className="markdown-code-block">
                  <code className={className} {...props}>
                    {children}
                  </code>
                </pre>
              </div>
            );
          },

          a: ({ children, href }) => (
            <a
              className="markdown-link"
              href={href}
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),

          hr: () => <hr className="markdown-divider" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function LatestResult({ result }) {
  if (!result) {
    return (
      <div
        className="result-panel panel"
        data-testid="panel-latest-result"
      >
        <div className="result-header">
          <div>
            <h2 className="panel-title">Latest response</h2>
            <p className="panel-caption">
              Run an experiment to inspect the recorded result.
            </p>
          </div>
        </div>

        <div className="result-empty">
          <div>
            <div className="empty-mark">
              <Sparkles size={21} />
            </div>

            <div className="empty-title">
              Awaiting your first run
            </div>

            <p className="empty-copy">
              A real request result and its resilience metadata will appear
              here.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const status = result.success ? 'success' : 'failed';

  return (
    <div
      className="result-panel panel fade-in"
      data-testid={`panel-result-${result.id}`}
    >
      <div className="result-header">
        <div>
          <h2 className="panel-title">Latest response</h2>

          <p className="panel-caption">
            Request #{result.id} ·{' '}
            {new Date(result.createdAt).toLocaleString()}
          </p>
        </div>

        <span
          className={`status-pill ${
            result.isSimulated ? 'simulated' : status
          }`}
          data-testid="status-result"
        >
          {result.isSimulated ? (
            'Simulated'
          ) : result.success ? (
            <>
              <Check size={12} /> Success
            </>
          ) : (
            <>
              <CircleAlert size={12} /> Failed
            </>
          )}
        </span>
      </div>

      {result.isSimulated && (
        <p
          className="research-note"
          style={{ marginTop: 14 }}
        >
          This attempt is marked simulated by the API. It is not evidence
          from a real provider request and is excluded from experiment
          metrics.
        </p>
      )}

      {result.response ? (
        <div
          className="result-response"
          data-testid="text-response"
        >
          <MarkdownResponse content={result.response} />
        </div>
      ) : (
        <div
          className="result-error"
          data-testid="text-result-error"
        >
          {result.errorMessage ||
            'The request did not return a response.'}

          {result.errorType
            ? ` · ${result.errorType}`
            : ''}
        </div>
      )}

      <div className="result-stats">
        <div>
          <div className="result-stat-label">Task type</div>
          <div className="result-stat-value">
            {result.taskType}
          </div>
        </div>

        <div>
          <div className="result-stat-label">Response time</div>
          <div className="result-stat-value">
            {result.responseTimeMs} ms
          </div>
        </div>

        <div>
          <div className="result-stat-label">Selected model</div>
          <div className="result-stat-value">
            {result.model || 'Not reported'}
          </div>
        </div>

        <div>
          <div className="result-stat-label">
            Retries · fallback
          </div>
          <div className="result-stat-value">
            {result.retryCount} ·{' '}
            {result.fallbackUsed
              ? 'Used'
              : 'Not used'}
          </div>
        </div>

        <div>
          <div className="result-stat-label">
            Primary model
          </div>
          <div className="result-stat-value">
            {result.primaryModel}
          </div>
        </div>

        <div>
          <div className="result-stat-label">
            Fallback model
          </div>
          <div className="result-stat-value">
            {result.fallbackModel}
          </div>
        </div>
      </div>
    </div>
  );
}

function HomePage() {
  const [message, setMessage] = useState('');
  const [mode, setMode] = useState('baseline');
  const [latest, setLatest] = useState(null);
  const [submitError, setSubmitError] = useState('');

  const mutation = useSendChatMessage();
  const client = useQueryClient();

  const submit = (event) => {
    event.preventDefault();

    const trimmed = message.trim();

    if (!trimmed || mutation.isPending) {
      return;
    }

    setSubmitError('');

    mutation.mutate(
      {
        data: {
          message: trimmed,
          experimentMode: mode,
        },
      },
      {
        onSuccess: (result) => {
          setLatest(result);

          client.invalidateQueries({
            queryKey: getGetStatisticsQueryKey(),
          });

          client.invalidateQueries({
            queryKey: getGetRequestsQueryKey(),
          });
        },

        onError: (error) => {
          setSubmitError(
            error?.message ||
              'The request could not be completed. Please try again.'
          );
        },
      }
    );
  };

  return (
    <main className="page-content">
      <PageHeading
        eyebrow="Model selection · resilience testing"
        title="Run an experiment."
        description="Compare task-based model selection and fallback behavior using live provider requests."
        meta="POST /api/chat"
      />

      {submitError && (
        <div style={{ marginBottom: 16 }}>
          <DataError
            text={submitError}
            onRetry={() => {
              setSubmitError('');
            }}
          />
        </div>
      )}

      <div className="workspace-grid">
        <section className="experiment-panel panel">
          <div className="panel-top">
            <div>
              <h2 className="panel-title">
                Experiment setup
              </h2>

              <p className="panel-caption">
                Choose a protocol, then submit a research prompt.
              </p>
            </div>

            <div
              className="mode-toggle"
              role="group"
              aria-label="Experiment mode"
            >
              {['baseline', 'proposed'].map((value) => (
                <button
                  key={value}
                  type="button"
                  className={`mode-button ${
                    mode === value ? 'selected' : ''
                  }`}
                  aria-pressed={mode === value}
                  onClick={() => setMode(value)}
                  data-testid={`button-mode-${value}`}
                >
                  {value === 'baseline'
                    ? 'Baseline'
                    : 'Proposed'}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={submit}>
            <label
              className="form-label"
              htmlFor="research-prompt"
            >
              Research prompt
            </label>

            <textarea
              id="research-prompt"
              className="prompt-box"
              value={message}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              maxLength={10000}
              placeholder="Enter a prompt that represents a task you want to evaluate…"
              data-testid="input-research-prompt"
            />

            <div className="composer-foot">
              <span className="small-note">
                {message.length.toLocaleString()} / 10,000 characters
              </span>

              <button
                className="submit-button"
                type="submit"
                disabled={
                  !message.trim() ||
                  mutation.isPending
                }
                data-testid="button-submit-experiment"
              >
                {mutation.isPending ? (
                  <>
                    <RefreshCw
                      size={15}
                      className="spin-icon"
                    />
                    Sending request
                  </>
                ) : (
                  <>
                    Run request <Send size={14} />
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="research-note">
            <strong>Research protocol.</strong> Baseline and proposed modes
            are sent directly to the API. Results, model decisions, retries
            and timings are reported by the service; no outcome is inferred
            by this interface.
          </div>
        </section>

        <LatestResult result={latest} />
      </div>

      <div className="section-head">
        <h2>What gets recorded</h2>
        <span>Request evidence</span>
      </div>

      <div className="dashboard-kpis">
        {[
          {
            icon: Database,
            title: 'Persisted records',
            copy: 'Requests are backed by the research database.',
          },
          {
            icon: Gauge,
            title: 'Measured latency',
            copy: 'Response timing comes from each API result.',
          },
          {
            icon: ShieldCheck,
            title: 'Fallback tracking',
            copy: 'Retries and fallback usage are recorded.',
          },
          {
            icon: Activity,
            title: 'Simulation labels',
            copy: 'Simulated attempts stay clearly identified.',
          },
        ].map(({ icon: Icon, title, copy }) => (
          <div
            className="panel kpi-card"
            key={title}
          >
            <Icon
              className="kpi-icon"
              size={17}
            />

            <div className="kpi-label">
              {title}
            </div>

            <div
              className="kpi-foot"
              style={{
                marginTop: 11,
                maxWidth: 190,
                lineHeight: 1.5,
              }}
            >
              {copy}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}

function formatRate(value) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return '—';
  }

  const number = Number(value);

  return `${(number <= 1 ? number * 100 : number).toFixed(1)}%`;
}

function formatTime(value) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return '—';
  }

  return `${Number(value).toLocaleString()} ms`;
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
  testId,
}) {
  return (
    <div
      className="panel kpi-card"
      data-testid={testId}
    >
      <Icon
        className="kpi-icon"
        size={17}
      />

      <div className="kpi-label">
        {label}
      </div>

      <div className="kpi-value">
        {value}
      </div>

      <div className="kpi-foot">
        {detail}
      </div>
    </div>
  );
}

function Distribution({
  title,
  subtitle,
  items,
  labelKey,
  color = '',
}) {
  const max = Math.max(
    0,
    ...(items || []).map(
      (item) => Number(item.count) || 0
    )
  );

  return (
    <section className="data-panel panel">
      <h2>{title}</h2>

      <p className="subtitle">
        {subtitle}
      </p>

      {items?.length ? (
        items.map((item, index) => (
          <div
            className="bar-row"
            key={`${item[labelKey]}-${index}`}
            data-testid={`bar-${title
              .toLowerCase()
              .replaceAll(' ', '-')}-${index}`}
          >
            <span title={item[labelKey]}>
              {item[labelKey]}
            </span>

            <div className="bar-track">
              <div
                className={`bar-fill ${color}`}
                style={{
                  width: `${
                    max
                      ? (Number(item.count) /
                          max) *
                        100
                      : 0
                  }%`,
                }}
              />
            </div>

            <span className="bar-count">
              {item.count}
            </span>
          </div>
        ))
      ) : (
        <div className="empty-table">
          No recorded data yet.
        </div>
      )}
    </section>
  );
}

function Comparison({ items }) {
  return (
    <section className="data-panel panel">
      <h2>Baseline vs proposed</h2>

      <p className="subtitle">
        Comparison computed from recorded, non-simulated experiment metrics.
      </p>

      {items?.length ? (
        <div className="comparison-grid">
          {items.map((item) => (
            <div
              className="comparison-card"
              key={item.experimentMode}
              data-testid={`comparison-${item.experimentMode}`}
            >
              <div className="comparison-name">
                {item.experimentMode} protocol
              </div>

              <div className="comparison-rate">
                {formatRate(item.successRate)}
              </div>

              <div className="comparison-line">
                <span>Requests</span>
                <strong>{item.totalRequests}</strong>
              </div>

              <div className="comparison-line">
                <span>Successful</span>
                <strong>{item.successfulRequests}</strong>
              </div>

              <div className="comparison-line">
                <span>Failed</span>
                <strong>{item.failedRequests}</strong>
              </div>

              <div className="comparison-line">
                <span>Mean response</span>
                <strong>
                  {formatTime(item.averageResponseTimeMs)}
                </strong>
              </div>

              <div className="comparison-line">
                <span>Retries · fallback</span>
                <strong>
                  {item.totalRetries} · {item.fallbackEvents}
                </strong>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div
          className="empty-table"
          data-testid="empty-comparison"
        >
          No experiment comparisons have been recorded.
        </div>
      )}
    </section>
  );
}

function DashboardPage() {
  const [filter, setFilter] = useState('');
  const [offset, setOffset] = useState(0);
  const limit = 10;

  const params = {
    limit,
    offset,
    ...(filter
      ? { experimentMode: filter }
      : {}),
  };

  const statsQuery = useGetStatistics();
  const requestsQuery = useGetRequests(params);

  const stats = statsQuery.data;
  const requestList = requestsQuery.data;

  const total = requestList?.total || 0;
  const pageCount = Math.max(
    1,
    Math.ceil(total / limit)
  );

  const currentPage =
    Math.floor(offset / limit) + 1;

  const refetchAll = () => {
    statsQuery.refetch();
    requestsQuery.refetch();
  };

  const onFilter = (event) => {
    setFilter(event.target.value);
    setOffset(0);
  };

  return (
    <main className="page-content">
      <PageHeading
        eyebrow="PostgreSQL-backed evidence"
        title="Research dashboard."
        description="Actual request metrics and stored experiment records. Simulated attempts are excluded from experiment statistics."
        meta={
          stats
            ? `${stats.simulatedRequestsExcluded} simulated excluded`
            : 'LIVE METRICS'
        }
      />

      {(statsQuery.isError ||
        requestsQuery.isError) && (
        <div style={{ marginBottom: 16 }}>
          <DataError
            text="Some research data could not be loaded."
            onRetry={refetchAll}
          />
        </div>
      )}

      {statsQuery.isLoading ? (
        <div className="dashboard-kpis">
          {[0, 1, 2, 3].map((n) => (
            <Skeleton key={n} />
          ))}
        </div>
      ) : stats ? (
        <>
          <div className="dashboard-kpis">
            <MetricCard
              icon={Database}
              label="Actual requests"
              value={stats.totalRequests.toLocaleString()}
              detail={`${stats.successfulRequests.toLocaleString()} successful · ${stats.failedRequests.toLocaleString()} failed`}
              testId="metric-total-requests"
            />

            <MetricCard
              icon={Check}
              label="Success rate"
              value={formatRate(stats.successRate)}
              detail={`${formatRate(stats.failureRate)} failure rate`}
              testId="metric-success-rate"
            />

            <MetricCard
              icon={Clock3}
              label="Mean response time"
              value={formatTime(stats.averageResponseTimeMs)}
              detail="Recorded response time"
              testId="metric-mean-response"
            />

            <MetricCard
              icon={ArrowDown}
              label="Resilience events"
              value={`${stats.totalRetries} retries`}
              detail={`${stats.fallback.totalEvents} fallbacks · ${formatRate(stats.fallback.percentage)}`}
              testId="metric-resilience"
            />
          </div>

          <div
            className="research-note"
            style={{ marginTop: 13 }}
            data-testid="note-simulated-excluded"
          >
            <strong>
              {stats.simulatedRequestsExcluded.toLocaleString()}{' '}
              simulated{' '}
              {stats.simulatedRequestsExcluded === 1
                ? 'attempt'
                : 'attempts'}{' '}
              excluded.
            </strong>{' '}
            Metrics and comparisons are sourced from the API; simulated
            requests are not counted as experiment evidence.
          </div>

          <div className="dashboard-columns">
            <Distribution
              title="Task distribution"
              subtitle="Recorded requests by API-classified task type."
              items={stats.taskDistribution}
              labelKey="taskType"
            />

            <Distribution
              title="Model usage"
              subtitle="Requests by reported model."
              items={stats.modelUsage}
              labelKey="model"
              color="orange"
            />

            <Comparison
              items={stats.experimentComparison}
            />

            <Distribution
              title="Error analysis"
              subtitle="Recorded errors by API-reported type."
              items={stats.errorAnalysis}
              labelKey="errorType"
              color="green"
            />
          </div>

          <section style={{ marginTop: 23 }}>
            <div className="section-head">
              <div>
                <h2>Request records</h2>

                <span
                  style={{
                    display: 'block',
                    marginTop: 5,
                  }}
                >
                  Stored API attempts ·{' '}
                  {total.toLocaleString()} total
                </span>
              </div>

              <div className="filters">
                <select
                  className="filter-select"
                  value={filter}
                  onChange={onFilter}
                  aria-label="Filter by experiment mode"
                  data-testid="select-experiment-mode"
                >
                  <option value="">
                    All protocols
                  </option>

                  <option value="baseline">
                    Baseline
                  </option>

                  <option value="proposed">
                    Proposed
                  </option>
                </select>

                <button
                  className="icon-button"
                  aria-label="Refresh records"
                  onClick={refetchAll}
                  data-testid="button-refresh-dashboard"
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </div>

            <div className="panel data-panel">
              {requestsQuery.isLoading ? (
                <div
                  style={{
                    display: 'grid',
                    gap: 12,
                  }}
                >
                  {[1, 2, 3].map((n) => (
                    <div
                      key={n}
                      className="loading-line"
                      style={{ height: 35 }}
                    />
                  ))}
                </div>
              ) : requestList?.items?.length ? (
                <>
                  <div className="table-wrap">
                    <table className="request-table">
                      <thead>
                        <tr>
                          <th>Request ID</th>
                          <th>Task</th>
                          <th>Mode</th>
                          <th>Selected model</th>
                          <th>Status</th>
                          <th>Response time</th>
                          <th>Retries</th>
                          <th>Error type</th>
                          <th>Fallback</th>
                          <th>Simulation</th>
                          <th>Created</th>
                        </tr>
                      </thead>

                      <tbody>
                        {requestList.items.map(
                          (record) => (
                            <tr
                              key={record.id}
                              data-testid={`row-request-${record.id}`}
                            >
                              <td className="mono">
                                #{record.id}
                              </td>

                              <td>
                                {record.taskType}
                              </td>

                              <td>
                                {record.experimentMode}
                              </td>

                              <td>
                                {record.model || '—'}
                              </td>

                              <td>
                                <span
                                  className={`status-pill ${
                                    record.finalStatus ===
                                    'success'
                                      ? 'success'
                                      : 'failed'
                                  }`}
                                >
                                  {record.finalStatus}
                                </span>
                              </td>

                              <td className="mono">
                                {record.responseTimeMs} ms
                              </td>

                              <td className="mono">
                                {record.retryCount}
                              </td>

                              <td>
                                {record.errorType || '—'}
                              </td>

                              <td>
                                {record.fallbackUsed
                                  ? 'Used'
                                  : '—'}
                              </td>

                              <td>
                                <span
                                  className={`status-pill ${
                                    record.isSimulated
                                      ? 'simulated'
                                      : 'success'
                                  }`}
                                >
                                  {record.isSimulated
                                    ? 'Simulated'
                                    : 'No'}
                                </span>
                              </td>

                              <td className="mono">
                                {new Date(
                                  record.createdAt
                                ).toLocaleString()}
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className="pagination">
                    <span>
                      Showing {offset + 1}–
                      {Math.min(
                        offset + limit,
                        total
                      )}{' '}
                      of {total.toLocaleString()}
                    </span>

                    <div className="page-buttons">
                      <button
                        className="icon-button"
                        disabled={offset === 0}
                        onClick={() =>
                          setOffset(
                            Math.max(
                              0,
                              offset - limit
                            )
                          )
                        }
                        aria-label="Previous page"
                        data-testid="button-previous-page"
                      >
                        <ArrowLeft size={14} />
                      </button>

                      <span className="mono">
                        {currentPage} / {pageCount}
                      </span>

                      <button
                        className="icon-button"
                        disabled={
                          offset + limit >= total
                        }
                        onClick={() =>
                          setOffset(
                            offset + limit
                          )
                        }
                        aria-label="Next page"
                        data-testid="button-next-page"
                      >
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div
                  className="empty-table"
                  data-testid="empty-request-records"
                >
                  {requestsQuery.isError
                    ? 'Request records are temporarily unavailable.'
                    : 'No request records match this filter.'}
                </div>
              )}
            </div>
          </section>
        </>
      ) : !statsQuery.isError ? (
        <div
          className="panel empty-table"
          data-testid="empty-dashboard"
        >
          No statistics are available yet.
        </div>
      ) : null}
    </main>
  );
}

function NotFoundPage() {
  return (
    <main className="page-content">
      <PageHeading
        eyebrow="Workspace"
        title="Page not found."
        description="This route is not part of the research workspace."
      />

      <Link
        href="/"
        className="submit-button"
        data-testid="link-return-home"
      >
        Return to experiments
      </Link>
    </main>
  );
}

function RoutedApp() {
  const [location] = useLocation();

  return (
    <ErrorBoundary resetKey={location}>
      <AppShell>
        <Switch>
          <Route
            path="/"
            component={HomePage}
          />

          <Route
            path="/dashboard"
            component={DashboardPage}
          />

          <Route component={NotFoundPage} />
        </Switch>
      </AppShell>
    </ErrorBoundary>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RoutedApp />
    </QueryClientProvider>
  );
}

export default App;

