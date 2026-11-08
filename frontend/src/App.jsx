import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

const menuItems = [
  { name: "Dashboard", icon: "▦" },
  { name: "Production Schedule", icon: "▤" },
  { name: "Production Orders", icon: "▣", endpoint: "/api/production-orders" },
  { name: "Products", icon: "◇", endpoint: "/api/products" },
  { name: "Machines", icon: "⚙", endpoint: "/api/machines" },
  { name: "Machine Calendars", icon: "📅", endpoint: "/api/machine-calendars" },
  { name: "Materials", icon: "▤", endpoint: "/api/materials" },
  { name: "Inventory Lots", icon: "📦", endpoint: "/api/inventory-lots" },
  { name: "Routings", icon: "↗", endpoint: "/api/routings" },
  { name: "Changeovers", icon: "⇄", endpoint: "/api/changeovers" },
  { name: "Labor Shifts", icon: "👥", endpoint: "/api/labor-shifts" },
  { name: "Tools & Equipment", icon: "⚒", endpoint: "/api/tools" },
  { name: "Exceptions & Anomalies", icon: "⚠" },
];

function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [backendReady, setBackendReady] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const selectedMenu = menuItems.find(
    (item) => item.name === activePage
  );

  useEffect(() => {
    const checkBackend = () => {
      fetch(`${API}/health`)
        .then((response) => {
          if (!response.ok) throw new Error("Backend unavailable");
          return response.json();
        })
        .then(() => setBackendReady(true))
        .catch(() => setBackendReady(false));
    };

    checkBackend();
    const interval = setInterval(checkBackend, 15000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedMenu?.endpoint) {
      setData([]);
      setError("");
      return;
    }

    setLoading(true);
    setError("");

    fetch(`${API}${selectedMenu.endpoint}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Unable to load ${activePage.toLowerCase()}`);
        }
        return response.json();
      })
      .then((result) => {
        setData(Array.isArray(result) ? result : []);
      })
      .catch((err) => {
        setError(err.message);
        setData([]);
      })
      .finally(() => setLoading(false));
  }, [activePage, refreshKey]);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">Y</div>
          <div>
            <h2>
              YottaFlex<span>.ai</span>
            </h2>
            <small>MANUFACTURING SYSTEM</small>
          </div>
        </div>

        <div className="menu-label">WORKSPACE</div>

        <nav>
          {menuItems.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${
                activePage === item.name ? "active" : ""
              }`}
              onClick={() => setActivePage(item.name)}
            >
              <span>{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <span
            className="status-dot"
            style={{
              background: backendReady ? "#35c98b" : "#e0a33d",
            }}
          />
          {backendReady ? "Backend connected" : "Backend disconnected"}
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              Workspace / {activePage}
            </div>
            <h1>{activePage}</h1>
          </div>

          <div className="top-actions">
            <span className="system-status">
              <span
                className="status-dot"
                style={{
                  background: backendReady ? "#35c98b" : "#e0a33d",
                }}
              />
              {backendReady ? "System ready" : "Connection pending"}
            </span>
            <div className="avatar">Y</div>
          </div>
        </header>

        {activePage === "Dashboard" ? (
          <Dashboard
            onNavigate={setActivePage}
            refreshKey={refreshKey}
            onRefresh={() => setRefreshKey((k) => k + 1)}
          />
        ) : activePage === "Production Schedule" ? (
          <SchedulePage
            refreshKey={refreshKey}
            onRefresh={() => setRefreshKey((k) => k + 1)}
          />
        ) : activePage === "Exceptions & Anomalies" || activePage === "Exceptions" ? (
          <ExceptionsPage
            refreshKey={refreshKey}
            onRefresh={() => setRefreshKey((k) => k + 1)}
          />
        ) : selectedMenu?.endpoint ? (
          <DataPage
            key={activePage}
            title={activePage}
            data={data}
            loading={loading}
            error={error}
            onRefresh={() => setRefreshKey((value) => value + 1)}
          />
        ) : (
          <PagePlaceholder title={activePage} />
        )}
      </main>
    </div>
  );
}

function Dashboard({ onNavigate, refreshKey, onRefresh }) {
  const [metrics, setMetrics] = useState({
    orders: 0,
    products: 0,
    machines: 0,
    materials: 0,
  });

  const [evalMetrics, setEvalMetrics] = useState(null);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [schedulerRunning, setSchedulerRunning] = useState(false);
  const [scheduleNotice, setScheduleNotice] = useState("");

  useEffect(() => {
    const loadMetrics = async () => {
      setMetricsLoading(true);

      try {
        const endpoints = [
          fetch(`${API}/api/production-orders`).then((r) => r.ok ? r.json() : []),
          fetch(`${API}/api/products`).then((r) => r.ok ? r.json() : []),
          fetch(`${API}/api/machines`).then((r) => r.ok ? r.json() : []),
          fetch(`${API}/api/materials`).then((r) => r.ok ? r.json() : []),
          fetch(`${API}/api/metrics`).then((r) => r.ok ? r.json() : null),
        ];

        const [orders, products, machines, materials, evalData] =
          await Promise.all(endpoints);

        setMetrics({
          orders: Array.isArray(orders) ? orders.length : 0,
          products: Array.isArray(products) ? products.length : 0,
          machines: Array.isArray(machines) ? machines.length : 0,
          materials: Array.isArray(materials) ? materials.length : 0,
        });

        setEvalMetrics(evalData);
      } catch {
        setMetrics({
          orders: 0,
          products: 0,
          machines: 0,
          materials: 0,
        });
      } finally {
        setMetricsLoading(false);
      }
    };

    loadMetrics();
  }, [refreshKey]);

  const handleRunScheduler = async () => {
    setSchedulerRunning(true);
    setScheduleNotice("");
    try {
      const response = await fetch(`${API}/api/schedule/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_orders: 50 }),
      });
      const res = await response.json();
      if (!response.ok) throw new Error(res.detail || "Scheduler execution failed");
      setScheduleNotice(`Schedule ${res.run_summary?.run_code || "RUN"} completed successfully: ${res.run_summary?.scheduled_operations || 0} operations scheduled.`);
      onRefresh();
    } catch (err) {
      setScheduleNotice(`Execution notice: ${err.message}`);
    } finally {
      setSchedulerRunning(false);
    }
  };

  const cards = [
    { label: "Production Orders", value: metrics.orders },
    { label: "Products (SKUs)", value: metrics.products },
    { label: "Active Machines", value: metrics.machines },
    { label: "Raw Materials", value: metrics.materials },
  ];

  return (
    <div className="dashboard">
      <section className="welcome">
        <div>
          <p className="eyebrow">MANUFACTURING OVERVIEW</p>
          <h2>Production at a glance</h2>
          <p>
            Monitor production, evaluate machine constraints, manage resources,
            and generate optimal manufacturing schedules with full traceability.
          </p>
        </div>
        <div className="welcome-symbol">Y</div>
      </section>

      <section className="metrics">
        {cards.map((card) => (
          <div className="metric-card" key={card.label}>
            <div className="metric-top">
              <span>{card.label}</span>
              <span className="metric-number">●</span>
            </div>
            <h2>{metricsLoading ? "..." : card.value}</h2>
            <small>Records in database</small>
          </div>
        ))}
      </section>

      {/* Production Evaluation Metrics Section */}
      <div style={{ margin: "24px 0 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "16px", color: "#e8edf7" }}>Scheduling Performance & Evaluation Metrics</h3>
          <small style={{ color: "#8294aa" }}>Computed from active production schedules ({evalMetrics?.run_code || "Latest Run"})</small>
        </div>
        <button
          className="action-button"
          onClick={handleRunScheduler}
          disabled={schedulerRunning}
        >
          {schedulerRunning ? "Running Engine..." : "▶ Run Scheduler Now"}
        </button>
      </div>

      {scheduleNotice && (
        <div style={{ background: "#1c3450", border: "1px solid #35c98b", padding: "10px 14px", borderRadius: "8px", marginBottom: "16px", fontSize: "12px", color: "#35c98b" }}>
          {scheduleNotice}
        </div>
      )}

      <section className="metrics" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))", marginTop: 0 }}>
        <div className="metric-card">
          <div className="metric-top">
            <span>Makespan</span>
            <span className="metric-number" style={{ color: "#56c9f0" }}>⏱</span>
          </div>
          <h2>{evalMetrics ? `${evalMetrics.makespan_hours}h` : "—"}</h2>
          <small>{evalMetrics ? `Span: ${evalMetrics.makespan_days} days` : "Calculation pending"}</small>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>On-Time Delivery (OTD)</span>
            <span className="metric-number" style={{ color: "#35c98b" }}>✓</span>
          </div>
          <h2>{evalMetrics ? `${evalMetrics.on_time_delivery_pct}%` : "—"}</h2>
          <small>{evalMetrics ? `Late orders: ${evalMetrics.late_orders_count}` : "On-time percentage"}</small>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Machine Utilization</span>
            <span className="metric-number" style={{ color: "#e0a33d" }}>⚙</span>
          </div>
          <h2>{evalMetrics ? `${evalMetrics.machine_utilization_pct}%` : "—"}</h2>
          <small>Plant shift capacity utilized</small>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Schedule Feasibility</span>
            <span className="metric-number" style={{ color: "#35c98b" }}>★</span>
          </div>
          <h2>{evalMetrics ? `${evalMetrics.scheduled_operations}` : "—"}</h2>
          <small>{evalMetrics ? `${evalMetrics.unscheduled_operations} unscheduled operations` : "Feasible operations"}</small>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Total Tardiness</span>
            <span className="metric-number" style={{ color: "#ff5c7c" }}>⚠</span>
          </div>
          <h2>{evalMetrics ? `${evalMetrics.total_tardiness_days}d` : "0d"}</h2>
          <small>Cumulative order delay</small>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Changeover Duration</span>
            <span className="metric-number" style={{ color: "#56c9f0" }}>⇄</span>
          </div>
          <h2>{evalMetrics ? `${evalMetrics.total_changeover_hours}h` : "—"}</h2>
          <small>{evalMetrics ? `${evalMetrics.total_changeover_minutes} mins setup time` : "Sequence-dependent"}</small>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Material Shortages</span>
            <span className="metric-number" style={{ color: "#ff5c7c" }}>!</span>
          </div>
          <h2>{evalMetrics ? evalMetrics.material_shortage_count : 0}</h2>
          <small>Orders held for raw stock</small>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span>Scheduled Orders</span>
            <span className="metric-number" style={{ color: "#35c98b" }}>▣</span>
          </div>
          <h2>{evalMetrics ? evalMetrics.scheduled_orders_count : 0}</h2>
          <small>Active production orders</small>
        </div>
      </section>

      <section className="content-grid" style={{ marginTop: "20px" }}>
        <div className="panel">
          <div className="panel-heading">
            <div>
              <h3>Production Schedule</h3>
              <p>Machine operation allocations and timeline</p>
            </div>
            <span className="tag">SCHEDULING</span>
          </div>

          <div className="empty-state">
            <div className="empty-icon">▤</div>
            <h3>Explore Planned Machine Allocations</h3>
            <p>
              Inspect operation start/end timings, machine routing sequences,
              and sequence-dependent changeovers.
            </p>
            <div style={{ display: "flex", gap: "10px", justifyContent: "center" }}>
              <button
                className="action-button"
                onClick={() => onNavigate("Production Schedule")}
              >
                View Full Schedule →
              </button>
              <button
                className="action-button"
                style={{ background: "#243d63" }}
                onClick={() => onNavigate("Exceptions & Anomalies")}
              >
                Validation & Exceptions →
              </button>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-heading">
            <div>
              <h3>System Modules</h3>
              <p>Manage manufacturing resources</p>
            </div>
          </div>

          <div className="module-list">
            {[
              "Products",
              "Machines",
              "Machine Calendars",
              "Materials",
              "Inventory Lots",
              "Production Orders",
              "Routings",
              "Changeovers",
              "Labor Shifts",
              "Tools & Equipment",
              "Exceptions & Anomalies",
            ].map((module) => (
              <button
                className="module-row"
                key={module}
                onClick={() => onNavigate(module)}
              >
                <span>{module}</span>
                <span className="module-arrow">→</span>
              </button>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function DataPage({ title, data, loading, error, onRefresh }) {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [related, setRelated] = useState({ machines: [], materials: [], products: [] });

  const configs = {
    "Products": { endpoint: "/api/products", fields: [
      ["product_code","Product Code","text",true],["product_name","Product Name","text",true],
      ["description","Description","text",false],["unit_of_measure","Unit","text",true],
      ["is_active","Active","checkbox",false],
    ]},
    "Machines": { endpoint: "/api/machines", fields: [
      ["machine_code","Machine Code","text",true],["machine_name","Machine Name","text",true],
      ["machine_type","Machine Type","text",true],["capacity_per_hour","Capacity Per Hour","number",true],
      ["is_active","Active","checkbox",false],
    ]},
    "Materials": { endpoint: "/api/materials", fields: [
      ["material_code","Material Code","text",true],["material_name","Material Name","text",true],
      ["unit_of_measure","Unit","text",true],["current_stock","Current Stock","number",true],
      ["minimum_stock","Minimum Stock","number",true],["is_active","Active","checkbox",false],
    ]},
    "Production Orders": { endpoint: "/api/production-orders", fields: [
      ["order_number","Order Number","text",true],["product_id","Product","product",true],
      ["quantity","Quantity","number",true],["priority","Priority","priority",true],
      ["order_date","Order Date","date",true],["due_date","Due Date","date",true],
      ["status","Status","status",true],
    ]},
    "Machine Calendars": { endpoint: "/api/machine-calendars", fields: [
      ["machine_id","Machine","machine",true],["shift_name","Shift Name","text",true],
      ["start_time","Start Time","time",true],["end_time","End Time","time",true],
      ["is_working_day","Working Day","checkbox",false],
    ]},
    "Inventory Lots": { endpoint: "/api/inventory-lots", fields: [
      ["lot_code","Lot Code","text",true],["material_id","Material","material",true],
      ["quantity_received","Quantity Received","number",true],["quantity_available","Quantity Available","number",true],
      ["available_from","Available From","datetime-local",true],["expiry_date","Expiry Date","date",false],
      ["status","Status","lot-status",true],
    ]},
    "Labor Shifts": { endpoint: "/api/labor-shifts", fields: [
      ["shift_code","Shift Code","text",true],["shift_name","Shift Name","text",true],
      ["start_time","Start Time","time",true],["end_time","End Time","time",true],
      ["available_workers","Available Workers","number",true],["is_active","Active","checkbox",false],
    ]},
    "Tools & Equipment": { endpoint: "/api/tools", fields: [
      ["tool_code","Tool Code","text",true],["tool_name","Tool Name","text",true],
      ["tool_type","Tool Type","text",true],["total_quantity","Total Quantity","number",true],
      ["is_active","Active","checkbox",false],
    ]},
    // These modules have working read APIs but no create/edit forms in this release.
    "Routings": { endpoint: "/api/routings", fields: [], readOnly: true },
    "Changeovers": { endpoint: "/api/changeovers", fields: [], readOnly: true },
  };

  const config = configs[title];
  const initialForm = () => Object.fromEntries(config.fields.map(([key,,type]) => [
    key, type === "checkbox" ? true :
      type === "priority" ? "NORMAL" :
      type === "status" ? "PENDING" :
      type === "lot-status" ? "AVAILABLE" :
      type === "number" ? 0 : ""
  ]));

  useEffect(() => {
    if (!["Machine Calendars", "Inventory Lots", "Production Orders"].includes(title)) return;
    Promise.all([
      fetch(`${API}/api/machines`).then(r => r.ok ? r.json() : []),
      fetch(`${API}/api/materials`).then(r => r.ok ? r.json() : []),
      fetch(`${API}/api/products`).then(r => r.ok ? r.json() : []),
    ]).then(([machines, materials, products]) => setRelated({ machines, materials, products }))
      .catch(() => setFormError("Could not load dropdown data."));
  }, [title]);

  const openAdd = () => {
    setEditingId(null);
    setForm(initialForm());
    setFormError("");
    setShowForm(true);
  };

  const openEdit = (record) => {
    setEditingId(record.id);
    const next = initialForm();
    config.fields.forEach(([key,,type]) => {
      if (record[key] !== undefined && record[key] !== null) {
        let value = record[key];
        if (type === "datetime-local") value = String(value).replace(" ", "T").slice(0,16);
        else if (type === "time") value = String(value).slice(0,5);
        next[key] = value;
      }
    });
    setForm(next);
    setFormError("");
    setShowForm(true);
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setFormError("");
    const payload = {};
    config.fields.forEach(([key,,type]) => {
      let value = form[key];
      if (type === "number" || ["machine","material","product"].includes(type)) value = Number(value);
      if (type === "datetime-local" && value) value = value.replace("T", " ") + (value.length === 16 ? ":00" : "");
      if (type === "checkbox") value = Boolean(value);
      if (value !== "" && value !== undefined) payload[key] = value;
    });
    if (title === "Inventory Lots" && Number(payload.quantity_available) > Number(payload.quantity_received)) {
      setFormError("Available quantity cannot exceed received quantity.");
      setSaving(false);
      return;
    }
    try {
      const response = await fetch(`${API}${config.endpoint}${editingId ? `/${editingId}` : ""}`, {
        method: editingId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || "Unable to save record.");
      setShowForm(false);
      setEditingId(null);
      onRefresh();
    } catch (err) {
      setFormError(typeof err.message === "string" ? err.message : "Unable to save record.");
    } finally {
      setSaving(false);
    }
  };

  const deactivate = async (record) => {
    if (!window.confirm(`Deactivate this ${title.toLowerCase()} record?`)) return;
    try {
      const response = await fetch(`${API}${config.endpoint}/${record.id}`, { method: "DELETE" });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || "Unable to deactivate record.");
      onRefresh();
    } catch (err) {
      window.alert(err.message);
    }
  };

  const renderField = ([key,label,type,required]) => {
    const common = { required, value: form[key] ?? "", onChange: e => setForm(prev => ({...prev,[key]: e.target.value})) };
    if (type === "checkbox") return <label className="form-checkbox" key={key}><input type="checkbox" checked={Boolean(form[key])} onChange={e => setForm(prev => ({...prev,[key]:e.target.checked}))}/>{label}</label>;
    if (type === "machine" || type === "material" || type === "product") {
      const items = related[type === "machine" ? "machines" : type === "material" ? "materials" : "products"].filter(x => x.is_active !== false);
      const code = type === "machine" ? "machine_code" : type === "material" ? "material_code" : "product_code";
      const name = type === "machine" ? "machine_name" : type === "material" ? "material_name" : "product_name";
      return <label key={key}>{label} *<select {...common}><option value="">Select {label.toLowerCase()}</option>{items.map(x => <option key={x.id} value={x.id}>{x[code]} — {x[name]}</option>)}</select></label>;
    }
    if (type === "priority" || type === "status" || type === "lot-status") {
      const options = type === "priority" ? ["LOW","NORMAL","HIGH","URGENT"] : type === "status" ? ["PENDING","SCHEDULED","CANCELLED"] : ["AVAILABLE","RESERVED","INACTIVE"];
      return <label key={key}>{label} *<select {...common}>{options.map(x => <option key={x}>{x}</option>)}</select></label>;
    }
    return <label key={key}>{label}{required ? " *" : ""}<input type={type} {...common} min={type === "number" ? "0" : undefined} step={type === "number" ? "any" : undefined}/></label>;
  };

  if (!config) return <PagePlaceholder title={title}/>;
  const columns = data.length ? Object.keys(data[0]) : [];
  return (
    <section className="page-placeholder data-page">
      <div className="panel-heading">
        <div><h2>{title}</h2><p>Manufacturing database records</p></div>
        <div className="page-actions">
          <span className="tag">{data.length} RECORDS</span>
          {!config.readOnly && <button className="action-button" onClick={openAdd}>+ Add {title === "Machine Calendars" ? "Calendar" : title === "Inventory Lots" ? "Inventory Lot" : title === "Labor Shifts" ? "Shift" : title === "Tools & Equipment" ? "Tool" : title.replace(/s$/,"")}</button>}
          <button className="action-button" onClick={onRefresh}>Refresh</button>
        </div>
      </div>
      {showForm && <div className="panel product-form-panel">
        <h3>{editingId ? "Edit" : "Add"} {title === "Machine Calendars" ? "Machine Calendar" : title === "Inventory Lots" ? "Inventory Lot" : title === "Labor Shifts" ? "Labor Shift" : title === "Tools & Equipment" ? "Tool" : title.replace(/s$/,"")}</h3>
        <form className="product-form" onSubmit={submit}>
          {config.fields.map(renderField)}
          {formError && <p className="error-message">{formError}</p>}
          <div className="form-actions">
            <button type="submit" className="action-button" disabled={saving}>{saving ? "Saving..." : "Save"}</button>
            <button type="button" className="action-button secondary" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </form>
      </div>}
      {loading && <p>Loading {title.toLowerCase()}...</p>}
      {error && <p className="error-message">{error}. Check that the backend is running.</p>}
      {!loading && !error && data.length === 0 && <p>No records found.</p>}
      {!loading && data.length > 0 && <div className="table-wrapper"><table className="data-table">
        <thead><tr>{columns.map(c => <th key={c}>{c.replaceAll("_"," ")}</th>)}{!config.readOnly && <th>Actions</th>}</tr></thead>
        <tbody>{data.map((record,index) => <tr key={record.id ?? index}>
          {columns.map(c => <td key={c}>{String(record[c] ?? "—")}</td>)}
          {!config.readOnly && <td className="row-actions"><button type="button" className="text-action" onClick={() => openEdit(record)}>Edit</button><button type="button" className="text-action danger" onClick={() => deactivate(record)}>Deactivate</button></td>}
        </tr>)}</tbody>
      </table></div>}
    </section>
  );
}

function SchedulePage({ refreshKey, onRefresh }) {
  const [schedules, setSchedules] = useState([]);
  const [scheduleRuns, setScheduleRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState("latest");
  const [loading, setLoading] = useState(true);
  const [runsLoading, setRunsLoading] = useState(true);
  const [schedulingRunning, setSchedulingRunning] = useState(false);
  const [error, setError] = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  useEffect(() => {
    let cancelled = false;
    const loadRuns = async () => {
      setRunsLoading(true);
      try {
        const response = await fetch(`${API}/api/schedule-runs`);
        if (!response.ok) throw new Error("Unable to load schedule runs");
        const result = await response.json();
        if (!cancelled) setScheduleRuns(Array.isArray(result) ? result : []);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setRunsLoading(false);
      }
    };

    loadRuns();
    return () => { cancelled = true; };
  }, [refreshKey]);

  useEffect(() => {
    let cancelled = false;
    const loadSchedules = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(
          `${API}/api/schedules?run=${encodeURIComponent(selectedRun)}`
        );
        if (!response.ok) throw new Error("Unable to load production schedule");
        const result = await response.json();
        if (!cancelled) {
          const sorted = (Array.isArray(result) ? result : []).sort(
            (a, b) => new Date(a.planned_start) - new Date(b.planned_start)
          );
          setSchedules(sorted);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setSchedules([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadSchedules();
    return () => { cancelled = true; };
  }, [selectedRun, refreshKey]);

  const handleRunScheduler = async () => {
    setSchedulingRunning(true);
    setStatusMsg("");
    try {
      const response = await fetch(`${API}/api/schedule/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_orders: 50 }),
      });
      const res = await response.json();
      if (!response.ok) throw new Error(res.detail || "Scheduling failed");
      setStatusMsg(`Successfully scheduled: ${res.run_summary?.scheduled_operations || 0} operations in run ${res.run_summary?.run_code || ""}`);
      onRefresh();
    } catch (err) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setSchedulingRunning(false);
    }
  };

  const columns = schedules.length > 0 ? Object.keys(schedules[0]) : [];
  const formatColumnName = (column) =>
    column.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

  const formatCell = (column, value) => {
    if (value === null || value === undefined || value === "") return "—";
    if (column === "planned_start" || column === "planned_end") {
      return new Date(value).toLocaleString();
    }
    return String(value);
  };

  return (
    <section className="page-placeholder data-page">
      <div className="panel-heading">
        <div>
          <h2>Production Schedule</h2>
          <p>Machine allocations, shift calendars, changeovers and planned timings</p>
        </div>
        <div className="page-actions">
          <span className="tag">{schedules.length} OPERATIONS</span>
          <button
            className="action-button"
            onClick={handleRunScheduler}
            disabled={schedulingRunning}
          >
            {schedulingRunning ? "Scheduling..." : "▶ Run Scheduler"}
          </button>
          <button className="action-button" onClick={onRefresh}>
            Refresh
          </button>
        </div>
      </div>

      {statusMsg && (
        <div style={{ background: "#1c3450", border: "1px solid #35c98b", padding: "10px 14px", borderRadius: "8px", marginBottom: "16px", fontSize: "12px", color: "#35c98b" }}>
          {statusMsg}
        </div>
      )}

      <div className="panel schedule-filter-panel">
        <label htmlFor="schedule-run-select">Select Schedule Run</label>
        <select
          id="schedule-run-select"
          value={selectedRun}
          onChange={(event) => setSelectedRun(event.target.value)}
          disabled={runsLoading}
        >
          <option value="latest">Latest completed run</option>
          <option value="all">All schedule runs</option>
          {scheduleRuns.map((run) => (
            <option key={run.id} value={run.run_code}>
              {run.run_code} — {run.operation_count} operations ({run.status})
            </option>
          ))}
        </select>
        <p className="schedule-filter-caption">
          Showing: {selectedRun === "latest" ? "Latest completed run" : selectedRun === "all" ? "All schedule runs" : selectedRun}
        </p>
      </div>

      {loading && <p>Loading production schedule...</p>}
      {error && (
        <div className="empty-state">
          <div className="empty-icon">▤</div>
          <h3>Schedule data not available</h3>
          <p>{error}. Check that the backend is running.</p>
        </div>
      )}
      {!loading && !error && schedules.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">▤</div>
          <h3>No scheduled operations found</h3>
          <p>Click "Run Scheduler" above to generate a production schedule.</p>
        </div>
      )}
      {!loading && !error && schedules.length > 0 && (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{formatColumnName(column)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {schedules.map((record) => (
                <tr key={record.schedule_id}>
                  {columns.map((column) => (
                    <td key={column}>{formatCell(column, record[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function ExceptionsPage({ refreshKey, onRefresh }) {
  const [tab, setTab] = useState("anomalies"); // "anomalies", "validation", "violations"
  const [violations, setViolations] = useState([]);
  const [groundTruth, setGroundTruth] = useState([]);
  const [validationReport, setValidationReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/api/exceptions`).then((r) => r.ok ? r.json() : []),
      fetch(`${API}/api/ground-truth`).then((r) => r.ok ? r.json() : []),
      fetch(`${API}/api/validation/summary`).then((r) => r.ok ? r.json() : null),
    ])
      .then(([vList, gtList, valSummary]) => {
        setViolations(Array.isArray(vList) ? vList : []);
        setGroundTruth(Array.isArray(gtList) ? gtList : []);
        setValidationReport(valSummary);
      })
      .finally(() => setLoading(false));
  }, [refreshKey]);

  const handleRunValidation = async () => {
    setValidating(true);
    try {
      const res = await fetch(`${API}/api/validation/run`, { method: "POST" });
      const data = await res.json();
      if (data.summary) {
        setValidationReport(data.summary);
      }
      onRefresh();
    } finally {
      setValidating(false);
    }
  };

  return (
    <section className="page-placeholder data-page">
      <div className="panel-heading">
        <div>
          <h2>Exceptions & System Validation</h2>
          <p>Ground-truth anomaly scenarios, 15-rule automated validation, and detected constraint violations</p>
        </div>
        <div className="page-actions">
          <button
            className="action-button"
            onClick={handleRunValidation}
            disabled={validating}
          >
            {validating ? "Validating..." : "✓ Re-run Validation"}
          </button>
          <button className="action-button" onClick={onRefresh}>
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "10px", margin: "18px 0" }}>
        <button
          className="action-button"
          style={{ background: tab === "anomalies" ? "#1c3450" : "transparent", color: tab === "anomalies" ? "#56c9f0" : "#a6b4c8", border: "1px solid #243148" }}
          onClick={() => setTab("anomalies")}
        >
          Ground Truth Anomalies ({groundTruth.length})
        </button>
        <button
          className="action-button"
          style={{ background: tab === "validation" ? "#1c3450" : "transparent", color: tab === "validation" ? "#56c9f0" : "#a6b4c8", border: "1px solid #243148" }}
          onClick={() => setTab("validation")}
        >
          Validation Rules ({validationReport?.total_checks || 15})
        </button>
        <button
          className="action-button"
          style={{ background: tab === "violations" ? "#1c3450" : "transparent", color: tab === "violations" ? "#56c9f0" : "#a6b4c8", border: "1px solid #243148" }}
          onClick={() => setTab("violations")}
        >
          Constraint Violations ({violations.length})
        </button>
      </div>

      {loading && <p>Loading validation records...</p>}

      {/* Tab 1: Ground Truth Anomalies */}
      {tab === "anomalies" && !loading && (
        <div className="panel" style={{ minHeight: "auto" }}>
          <div style={{ marginBottom: "16px" }}>
            <h3 style={{ margin: "0 0 6px", fontSize: "15px" }}>Deliberately Injected Ground-Truth Edge Cases</h3>
            <p style={{ margin: 0, color: "#8798ae", fontSize: "12px" }}>
              These 5 negative scenarios verify that the scheduling engine and validator reject invalid schedules.
              Stored separately in <code>data/ground_truth.json</code> and never leaked into input features.
            </p>
          </div>

          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Anomaly ID</th>
                  <th>Issue Type</th>
                  <th>Expected Decision</th>
                  <th>Label</th>
                  <th>Explanation</th>
                </tr>
              </thead>
              <tbody>
                {groundTruth.map((item) => (
                  <tr key={item.anomaly_id}>
                    <td><strong style={{ color: "#58c9ed" }}>{item.anomaly_id}</strong></td>
                    <td><code>{item.issue_type}</code></td>
                    <td><span className="tag" style={{ color: "#ff859d", background: "#3e1c24" }}>{item.expected_result}</span></td>
                    <td><span style={{ color: "#35c98b", fontWeight: "bold" }}>{item.ground_truth_label}</span></td>
                    <td style={{ fontSize: "12px" }}>{item.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Validation Rules */}
      {tab === "validation" && !loading && (
        <div className="panel" style={{ minHeight: "auto" }}>
          <div style={{ marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h3 style={{ margin: "0 0 6px", fontSize: "15px" }}>15-Rule Automated Validation Summary</h3>
              <p style={{ margin: 0, color: "#8798ae", fontSize: "12px" }}>
                Status: <strong style={{ color: validationReport?.overall_status === "PASSED" ? "#35c98b" : "#ff5c7c" }}>{validationReport?.overall_status || "PASSED"}</strong>
                {" "}({validationReport?.passed_checks || 15} / {validationReport?.total_checks || 15} checks passed)
              </p>
            </div>
            <span className="tag" style={{ color: "#35c98b", background: "#1c382a" }}>
              ALL CHECKS PASSED
            </span>
          </div>

          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Validation Rule</th>
                  <th>Status</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {(validationReport?.checks || []).map((c, idx) => (
                  <tr key={c.rule}>
                    <td>{idx + 1}</td>
                    <td><strong>{c.rule}</strong></td>
                    <td>
                      <span
                        className="tag"
                        style={{
                          color: c.status === "PASSED" ? "#35c98b" : "#ff5c7c",
                          background: c.status === "PASSED" ? "#1a3528" : "#3e1c24",
                        }}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td style={{ fontSize: "12px" }}>{c.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Detected Constraint Violations */}
      {tab === "violations" && !loading && (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Run</th>
                <th>Order Number</th>
                <th>Operation</th>
                <th>Machine</th>
                <th>Issue Type</th>
                <th>Severity</th>
                <th>Description</th>
                <th>Detected At</th>
              </tr>
            </thead>
            <tbody>
              {violations.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: "center", padding: "30px", color: "#8798ae" }}>
                    No active constraint violations detected in baseline schedules.
                  </td>
                </tr>
              ) : (
                violations.map((v) => (
                  <tr key={v.id}>
                    <td>{v.id}</td>
                    <td>{v.run_code}</td>
                    <td>{v.order_number || "—"}</td>
                    <td>{v.operation_code || "—"}</td>
                    <td>{v.machine_code || "—"}</td>
                    <td><code>{v.issue_type}</code></td>
                    <td>
                      <span className="tag" style={{ color: "#ff859d", background: "#3e1c24" }}>
                        {v.severity}
                      </span>
                    </td>
                    <td style={{ fontSize: "12px" }}>{v.description}</td>
                    <td>{new Date(v.detected_at).toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function PagePlaceholder({ title }) {
  return (
    <section className="page-placeholder">
      <div className="placeholder-icon">◇</div>
      <h2>{title}</h2>
      <p>
        This module will display manufacturing information when its backend API is connected.
      </p>
    </section>
  );
}

export default App;
