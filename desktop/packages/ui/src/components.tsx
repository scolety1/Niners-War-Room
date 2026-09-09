import { getCurrentWindow } from "@tauri-apps/api/window";
import type { CommandItem, DesktopMode, HealthTone, NavigationGroup } from "@nwr/contracts";
import type { CSSProperties, ErrorInfo, ReactNode, Ref } from "react";
import { Component, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { stableSortRows } from "./table-sort";
import type { TableSortDirection, TableSortKind } from "./table-sort";

type IconName = "activity" | "alert" | "board" | "check" | "chevron" | "close" |
  "command" | "compare" | "draft" | "health" | "home" | "layers" | "market" |
  "maximize" | "minimize" | "players" | "profile" | "rookie" | "search" |
  "settings" | "shield" | "target" | "trade" | "trophy" | "undo";

const ICON_PATHS: Record<IconName, ReactNode> = {
  activity: <path d="M3 12h4l2.2-6 4.1 12 2.2-6H21" />,
  alert: <><path d="M12 3 2.7 20h18.6L12 3Z" /><path d="M12 9v4.5M12 17h.01" /></>,
  board: <><rect x="4" y="3" width="16" height="18" rx="2" /><path d="M8 8h8M8 12h8M8 16h5" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  chevron: <path d="m9 18 6-6-6-6" />,
  close: <path d="m7 7 10 10M17 7 7 17" />,
  command: <path d="M9 6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6Z" />,
  compare: <><path d="M8 3 4 7l4 4M4 7h13M16 21l4-4-4-4M20 17H7" /></>,
  draft: <><path d="M4 19 15 8l4 4L8 23H4v-4Z" /><path d="m13 10 4 4M5 5h5M5 9h3" /></>,
  health: <><path d="M12 21s-7-4.4-7-11a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 6.6-7 11-7 11Z" /><path d="M8 13h2l1-3 2 6 1-3h2" /></>,
  home: <><path d="m3 11 9-8 9 8" /><path d="M5 10v11h14V10M9 21v-7h6v7" /></>,
  layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 12 9 5 9-5M3 16l9 5 9-5" /></>,
  market: <><path d="M4 19V9M10 19V5M16 19v-7M22 19H2" /><path d="m4 6 5-3 6 4 5-4" /></>,
  maximize: <rect x="5" y="5" width="14" height="14" rx="1" />,
  minimize: <path d="M5 12h14" />,
  players: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></>,
  profile: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
  rookie: <path d="m12 2 3 6 6.5 1-4.7 4.6 1.1 6.4-5.9-3.1L6.1 20l1.1-6.4L2.5 9 9 8l3-6Z" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.8 1.8 0 0 0 .4 2l.1.1-2.8 2.8-.1-.1a1.8 1.8 0 0 0-2-.4 1.8 1.8 0 0 0-1 1.6v.2h-4V21a1.8 1.8 0 0 0-1-1.6 1.8 1.8 0 0 0-2 .4l-.1.1-2.8-2.8.1-.1a1.8 1.8 0 0 0 .4-2A1.8 1.8 0 0 0 3 14H2.8v-4H3a1.8 1.8 0 0 0 1.6-1 1.8 1.8 0 0 0-.4-2l-.1-.1 2.8-2.8.1.1a1.8 1.8 0 0 0 2 .4A1.8 1.8 0 0 0 10 3V2.8h4V3a1.8 1.8 0 0 0 1 1.6 1.8 1.8 0 0 0 2-.4l.1-.1 2.8 2.8-.1.1a1.8 1.8 0 0 0-.4 2 1.8 1.8 0 0 0 1.6 1h.2v4H21a1.8 1.8 0 0 0-1.6 1Z" /></>,
  shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" /><path d="m9 12 2 2 4-4" /></>,
  target: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></>,
  trade: <><path d="M7 7h11l-3-3M17 17H6l3 3" /><path d="m18 7-3 3M6 17l3-3" /></>,
  trophy: <><path d="M8 4h8v5a4 4 0 0 1-8 0V4Z" /><path d="M8 6H4v2a4 4 0 0 0 4 4M16 6h4v2a4 4 0 0 1-4 4M12 13v5M8 21h8M10 18h4" /></>,
  undo: <><path d="m9 7-5 5 5 5" /><path d="M20 17a7 7 0 0 0-7-7H4" /></>,
};

export function Icon({ name, size = 18 }: { name: string; size?: number }) {
  return <svg aria-hidden="true" className="nwr-icon" fill="none" height={size} viewBox="0 0 24 24" width={size} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7">{ICON_PATHS[name as IconName] ?? ICON_PATHS.activity}</svg>;
}

function isTauri() { return "__TAURI_INTERNALS__" in window; }
async function windowAction(action: "minimize" | "toggleMaximize" | "close") {
  if (!isTauri()) return;
  await getCurrentWindow()[action]();
}

export function WindowChrome({ title }: { title: string }) {
  return <div className="window-chrome" data-tauri-drag-region>
    <div className="window-chrome__mark" data-tauri-drag-region><span className="window-chrome__monogram">NWR</span><span>{title}</span></div>
    <div className="window-chrome__controls">
      <button aria-label="Minimize window" onClick={() => void windowAction("minimize")}><Icon name="minimize" size={15} /></button>
      <button aria-label="Maximize window" onClick={() => void windowAction("toggleMaximize")}><Icon name="maximize" size={14} /></button>
      <button aria-label="Close window" className="window-chrome__close" onClick={() => void windowAction("close")}><Icon name="close" size={15} /></button>
    </div>
  </div>;
}

interface AppShellProps {
  mode: DesktopMode;
  title: string;
  contextLabel: string;
  navigation: NavigationGroup[];
  commands: CommandItem[];
  sourceAsOf: string;
  healthTone: HealthTone;
  healthLabel: string;
  profileLabel: string;
  children: ReactNode;
  // Global sidebar collapse -- proven absent before this addition (no prior
  // AppShell caller had any way to narrow the always-full-width global
  // nav). Both props are optional and default to "not collapsed, no
  // toggle rendered" so every existing caller (Dynasty, and every Redraft
  // page besides Draft Room) renders byte-for-byte as before; only a
  // caller that explicitly wants the affordance (Draft Room, for maximum
  // horizontal room during a live draft) passes them.
  sidebarCollapsed?: boolean;
  onToggleSidebarCollapsed?: () => void;
}

export function AppShell(props: AppShellProps) {
  const { mode, title, contextLabel, navigation, commands, sourceAsOf, healthTone, healthLabel, profileLabel, children, sidebarCollapsed = false, onToggleSidebarCollapsed } = props;
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const commandTrigger = useRef<HTMLButtonElement>(null);
  const content = useRef<HTMLElement>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const closePalette = () => { setPaletteOpen(false); window.setTimeout(() => commandTrigger.current?.focus(), 0); };
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); if (paletteOpen) closePalette(); else setPaletteOpen(true); }
      if (event.key === "Escape" && paletteOpen) closePalette();
      if (!event.ctrlKey && !event.metaKey && !event.altKey && !event.shiftKey && !paletteOpen && !/INPUT|SELECT|TEXTAREA/.test((event.target as HTMLElement)?.tagName ?? "")) {
        const item = navigation.flatMap((group) => group.items).find((candidate) => candidate.shortcut === event.key);
        if (item) { event.preventDefault(); navigate(item.path); }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navigate, navigation, paletteOpen]);
  useLayoutEffect(() => {
    content.current?.scrollTo({ behavior: "auto", left: 0, top: 0 });
  }, [location.pathname, location.search]);
  useEffect(() => setMobileNavOpen(false), [location.pathname]);
  return <div className={`app-frame app-frame--${mode} ${sidebarCollapsed ? "app-frame--sidebar-collapsed" : ""}`}>
    <WindowChrome title={title} />
    <div aria-hidden={paletteOpen ? true : undefined} className="app-frame__body" inert={paletteOpen ? true : undefined}>
      <aside className={`sidebar ${mobileNavOpen ? "sidebar--open" : ""} ${sidebarCollapsed ? "sidebar--collapsed" : ""}`}>
        {onToggleSidebarCollapsed ? (
          <button
            aria-expanded={!sidebarCollapsed}
            aria-label={sidebarCollapsed ? "Expand navigation" : "Collapse navigation"}
            className="sidebar__collapse-toggle"
            onClick={onToggleSidebarCollapsed}
            title={sidebarCollapsed ? "Expand navigation" : "Collapse navigation"}
          >
            <Icon name="chevron" size={13} />
          </button>
        ) : null}
        <div className="brand-lockup"><div className="brand-lockup__crest" aria-hidden="true"><span>SF</span><i /></div><div><strong>Niners War Room</strong><span>{mode}</span></div></div>
        <div className="mode-ribbon"><i /><span>{contextLabel}</span></div>
        <nav aria-label={`${title} navigation`} className="sidebar__nav">
          {navigation.map((group) => <div className="nav-group" key={group.label}><span className="nav-group__label">{group.label}</span>{group.items.map((item) => <NavLink className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`} key={item.path} title={sidebarCollapsed ? item.label : undefined} to={item.path}><Icon name={item.icon} size={17} /><span>{item.label}</span>{item.shortcut ? <kbd>{item.shortcut}</kbd> : null}<Icon name="chevron" size={13} /></NavLink>)}</div>)}
        </nav>
        <div className="sidebar__footer"><div className="profile-chip"><div className="profile-chip__avatar">GM</div><div><span>Active context</span><strong>{profileLabel}</strong></div></div><div className="local-lock"><Icon name="shield" size={14} /> Local only · protected session</div></div>
      </aside>
      <button aria-label="Close navigation" className={`sidebar-scrim ${mobileNavOpen ? "sidebar-scrim--visible" : ""}`} onClick={() => setMobileNavOpen(false)} />
      <section className="workspace"><header className="status-bar"><button aria-label="Open navigation" className="mobile-nav-trigger" onClick={() => setMobileNavOpen(true)}><Icon name="layers" /></button><button aria-expanded={paletteOpen} aria-haspopup="dialog" className="command-trigger" onClick={() => setPaletteOpen(true)} ref={commandTrigger}><Icon name="search" size={16} /><span>Search players or jump to a tool</span><kbd>Ctrl K</kbd></button><div className="status-bar__signals"><StatusBadge tone={healthTone} label={healthLabel} pulse /><span className="source-clock"><Icon name="activity" size={14} />{sourceAsOf || "Source date unavailable"}</span></div></header><main className="workspace__content" id="main-content" ref={content}>{children}</main></section>
    </div>
    <CommandPalette commands={commands} onClose={closePalette} open={paletteOpen} />
  </div>;
}

export function normalizeCommandSearch(value: unknown): string {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

export function filterCommandItems(commands: CommandItem[], query: string): CommandItem[] {
  const needle = normalizeCommandSearch(query.trim());
  if (!needle) return commands.slice(0, 10);
  return commands
    .filter((command) => normalizeCommandSearch(
      [command.label, command.detail, ...(command.keywords ?? [])].join(" "),
    ).includes(needle))
    .slice(0, 12);
}

function CommandPalette({ commands, open, onClose }: { commands: CommandItem[]; open: boolean; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const navigate = useNavigate();
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => { if (open) { setQuery(""); setActiveIndex(0); window.setTimeout(() => input.current?.focus(), 20); } }, [open]);
  const results = useMemo(() => filterCommandItems(commands, query), [commands, query]);
  const openResult = (index: number) => { const command = results[index]; if (command) { navigate(command.path); onClose(); } };
  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") { event.preventDefault(); setActiveIndex((value) => results.length ? (value + 1) % results.length : 0); }
    if (event.key === "ArrowUp") { event.preventDefault(); setActiveIndex((value) => results.length ? (value - 1 + results.length) % results.length : 0); }
    if (event.key === "Enter") { event.preventDefault(); openResult(activeIndex); }
    if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); onClose(); }
  };
  useEffect(() => {
    if (!open) return;
    const trapFocus = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const dialog = input.current?.closest<HTMLElement>(".command-palette");
      const focusable = Array.from(
        dialog?.querySelectorAll<HTMLElement>(
          'input:not(:disabled), button:not(:disabled), [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      );
      if (!focusable.length) return;
      const first = focusable[0]!;
      const last = focusable.at(-1)!;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", trapFocus);
    return () => window.removeEventListener("keydown", trapFocus);
  }, [open, results.length]);
  if (!open) return null;
  return <div className="palette-backdrop" onMouseDown={onClose} role="presentation"><section aria-label="Command palette" aria-modal="true" className="command-palette" onMouseDown={(event) => event.stopPropagation()} role="dialog"><div className="command-palette__search"><Icon name="search" /><input aria-activedescendant={results[activeIndex] ? `command-result-${activeIndex}` : undefined} aria-controls="command-results" aria-label="Search commands" onChange={(event) => { setQuery(event.target.value); setActiveIndex(0); }} onKeyDown={onKeyDown} placeholder="Search players, boards, decisions…" ref={input} value={query} /><kbd>Esc</kbd></div><div className="command-palette__results" id="command-results" role="listbox"><span className="command-palette__label">Best matches</span>{results.map((command, index) => <button aria-selected={activeIndex === index} className={activeIndex === index ? "command-palette__result--active" : ""} id={`command-result-${index}`} key={command.id} onClick={() => openResult(index)} onMouseEnter={() => setActiveIndex(index)} role="option"><span className="command-palette__icon"><Icon name={command.icon} /></span><span><strong>{command.label}</strong><small>{command.detail}</small></span><Icon name="chevron" size={14} /></button>)}{!results.length ? <div className="command-palette__empty">No matching action</div> : null}</div><footer><span><kbd>↑</kbd><kbd>↓</kbd> Navigate</span><span><kbd>↵</kbd> Open</span></footer></section></div>;
}

export function PageHeader({ eyebrow, title, description, actions, status }: { eyebrow: string; title: string; description: string; actions?: ReactNode; status?: ReactNode }) {
  return <header className="page-header"><div><div className="page-header__eyebrow"><span />{eyebrow}</div><h1>{title}</h1><p>{description}</p>{status ? <div className="page-header__status">{status}</div> : null}</div>{actions ? <div className="page-header__actions">{actions}</div> : null}</header>;
}
export function StatusBadge({ tone, label, pulse = false }: { tone: HealthTone | "safe" | "deprioritized"; label: string; pulse?: boolean }) { return <span className={`status-badge status-badge--${tone}`}><i className={pulse ? "pulse" : ""} />{label}</span>; }
export function Panel({ title, eyebrow, action, children, className = "" }: { title?: string; eyebrow?: string; action?: ReactNode; children: ReactNode; className?: string }) { return <section className={`panel ${className}`}>{title || eyebrow || action ? <header className="panel__header"><div>{eyebrow ? <span>{eyebrow}</span> : null}{title ? <h2>{title}</h2> : null}</div>{action}</header> : null}<div className="panel__body">{children}</div></section>; }
export function MetricCard({ label, value, detail, trend, icon, tone = "violet" }: { label: string; value: ReactNode; detail: string; trend?: string; icon: string; tone?: "violet" | "crimson" | "gold" | "cyan" }) { return <article className={`metric-card metric-card--${tone}`}><div className="metric-card__icon"><Icon name={icon} size={19} /></div><span className="metric-card__label">{label}</span><strong className="metric-card__value">{value}</strong><div className="metric-card__detail"><span>{detail}</span>{trend ? <b>{trend}</b> : null}</div></article>; }
export function ActionCard({ icon, title, description, meta, onClick }: { icon: string; title: string; description: string; meta: string; onClick: () => void }) { return <button className="action-card" onClick={onClick}><span className="action-card__icon"><Icon name={icon} /></span><span><strong>{title}</strong><small>{description}</small><em>{meta}</em></span><Icon name="chevron" size={15} /></button>; }
export function Button({ children, variant = "primary", icon, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger"; icon?: string }) { return <button {...props} className={`button button--${variant} ${className ?? ""}`}>{icon ? <Icon name={icon} size={16} /> : null}{children}</button>; }
export function SearchInput({ value, onChange, placeholder = "Search players…", inputRef }: { value: string; onChange: (value: string) => void; placeholder?: string; inputRef?: Ref<HTMLInputElement> }) { return <label className="search-input"><Icon name="search" size={16} /><input aria-label={placeholder.replace(/…$/, "")} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} ref={inputRef} type="search" value={value} /></label>; }
export function SelectField({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: Array<{ value: string; label: string }> }) { return <label className="select-field"><span>{label}</span><select onChange={(event) => onChange(event.target.value)} value={value}>{options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>; }
export function SegmentedControl({ label, options, value, onChange }: { label: string; options: string[]; value: string; onChange: (value: string) => void }) { return <fieldset className="segmented"><legend>{label}</legend>{options.map((option) => <button aria-pressed={value === option} className={value === option ? "segmented--active" : ""} key={option} onClick={() => onChange(option)} type="button">{option}</button>)}</fieldset>; }
export interface TableColumn {
  key: string;
  label: string;
  // Optional header hover text -- lets a compact column label ("Pick
  // Score") carry a longer provenance/evidence note ("EXPERIMENTAL...")
  // without that note living in the visible chrome. Purely additive;
  // every existing column omits it and renders exactly as before.
  titleHint?: string;
  align?: "left" | "right" | "center";
  width?: string;
  render?: (row: Record<string, unknown>) => ReactNode;
  sort?: TableSortKind;
  sortValue?: (row: Record<string, unknown>) => unknown;
}
export function DataTable({
  columns,
  rows,
  rowKey,
  onRowClick,
  emptyMessage = "No rows match this view.",
  resetKey,
}: {
  columns: TableColumn[];
  rows: Array<Record<string, unknown>>;
  rowKey: (row: Record<string, unknown>) => string;
  onRowClick?: (row: Record<string, unknown>) => void;
  emptyMessage?: string;
  resetKey?: string | number;
}) {
  const [sort, setSort] = useState<{ key: string; direction: TableSortDirection } | null>(null);
  useEffect(() => setSort(null), [resetKey]);
  const activeColumn = sort ? columns.find((column) => column.key === sort.key && column.sort) : undefined;
  const displayedRows = useMemo(() => {
    if (!sort || !activeColumn?.sort) return rows;
    return stableSortRows(
      rows,
      (row) => activeColumn.sortValue ? activeColumn.sortValue(row) : row[activeColumn.key],
      activeColumn.sort,
      sort.direction,
    );
  }, [activeColumn, rows, sort]);
  const toggleSort = (column: TableColumn) => {
    if (!column.sort) return;
    setSort((current) => current?.key === column.key
      ? { key: column.key, direction: current.direction === "ascending" ? "descending" : "ascending" }
      : { key: column.key, direction: "ascending" });
  };
  return <div className="data-table-wrap"><table className="data-table"><thead><tr>{columns.map((column) => {
    const direction = sort?.key === column.key ? sort.direction : undefined;
    return <th aria-sort={column.sort ? direction ?? "none" : undefined} key={column.key} scope="col" style={{ textAlign: column.align ?? "left", width: column.width }} title={column.titleHint}>{column.sort ? <button className="data-table__sort" onClick={() => toggleSort(column)} type="button"><span>{column.label}</span><span aria-hidden="true">{direction === "ascending" ? "▲" : direction === "descending" ? "▼" : "↕"}</span></button> : column.label}</th>;
  })}</tr></thead><tbody>{displayedRows.map((row) => <tr className={onRowClick ? "data-table__clickable" : ""} key={rowKey(row)} onClick={() => onRowClick?.(row)} onKeyDown={(event) => { if (onRowClick && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); onRowClick(row); } }} role={onRowClick ? "link" : undefined} tabIndex={onRowClick ? 0 : undefined}>{columns.map((column) => <td key={column.key} style={{ textAlign: column.align ?? "left" }}>{column.render ? column.render(row) : String(row[column.key] ?? "—")}</td>)}</tr>)}</tbody></table>{!displayedRows.length ? <div className="data-table__empty">{emptyMessage}</div> : null}</div>;
}
export function ProgressBar({ value, max = 100, tone = "violet" }: { value: number; max?: number; tone?: "violet" | "crimson" | "gold" | "cyan" }) { const width = Math.max(0, Math.min(100, (value / max) * 100)); return <span aria-label={`${Math.round(width)} percent`} aria-valuemax={max} aria-valuemin={0} aria-valuenow={Math.max(0, Math.min(max, value))} className={`progress progress--${tone}`} role="progressbar"><i style={{ "--progress": `${width}%` } as CSSProperties} /></span>; }
export function EmptyState({ icon = "alert", title, message, action }: { icon?: string; title: string; message: string; action?: ReactNode }) { return <div className="empty-state"><span><Icon name={icon} size={26} /></span><h2>{title}</h2><p>{message}</p>{action}</div>; }
export function LoadingScreen({ label = "Synchronizing governed evidence" }: { label?: string }) { return <div className="loading-screen"><div className="loading-orbit"><span>NWR</span></div><strong>{label}</strong><small>Local analytical services · no cloud connection</small></div>; }
export function ErrorState({ title = "Command center unavailable", message, recovery, onRetry }: { title?: string | undefined; message: string; recovery?: string | undefined; onRetry?: (() => void) | undefined }) { return <div className="error-state"><span><Icon name="alert" size={28} /></span><div><h2>{title}</h2><p>{message}</p>{recovery ? <small>{recovery}</small> : null}</div>{onRetry ? <Button onClick={onRetry} variant="secondary" icon="undo">Retry</Button> : null}</div>; }

export class OwnerErrorBoundary extends Component<
  { children: ReactNode; mode: DesktopMode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() { return { failed: true }; }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[NWR ${this.props.mode} display error]`, error, info.componentStack);
  }

  private retry = () => window.location.reload();

  render() {
    if (!this.state.failed) return this.props.children;
    const modeLabel = this.props.mode === "dynasty" ? "Dynasty" : "Redraft";
    return <div className="standalone-frame"><WindowChrome title={`Niners War Room — ${modeLabel}`} /><div className="standalone-state"><ErrorState title={`${modeLabel} display needs a restart`} message="A display problem was stopped before it could affect local NWR data." recovery="Restart this window. Your saved local work remains protected." onRetry={this.retry} /></div></div>;
  }
}
export function FieldLabel({ children }: { children: ReactNode }) { return <span className="field-label">{children}</span>; }
export function formatNumber(value: number | null | undefined, digits = 0): string { if (value === null || value === undefined || Number.isNaN(value)) return "—"; return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value); }
export function classNames(...values: Array<string | false | null | undefined>): string { return values.filter(Boolean).join(" "); }
