import {
    lazy,
    Suspense,
    useEffect,
    useRef,
    useState,
    type FormEvent,
} from "react";
import {
    Link,
    NavLink,
    Navigate,
    Outlet,
    Route,
    Routes,
    useLocation,
} from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
    ArrowRight,
    ArrowSquareOut,
    BookOpen,
    CheckCircle,
    Flask,
    Gear,
    Heartbeat,
    List,
    LockKey,
    MagnifyingGlass,
    Phone,
    SignOut,
    SquaresFour,
    WarningCircle,
    Waveform,
} from "@phosphor-icons/react";
import { getHealth } from "../lib/api/client";
import { useSession } from "./auth";
import { DataBoundary, Pending } from "../features/workspace/shared";

const CallReviewPage = lazy(() =>
    import("../features/reviews/CallReviewPage").then((m) => ({
        default: m.CallReviewPage,
    })),
);

const DashboardPage = lazy(() =>
    import("../features/analytics/DashboardPage").then((m) => ({
        default: m.DashboardPage,
    })),
);
const CallsPage = lazy(() =>
    import("../features/calls/CallsPage").then((m) => ({
        default: m.CallsPage,
    })),
);
const CallDetailPage = lazy(() =>
    import("../features/calls/CallDetailPage").then((m) => ({
        default: m.CallDetailPage,
    })),
);
const ReportWorkspace = lazy(() =>
    import("../features/workspace/ReportWorkspace").then((m) => ({
        default: m.ReportWorkspace,
    })),
);
const LivePage = lazy(() =>
    import("../features/live/LivePage").then((m) => ({ default: m.LivePage })),
);
const ModelsPage = lazy(() =>
    import("../features/models/ModelsPage").then((m) => ({
        default: m.ModelsPage,
    })),
);

const routes = [
    {
        path: "/overview",
        name: "Overview",
        icon: SquaresFour,
        description: "A single view of your call operations.",
    },
    {
        path: "/calls",
        name: "Calls",
        icon: Phone,
        description: "Find recordings and follow analysis progress.",
    },
    {
        path: "/qa",
        name: "QA & compliance",
        icon: CheckCircle,
        description: "Inspect quality and compliance evidence.",
    },
    {
        path: "/emotion",
        name: "Emotion review",
        icon: WarningCircle,
        description: "Review cautious acoustic evidence.",
    },
    {
        path: "/coaching",
        name: "Coaching",
        icon: BookOpen,
        description: "Review call-specific follow-up.",
    },
    {
        path: "/live",
        name: "Live monitoring",
        icon: Waveform,
        description: "A home for live conversations and assistance.",
    },
    {
        path: "/knowledge",
        name: "Knowledge base",
        icon: BookOpen,
        description: "Keep company guidance within reach.",
    },
    {
        path: "/models",
        name: "Model lab",
        icon: Flask,
        description: "Review model versions and evaluation evidence.",
    },
    {
        path: "/settings",
        name: "Settings",
        icon: Gear,
        description: "Manage workspace preferences and access.",
    },
    {
        path: "/health",
        name: "System health",
        icon: Heartbeat,
        description: "Check your connection to the local services.",
    },
];

export function App() {
    return (
        <Routes>
            <Route element={<AppShell />}>
                <Route index element={<Navigate to="/health" replace />} />
                <Route path="health" element={<HealthPage />} />
                <Route path="connect" element={<ConnectPage />} />
                <Route element={<RequireIdentity />}>
                    {routes
                        .filter((route) => route.path !== "/health")
                        .map((route) => (
                            <Route
                                key={route.path}
                                path={route.path}
                                element={
                                    <FeaturePage
                                        path={route.path}
                                        name={route.name}
                                        description={route.description}
                                    />
                                }
                            />
                        ))}
                    <Route
                        path="reviews/:callId"
                        element={
                            <Suspense fallback={<Pending />}>
                                <CallReviewPage />
                            </Suspense>
                        }
                    />
                    <Route
                        path="calls/:callId"
                        element={
                            <Suspense fallback={<Pending />}>
                                <CallDetailPage />
                            </Suspense>
                        }
                    />
                    <Route
                        path="compliance"
                        element={
                            <Suspense fallback={<Pending />}>
                                <ReportWorkspace kind="qa" />
                            </Suspense>
                        }
                    />
                </Route>
                <Route
                    path="*"
                    element={
                        <section className="panel empty-state">
                            <h1>Page not found</h1>
                            <p>
                                This address does not belong to the workspace.
                            </p>
                            <Link className="button" to="/health">
                                Go to system health
                            </Link>
                        </section>
                    }
                />
            </Route>
        </Routes>
    );
}

function AppShell() {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState("");
    const location = useLocation();
    const { identity, clear } = useSession();
    const menu = useRef<HTMLButtonElement>(null);
    const heading = useRef<HTMLElement>(null);
    const title =
        routes.find((route) => route.path === location.pathname)?.name ??
        (location.pathname.startsWith("/reviews/")
            ? "Human review"
            : location.pathname.startsWith("/calls/")
              ? "Call analysis"
              : location.pathname === "/compliance"
                ? "QA & compliance"
                : "Workspace access");
    useEffect(() => {
        document.title = `${title} · Adaptive Call Center Intelligence`;
        heading.current?.focus();
    }, [location.pathname, title]);
    useEffect(() => {
        function escape(event: KeyboardEvent) {
            if (event.key === "Escape" && open) {
                setOpen(false);
                menu.current?.focus();
            }
        }
        document.addEventListener("keydown", escape);
        return () => document.removeEventListener("keydown", escape);
    }, [open]);
    return (
        <div className="workspace">
            <a className="skip-link" href="#main">
                Skip to content
            </a>
            <header className="topbar">
                <Link className="brand" to="/health">
                    <span className="brand-mark" aria-hidden="true">
                        <Waveform size={25} weight="bold" />
                    </span>
                    <span>
                        Adaptive
                        <span className="brand-subtitle">
                            Call Center Intelligence
                        </span>
                    </span>
                </Link>
                <label className="nav-search">
                    <MagnifyingGlass size={19} aria-hidden="true" />
                    <span className="sr-only">Find a workspace page</span>
                    <input
                        placeholder="Find a workspace page…"
                        value={search}
                        onChange={(event) => {
                            setSearch(event.target.value);
                            setOpen(true);
                        }}
                    />
                </label>
                <div className="account">
                    <span className="avatar" aria-hidden="true">
                        {identity.data && !identity.isError ? "AU" : "G"}
                    </span>
                    <span>
                        {identity.data && !identity.isError
                            ? "Workspace member"
                            : "Guest workspace"}
                        <small>
                            {identity.data && !identity.isError
                                ? identity.data.role
                                : "Connect to get started"}
                        </small>
                    </span>
                    {identity.data && !identity.isError && (
                        <button
                            className="icon-button"
                            aria-label="Disconnect workspace"
                            onClick={clear}
                        >
                            <SignOut size={21} />
                        </button>
                    )}
                </div>
                <button
                    ref={menu}
                    className="icon-button menu-toggle"
                    aria-label="Workspace menu"
                    aria-expanded={open}
                    aria-controls="workspace-navigation"
                    onClick={() => setOpen(!open)}
                >
                    <List size={23} />
                </button>
            </header>
            <aside
                id="workspace-navigation"
                className={`sidebar ${open ? "is-open" : ""}`}
            >
                <p className="nav-caption">WORKSPACE</p>
                <nav aria-label="Workspace pages">
                    {routes
                        .filter((route) =>
                            route.name
                                .toLowerCase()
                                .includes(search.toLowerCase()),
                        )
                        .map(({ path, name, icon: Icon }) => (
                            <NavLink
                                key={path}
                                to={path}
                                onClick={() => {
                                    setOpen(false);
                                    setSearch("");
                                }}
                            >
                                <Icon size={21} aria-hidden="true" />
                                <span>{name}</span>
                            </NavLink>
                        ))}
                    {!routes.some((route) =>
                        route.name.toLowerCase().includes(search.toLowerCase()),
                    ) && <output className="muted">No matching pages.</output>}
                </nav>
                <div className="sidebar-bottom">
                    <div className="sidebar-note">
                        <LockKey size={23} aria-hidden="true" />
                        <strong>Your data, under your control</strong>
                        <p>
                            Access is verified by your local API. Disconnect
                            when you finish.
                        </p>
                    </div>
                    <a className="legacy-link" href="/review-ui/">
                        Open review workspace
                        <ArrowSquareOut size={17} aria-hidden="true" />
                    </a>
                </div>
            </aside>
            <main ref={heading} tabIndex={-1} id="main">
                <div className="breadcrumb">
                    Workspace <span>/</span> {title}
                </div>
                <Outlet />
            </main>
        </div>
    );
}

function RequireIdentity() {
    const { identity, tokenPresent } = useSession();
    const location = useLocation();
    if (!tokenPresent)
        return (
            <Navigate
                to="/connect"
                state={{ from: location.pathname + location.search }}
                replace
            />
        );
    if (identity.isPending)
        return (
            <output className="panel empty-state">
                Verifying workspace access…
            </output>
        );
    if (identity.isError) return <ConnectPage />;
    return (
        <DataBoundary>
            <Outlet />
        </DataBoundary>
    );
}

function FeaturePage({
    path,
    name,
    description,
}: {
    path: string;
    name: string;
    description: string;
}) {
    const page =
        path === "/overview" ? (
            <DashboardPage />
        ) : path === "/calls" ? (
            <CallsPage />
        ) : path === "/live" ? (
            <LivePage />
        ) : path === "/models" ? (
            <ModelsPage />
        ) : path === "/qa" ? (
            <ReportWorkspace kind="qa" />
        ) : path === "/emotion" ? (
            <ReportWorkspace kind="emotion" />
        ) : path === "/knowledge" ? (
            <ReportWorkspace kind="knowledge" />
        ) : path === "/coaching" ? (
            <ReportWorkspace kind="coaching" />
        ) : (
            <WorkspacePage name={name} description={description} />
        );
    return <Suspense fallback={<Pending />}>{page}</Suspense>;
}

function ConnectPage() {
    const { identity, connect, tokenPresent, clear } = useSession();
    const [credential, setCredential] = useState("");
    const location = useLocation();
    const from = (location.state as { from?: string } | null)?.from;
    const destination = typeof from === "string" ? from.split("?")[0] : "";
    if (identity.data && !identity.isError && !identity.isFetching)
        return (
            <Navigate
                to={
                    routes.some(
                        (route) =>
                            (route.path === destination &&
                                destination !== "/health") ||
                            /^\/(?:calls|reviews)\/[0-9a-f-]{36}$/i.test(
                                destination || "",
                            ),
                    )
                        ? from!
                        : "/overview"
                }
                replace
            />
        );
    function submit(event: FormEvent) {
        event.preventDefault();
        if (!credential.trim() || credential.length > 16384) return;
        connect(credential);
        setCredential("");
    }
    return (
        <>
            <PageHeading
                eyebrow="WORKSPACE ACCESS"
                title="A secure start to your day."
                description="Connect with an enabled workspace identity to continue."
            />
            <section className="panel connect-panel">
                <div className="feature-icon">
                    <LockKey size={28} aria-hidden="true" />
                </div>
                <h2>Connect to your workspace</h2>
                <p className="muted">
                    Use a short-lived access token issued for this API. Your
                    administrator can help you get access.
                </p>
                <form onSubmit={submit}>
                    <label htmlFor="access-token">Workspace access token</label>
                    <input
                        id="access-token"
                        type="password"
                        autoComplete="off"
                        spellCheck={false}
                        maxLength={16384}
                        required
                        value={credential}
                        onChange={(event) => setCredential(event.target.value)}
                    />
                    <p className="field-hint">
                        Kept in this tab's memory. Reloading or disconnecting
                        clears access.
                    </p>
                    <button
                        className="button"
                        disabled={identity.isFetching || !credential.trim()}
                    >
                        Connect securely
                        <ArrowRight size={18} aria-hidden="true" />
                    </button>
                </form>
                {identity.isFetching && (
                    <output>Verifying workspace access…</output>
                )}
                {identity.isError && (
                    <p role="alert" className="error-message">
                        {identity.error.message}
                    </p>
                )}
                {tokenPresent && (
                    <button className="text-button" onClick={clear}>
                        Clear workspace access
                    </button>
                )}
                <div className="notice">
                    <strong>Access unavailable?</strong>
                    <p>
                        The API needs a configured identity provider and an
                        enabled account. There is no guest access to protected
                        data.
                    </p>
                </div>
            </section>
        </>
    );
}

function PageHeading({
    eyebrow,
    title,
    description,
}: {
    eyebrow: string;
    title: string;
    description: string;
}) {
    return (
        <div className="page-heading">
            <p className="eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
            <p>{description}</p>
        </div>
    );
}

function HealthPage() {
    const live = useQuery({
        queryKey: ["health"],
        queryFn: ({ signal }) => getHealth("/health", signal),
        retry: false,
        staleTime: 15000,
    });
    const ready = useQuery({
        queryKey: ["ready"],
        queryFn: ({ signal }) => getHealth("/ready", signal),
        retry: false,
        staleTime: 15000,
    });
    const { identity } = useSession();
    return (
        <>
            <PageHeading
                eyebrow="SYSTEM HEALTH"
                title="A clear view of your workspace."
                description="Check the services behind your call center before getting to work."
            />
            <div className="status-grid">
                <StatusCard
                    title="API connection"
                    value={
                        live.isPending
                            ? "Checking…"
                            : live.isError
                              ? "Unavailable"
                              : "Connected"
                    }
                    detail={
                        live.isError
                            ? live.error.message
                            : "Local service · /health"
                    }
                    good={live.isSuccess}
                    pending={live.isPending}
                />
                <StatusCard
                    title="Service readiness"
                    value={
                        ready.isPending
                            ? "Checking…"
                            : ready.isError
                              ? "Needs attention"
                              : "Ready"
                    }
                    detail={
                        ready.isError
                            ? ready.error.message
                            : "Database and identity configuration"
                    }
                    good={ready.isSuccess}
                    pending={ready.isPending}
                />
                <StatusCard
                    title="Workspace access"
                    value={
                        identity.data && !identity.isError
                            ? "Verified"
                            : "Not connected"
                    }
                    detail={
                        identity.data && !identity.isError
                            ? `Enabled ${identity.data.role} account`
                            : "Connect to open protected pages"
                    }
                    good={Boolean(identity.data) && !identity.isError}
                    pending={false}
                />
            </div>
            <div className="health-grid">
                <section className="panel service-panel">
                    <div className="section-title">
                        <div>
                            <p className="eyebrow">LOCAL SERVICES</p>
                            <h2>Connection details</h2>
                        </div>
                        <button
                            className="secondary-button"
                            disabled={live.isFetching || ready.isFetching}
                            onClick={() => {
                                void live.refetch();
                                void ready.refetch();
                            }}
                        >
                            Check again
                        </button>
                    </div>
                    <div className="table-scroll">
                        <table>
                            <caption className="sr-only">
                                Current API checks
                            </caption>
                            <thead>
                                <tr>
                                    <th scope="col">Service</th>
                                    <th scope="col">Endpoint</th>
                                    <th scope="col">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <th scope="row">API liveness</th>
                                    <td>
                                        <code>/health</code>
                                    </td>
                                    <td>
                                        <span
                                            className={`pill ${live.isSuccess ? "positive" : "caution"}`}
                                        >
                                            {live.isPending
                                                ? "Checking"
                                                : live.isError
                                                  ? "Unavailable"
                                                  : "Connected"}
                                        </span>
                                    </td>
                                </tr>
                                <tr>
                                    <th scope="row">API readiness</th>
                                    <td>
                                        <code>/ready</code>
                                    </td>
                                    <td>
                                        <span
                                            className={`pill ${ready.isSuccess ? "positive" : "caution"}`}
                                        >
                                            {ready.isPending
                                                ? "Checking"
                                                : ready.isError
                                                  ? "Not ready"
                                                  : "Ready"}
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <output className="field-hint">
                        {live.isFetching || ready.isFetching
                            ? "Checking local services…"
                            : live.dataUpdatedAt
                              ? `Liveness last checked ${new Date(live.dataUpdatedAt).toLocaleTimeString()}. These checks do not measure model accuracy.`
                              : "No successful liveness check yet."}
                    </output>
                </section>
                <section className="panel welcome-panel">
                    <span className="feature-icon">
                        <SquaresFour size={26} aria-hidden="true" />
                    </span>
                    <p className="eyebrow">
                        YOUR NEXT CONVERSATION STARTS HERE
                    </p>
                    <h2>Everything in one workspace.</h2>
                    <p>
                        Calls, live monitoring, knowledge and model tools will
                        share this home as they become available.
                    </p>
                    <Link className="button" to="/overview">
                        Open workspace
                        <ArrowRight size={18} aria-hidden="true" />
                    </Link>
                </section>
            </div>
            <section className="panel footnote">
                <CheckCircle size={24} aria-hidden="true" />
                <div>
                    <h2>Built around careful review</h2>
                    <p>
                        Darija transcription and emotion predictions still
                        require human review. System readiness does not certify
                        model quality.
                    </p>
                </div>
                <a className="secondary-button" href="/review-ui/">
                    Go to review
                    <ArrowSquareOut size={16} aria-hidden="true" />
                </a>
            </section>
        </>
    );
}

function StatusCard({
    title,
    value,
    detail,
    good,
    pending,
}: {
    title: string;
    value: string;
    detail: string;
    good: boolean;
    pending: boolean;
}) {
    return (
        <section className="panel status-card" aria-live="polite">
            <div className={`status-symbol ${good ? "positive" : "neutral"}`}>
                {good ? (
                    <CheckCircle size={23} aria-hidden="true" />
                ) : (
                    <WarningCircle size={23} aria-hidden="true" />
                )}
            </div>
            <h2>{title}</h2>
            <p className={`status-value ${pending ? "opacity-60" : ""}`}>
                {value}
            </p>
            <p className="muted">{detail}</p>
        </section>
    );
}

function WorkspacePage({
    name,
    description,
}: {
    name: string;
    description: string;
}) {
    return (
        <>
            <PageHeading
                eyebrow="YOUR WORKSPACE"
                title={name}
                description={description}
            />
            <section className="panel empty-state">
                <span className="feature-icon">
                    <SquaresFour size={30} aria-hidden="true" />
                </span>
                <span className="pill neutral">Workspace foundation</span>
                <h2>This workspace is taking shape.</h2>
                <p>
                    Your access has been verified. This page is reserved for the
                    next implementation steps; no call data or model results are
                    loaded here yet.
                </p>
                <div className="empty-actions">
                    <Link className="button" to="/health">
                        Check system health
                        <ArrowRight size={17} aria-hidden="true" />
                    </Link>
                    <a className="secondary-button" href="/review-ui/">
                        Open existing review
                    </a>
                </div>
            </section>
        </>
    );
}
