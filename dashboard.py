import json
import os
import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="CraneIQ Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# AUTO-REFRESH every 2 seconds
# ---------------------------------------------------------------------------
st_autorefresh(interval=2000, key="refresh")

# ---------------------------------------------------------------------------
# LOAD LIVE DATA FROM LOGGER
# ---------------------------------------------------------------------------
LOG_PATH = "logs/events.jsonl"

if not os.path.exists(LOG_PATH):
    st.error(f"Log file not found: `{LOG_PATH}`. Make sure the logger is running.")
    st.stop()

with open(LOG_PATH, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

if not lines:
    st.warning("Log file exists but is empty. Waiting for events...")
    st.stop()

# Find the most recent line that actually parses — a half-written line
# during a concurrent write shouldn't crash the whole dashboard.
latest = None
for line in reversed(lines):
    try:
        latest = json.loads(line)
        break
    except json.JSONDecodeError:
        continue

if latest is None:
    st.warning("No valid events could be parsed from the log yet.")
    st.stop()


def safe_pct(value):
    """Convert a 0-1 confidence value to a 0-100 percentage, tolerating None."""
    return (value * 100.0) if value is not None else 0.0


gesture = latest.get("gesture") or "IDLE"
operator_action = latest.get("operator_action") or "—"
confidence = safe_pct(latest.get("confidence"))
timestamp_raw = latest.get("timestamp")
verification = latest.get("verification_state") or "IDLE"

try:
    last_update_dt = datetime.fromisoformat(timestamp_raw)
except (TypeError, ValueError):
    last_update_dt = datetime.now()
time_display = last_update_dt.strftime("%H:%M:%S")
date_display = last_update_dt.strftime("%b %d, %Y")

# verification_engine.py has 7 possible states — each maps to one of three
# visual tones so DELAYED_ACTION/WAITING/UNCERTAIN aren't shown as a full
# mismatch, and IDLE reads as neutral rather than alarming.
STATE_DISPLAY = {
    "MATCH":                ("safe",    "Operator action matches the detected gesture"),
    "DELAYED_ACTION":       ("warning", "Correct action, but slower than expected"),
    "MISMATCH":             ("danger",  "Operator action does not match the detected gesture"),
    "NO_ACTION":            ("danger",  "No operator response detected in time"),
    "WAITING_FOR_RESPONSE": ("warning", "Gesture detected, awaiting operator action"),
    "UNCERTAIN":            ("warning", "Gesture not confidently classified"),
    "IDLE":                 ("idle",    "No active gesture"),
}
tone, tone_text = STATE_DISPLAY.get(verification, ("idle", f"State: {verification}"))

all_events = []
for line in reversed(lines[-15:]):
    try:
        ev = json.loads(line)
        ev_time = datetime.fromisoformat(ev["timestamp"]).strftime("%H:%M:%S")
        ev_conf = safe_pct(ev.get("confidence"))
        ev_state = ev.get("verification_state") or "IDLE"
        all_events.append((ev_time, ev.get("gesture") or "IDLE", ev.get("operator_action") or "—", ev_conf, ev_state))
    except Exception:
        continue
    if len(all_events) >= 10:
        break

# ---------------------------------------------------------------------------
# STYLE — single palette, single font family, generous spacing
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root{
  --navy:#0B1220;
  --navy-deep:#070C16;
  --steel:#3E6FE0;
  --steel-soft:#8FA8E8;
  --amber:#E8A33D;
  --amber-bg:rgba(232,163,61,0.14);
  --green:#3FCB92;
  --green-bg:rgba(63,203,146,0.14);
  --red:#EF6F63;
  --red-bg:rgba(239,111,99,0.14);
  --ink:#F3F6FC;
  --ink-soft:#B9C3D6;
  --ink-faint:#7C8AA5;
  --line:rgba(255,255,255,0.09);
  --canvas:#0B1220;
  --card:#121A2C;
}

html, body, [class*="css"]{
  font-family:'Inter', sans-serif;
}

[data-testid="stAppViewContainer"]{ background: var(--canvas); }
[data-testid="stHeader"]{ background:transparent; }
[data-testid="stToolbar"]{ visibility:hidden; }

[data-testid="stSidebar"]{
  background: var(--navy-deep);
  border-right: none;
}
[data-testid="stSidebar"] * { color: #E7ECF3; }

.block-container{ padding-top: 2.8rem; padding-bottom: 3rem; max-width: 1180px; }

/* ---- Sidebar ---- */
.brand-name{ font-size:16px; font-weight:700; color:#FFFFFF; letter-spacing:-0.2px; }
.brand-sub{
  font-family:'IBM Plex Mono', monospace; font-size:10px; letter-spacing:1.4px;
  text-transform:uppercase; color:#7A8399; margin-top:2px;
}
.sidebar-section{
  font-family:'IBM Plex Mono', monospace; font-size:10px; letter-spacing:1.6px;
  text-transform:uppercase; color:#5C6478; margin:36px 0 14px 0;
}
.sidebar-row{
  display:flex; align-items:center; justify-content:space-between;
  padding:11px 0; border-bottom:1px solid rgba(255,255,255,0.06);
}
.sidebar-label{ font-size:13px; color:#B6BECC; }
.sidebar-value{ font-size:13px; font-weight:600; color:#F0F2F6; }
.sidebar-footer{
  margin-top:40px; padding-top:18px; border-top:1px solid rgba(255,255,255,0.08);
  font-family:'IBM Plex Mono', monospace; font-size:10px; color:#5E6980; line-height:1.9;
}

/* ---- Header ---- */
.page-eyebrow{
  font-family:'IBM Plex Mono', monospace; font-size:11px; letter-spacing:2px;
  text-transform:uppercase; color:var(--amber); margin-bottom:10px;
}
h1.page-title{
  font-size:30px; font-weight:800; color:var(--ink); letter-spacing:-0.4px; margin:0 0 6px 0;
}
.page-subtitle{ color:var(--ink-soft); font-size:14px; }

/* ---- Status banner (single, three tones) ---- */
.banner{
  border-radius:10px; padding:18px 22px; margin:28px 0 32px 0;
  display:flex; align-items:center; gap:16px; background: var(--card);
  border: 1px solid var(--line);
}
.banner-dot{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.banner-safe .banner-dot{ background: var(--green); }
.banner-warning .banner-dot{ background: var(--amber); }
.banner-danger .banner-dot{ background: var(--red); }
.banner-idle .banner-dot{ background: var(--ink-faint); }
.banner-state{
  font-family:'IBM Plex Mono', monospace; font-size:13px; font-weight:600; color: var(--ink);
  letter-spacing:0.3px;
}
.banner-text{ font-size:14px; color: var(--ink-soft); margin-left:2px; }
.banner-time{
  margin-left:auto; font-family:'IBM Plex Mono', monospace; font-size:11.5px; color: var(--ink-faint);
}

/* ---- KPI cards ---- */
.kpi-card{
  background: var(--card); border:1px solid var(--line); border-radius:10px;
  padding:22px 24px; height:100%;
}
.kpi-label{
  font-family:'IBM Plex Mono', monospace; font-size:10.5px; letter-spacing:1.2px;
  text-transform:uppercase; color: var(--ink-faint); margin-bottom:14px;
}
.kpi-value{
  font-size:26px; font-weight:700; color: var(--ink); letter-spacing:-0.3px;
}
.kpi-value.mono{ font-family:'IBM Plex Mono', monospace; font-size:24px; }
.kpi-value.small{ font-size:18px; line-height:1.5; }
.kpi-pill{
  display:inline-block; font-size:10px; font-weight:600; padding:3px 9px; border-radius:20px;
  margin-top:10px; font-family:'IBM Plex Mono', monospace; letter-spacing:0.3px;
}
.pill-safe{ background: var(--green-bg); color: var(--green); }
.pill-warning{ background: var(--amber-bg); color: var(--amber); }
.pill-danger{ background: var(--red-bg); color: var(--red); }
.pill-idle{ background:#F0F1F3; color: var(--ink-faint); }

/* ---- Panels ---- */
.panel{
  background: var(--card); border:1px solid var(--line); border-radius:10px;
  padding:26px 28px; margin-bottom:24px;
}
.panel-title{ font-size:15px; font-weight:700; color: var(--ink); margin-bottom:20px; }

/* ---- Confidence bar ---- */
.confidence-row{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:16px; }
.confidence-value{ font-family:'IBM Plex Mono', monospace; font-size:22px; font-weight:700; color: var(--ink); }
div[data-testid="stProgress"] > div > div > div{ background: var(--steel); }
div[data-testid="stProgress"] > div > div{ background:rgba(255,255,255,0.08); height:8px; border-radius:4px; }

/* ---- Events list ---- */
.event-row{
  display:flex; align-items:center; gap:18px; padding:14px 0;
  border-bottom:1px solid var(--line);
}
.event-row:last-child{ border-bottom:none; }
.event-time{
  font-family:'IBM Plex Mono', monospace; font-size:11.5px; color: var(--ink-faint); width:64px; flex-shrink:0;
}
.event-tag{
  font-family:'IBM Plex Mono', monospace; font-size:9.5px; font-weight:600;
  padding:4px 10px; border-radius:20px; width:120px; text-align:center; flex-shrink:0; letter-spacing:0.3px;
}
.event-detail{ font-size:13px; color: var(--ink-soft); }
.event-detail b{ color: var(--ink); font-weight:600; }
.empty-state{ color: var(--ink-faint); font-size:13px; padding:8px 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand-name">CraneIQ</div>'
        '<div class="brand-sub">Site Monitor</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)

    def sidebar_row(label, value):
        st.markdown(
            f"""<div class="sidebar-row">
                    <span class="sidebar-label">{label}</span>
                    <span class="sidebar-value">{value}</span>
                </div>""",
            unsafe_allow_html=True,
        )

    # Static for this prototype — not wired to a live health check.
    sidebar_row("Camera", "Online")
    sidebar_row("Model", "Loaded")
    sidebar_row("Tracking", "Active")

    st.markdown(
        """<div class="sidebar-footer">
                CraneIQ Prototype<br>
                Edge AI · Offline
            </div>""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown('<div class="page-eyebrow">Real-Time Verification</div>', unsafe_allow_html=True)
st.markdown('<h1 class="page-title">CraneIQ Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Rigger signal and operator action, compared live.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# STATUS BANNER
# ---------------------------------------------------------------------------
banner_time = last_update_dt.strftime("%H:%M:%S")
st.markdown(
    f"""
    <div class="banner banner-{tone}">
        <div class="banner-dot"></div>
        <div class="banner-state">{verification}</div>
        <div class="banner-text">{tone_text}</div>
        <div class="banner-time">{banner_time}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------------------------
pill_class = {"safe": "pill-safe", "warning": "pill-warning", "danger": "pill-danger", "idle": "pill-idle"}[tone]

c1, c2, c3, c4 = st.columns(4, gap="medium")

with c1:
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">Detected Gesture</div>
                <div class="kpi-value">{gesture}</div>
            </div>""",
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">Operator Action</div>
                <div class="kpi-value">{operator_action}</div>
                <div class="kpi-pill {pill_class}">{verification}</div>
            </div>""",
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">Confidence</div>
                <div class="kpi-value mono">{confidence:.1f}%</div>
            </div>""",
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">Last Update</div>
                <div class="kpi-value small">{date_display}<br>{time_display}</div>
            </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CONFIDENCE
# ---------------------------------------------------------------------------
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="confidence-row">
        <div class="panel-title" style="margin-bottom:0;">Model Confidence</div>
        <div class="confidence-value">{confidence:.1f}%</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.progress(min(max(confidence / 100, 0.0), 1.0))
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# RECENT EVENTS
# ---------------------------------------------------------------------------
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">Recent Events</div>', unsafe_allow_html=True)

if not all_events:
    st.markdown('<div class="empty-state">No events logged yet.</div>', unsafe_allow_html=True)
else:
    rows = ""
    for ev_time, ev_gesture, ev_operator, ev_conf, ev_state in all_events:
        row_tone, _ = STATE_DISPLAY.get(ev_state, ("idle", ""))
        rows += f"""
            <div class="event-row">
                <span class="event-time">{ev_time}</span>
                <span class="event-tag pill-{row_tone}" style="border-radius:20px;">{ev_state}</span>
                <span class="event-detail">Gesture: <b>{ev_gesture}</b> &nbsp;·&nbsp; Operator: <b>{ev_operator}</b> &nbsp;·&nbsp; {ev_conf:.1f}% confidence</span>
            </div>"""
    st.markdown(rows, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)