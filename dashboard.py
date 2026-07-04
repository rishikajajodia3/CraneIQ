import json
import os
import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
st.set_page_config(
    page_title="CraneIQ Dashboard",
    page_icon="🏗️",
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
latest = None
all_events = []
if not os.path.exists(LOG_PATH):
    st.error(f"⚠️ Log file not found: `{LOG_PATH}`. Make sure the logger is running and the file exists.")
    st.stop()
with open(LOG_PATH, "r") as f:
    lines = [line.strip() for line in f if line.strip()]
if not lines:
    st.warning("⚠️ Log file exists but is empty. Waiting for the logger to write events...")
    st.stop()
latest = json.loads(lines[-1])
# Parse latest values
gesture        = latest["gesture"]
operator_action = latest["operator_action"]
confidence_raw = latest["confidence"]
confidence     = confidence_raw * 100.0          # 1.0 → 100.0%
timestamp_raw  = latest["timestamp"]
verification   = latest["verification_state"]    # "MATCH" or "MISMATCH"
# Format timestamp: "2026-07-03T20:53:16.084827" → "20:53:16"
last_update_dt = datetime.fromisoformat(timestamp_raw)
time_display   = last_update_dt.strftime("%H:%M:%S")
date_display   = last_update_dt.strftime("%Y-%m-%d")
is_safe = (verification == "MATCH")
# Parse last 10 events (newest first)
for line in reversed(lines[-10:]):
    try:
        ev = json.loads(line)
        ev_time = datetime.fromisoformat(ev["timestamp"]).strftime("%H:%M:%S")
        ev_conf = ev["confidence"] * 100.0
        ev_state = ev["verification_state"]
        all_events.append((ev_time, ev["gesture"], ev["operator_action"], ev_conf, ev_state))
    except Exception:
        continue
# ---------------------------------------------------------------------------
# STYLE
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --blue:#2054D6;
  --blue-deep:#12308A;
  --green:#12855C;
  --green-bg:#EAF7F1;
  --amber:#B5720A;
  --amber-bg:#FDF3E4;
  --ink:#0E1526;
  --ink-soft:#5B6478;
  --ink-faint:#8891A3;
  --line:#E4E9F2;
}
html, body, [class*="css"]{
  font-family:'Inter', sans-serif;
}
/* App background */
[data-testid="stAppViewContainer"]{
  background:#0A0F1E;
  background-image:
    linear-gradient(rgba(148,163,184,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148,163,184,0.05) 1px, transparent 1px);
  background-size:34px 34px;
}
[data-testid="stHeader"]{ background:transparent; }
/* Sidebar */
[data-testid="stSidebar"]{
  background:#060A14;
  border-right:1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] *{ color:#E7ECF7; }
.brand-mark{
  width:32px;height:32px;border-radius:6px;
  background:linear-gradient(155deg, var(--blue) 0%, var(--blue-deep) 100%);
  display:flex;align-items:center;justify-content:center;
  font-family:'IBM Plex Mono',monospace;font-weight:700;color:#fff;font-size:13px;
}
.status-title{
  font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:1.4px;
  text-transform:uppercase;color:#4C5670;margin:18px 0 6px 2px;
}
.status-row{
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 2px;border-bottom:1px solid rgba(255,255,255,0.05);
}
.status-label{ font-size:12.5px; color:#8892A8; }
.status-value{
  display:flex;align-items:center;gap:7px;
  font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:600;color:#E7ECF7;
}
.dot{ width:6px;height:6px;border-radius:50%; flex-shrink:0; }
.dot-on{ background:#22C67A; box-shadow:0 0 0 3px rgba(34,198,122,0.18); }
.dot-live{ background:#22C67A; box-shadow:0 0 0 3px rgba(34,198,122,0.18); animation:pulse 2s infinite; }
@keyframes pulse{
  0%{box-shadow:0 0 0 0 rgba(34,198,122,0.4);}
  70%{box-shadow:0 0 0 6px rgba(34,198,122,0);}
  100%{box-shadow:0 0 0 0 rgba(34,198,122,0);}
}
.sidebar-footer{
  margin-top:24px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.06);
  font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:#404A64;line-height:1.7;
}
/* Header */
.title-eyebrow{
  font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:2px;
  text-transform:uppercase;color:#5A6788;margin-bottom:6px;
}
h1.dash-title{
  font-size:28px;font-weight:800;color:#F4F7FF;letter-spacing:-0.3px;margin:0;
}
.subtitle{ color:#7D89A6;font-size:13.5px;margin-top:6px; }
/* Alert — SAFE (green) */
.alert{
  background:var(--green-bg);border:1px solid #BFE6D4;border-left:4px solid var(--green);
  border-radius:8px;padding:16px 20px;display:flex;align-items:center;gap:12px;margin:22px 0 26px;
}
.alert-icon{
  width:22px;height:22px;border-radius:50%;background:var(--green);color:#fff;
  font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;
}
.alert-text{ font-size:14px;color:#0C4A32; }
.alert-time{ margin-left:auto;font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:#3E8A6C; }
/* Alert — ALERT (red) */
.alert-danger{
  background:#FEF2F2;border:1px solid #FECACA;border-left:4px solid #DC2626;
  border-radius:8px;padding:16px 20px;display:flex;align-items:center;gap:12px;margin:22px 0 26px;
}
.alert-danger .alert-icon{ background:#DC2626; }
.alert-danger .alert-text{ color:#7F1D1D; }
.alert-danger .alert-time{ color:#B91C1C; }
/* Cards */
.kpi-card{
  background:#fff;border:1px solid var(--line);border-radius:10px;
  padding:20px 20px 18px;position:relative;overflow:hidden;height:100%;
}
.kpi-card::before{
  content:'';position:absolute;top:0;left:0;width:100%;height:2px;
  background:var(--blue-deep);opacity:0.12;
}
.kpi-label{
  font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:1.2px;
  text-transform:uppercase;color:var(--ink-faint);margin-bottom:12px;
  display:flex;align-items:center;justify-content:space-between;
}
.kpi-value{
  font-size:34px;font-weight:800;color:var(--blue-deep);
  letter-spacing:-0.5px;font-family:'IBM Plex Mono',monospace;
}
.kpi-value.stack{ line-height:1.25;font-size:23px; }
.kpi-tag{
  font-size:9px;font-weight:700;padding:2px 6px;border-radius:4px;
  background:#EFF3FC;color:var(--blue-deep);letter-spacing:0.4px;
}
.kpi-tag.match{ background:var(--green-bg); color:var(--green); }
.kpi-tag.mismatch{ background:#FEE2E2; color:#DC2626; }
/* Panels */
.panel{
  background:#fff;border:1px solid var(--line);border-radius:10px;
  padding:24px 26px;margin-bottom:20px;
}
.panel-eyebrow{
  font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:1.4px;
  text-transform:uppercase;color:var(--ink-faint);font-weight:600;margin-bottom:4px;display:block;
}
.panel-title{ font-size:16px;font-weight:700;color:var(--ink); }
.gauge-reading{
  font-family:'IBM Plex Mono',monospace;font-size:28px;font-weight:700;color:var(--blue-deep);
}
.gauge-ticks{
  display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;
  font-size:10px;color:var(--ink-faint);margin-top:8px;
}
/* Health grid */
.health-item{ padding:4px 4px; }
.health-label{
  font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:1px;
  text-transform:uppercase;color:var(--ink-faint);margin-bottom:8px;
}
.health-value{
  display:flex;align-items:center;gap:8px;font-size:16px;font-weight:700;color:var(--ink);
}
.health-value .dot{ background:#12855C; box-shadow:0 0 0 3px rgba(18,133,92,0.15); }
/* Events */
.event-row{
  display:flex;align-items:center;gap:14px;padding:12px 0;
  border-bottom:1px solid var(--line);
}
.event-row:last-child{ border-bottom:none; }
.event-time{
  font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--ink-faint);
  width:70px;flex-shrink:0;
}
.event-badge{
  font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
  padding:3px 8px;border-radius:4px;width:68px;text-align:center;flex-shrink:0;
}
.badge-safe{ background:var(--green-bg); color:var(--green); }
.badge-mismatch{ background:#FEE2E2; color:#DC2626; }
.event-text{ font-size:13px;color:var(--ink-soft); }
/* Progress bar restyle for the gauge */
div[data-testid="stProgress"] > div > div > div{
  background:linear-gradient(90deg, #3E6FE0 0%, var(--blue-deep) 100%);
}
div[data-testid="stProgress"] > div > div{
  background:#EEF1F7;
  height:10px;
  border-radius:5px;
}
/* Deploy button */
.stButton > button{
  background:var(--blue);color:#fff;border:none;font-weight:600;
  padding:8px 18px;border-radius:7px;box-shadow:0 6px 16px -6px rgba(32,84,214,0.35);
}
.stButton > button:hover{ background:var(--blue-deep); color:#fff; }
</style>
""",
    unsafe_allow_html=True,
)
# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div class="brand-mark">CQ</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(
            "<div style='font-weight:700;font-size:15px;'>CraneIQ</div>"
            "<div style='font-family:IBM Plex Mono, monospace;font-size:9.5px;"
            "color:#5C6884;letter-spacing:1.2px;text-transform:uppercase;'>Site Monitor · Bay 04</div>",
            unsafe_allow_html=True,
        )
    st.markdown('<div class="status-title">System Status</div>', unsafe_allow_html=True)
    def status_row(label, value, live=False):
        dot_class = "dot-live" if live else "dot-on"
        st.markdown(
            f"""<div class="status-row">
                    <span class="status-label">{label}</span>
                    <span class="status-value"><span class="dot {dot_class}"></span>{value}</span>
                </div>""",
            unsafe_allow_html=True,
        )
    status_row("Dashboard", "Running", live=True)
    status_row("Camera Feed", "Online")
    status_row("AI Model", "Loaded")
    status_row("MediaPipe", "Active")
    st.markdown(
        """<div class="sidebar-footer">
                BUILD 2.4.1<br>
                NODE: crane-iq-edge-07<br>
                UPTIME: 14h 22m
            </div>""",
        unsafe_allow_html=True,
    )
# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
h_left, h_right = st.columns([5, 1])
with h_left:
    st.markdown(
        """
        <div class="title-eyebrow">Real-Time Gesture Monitoring</div>
        <h1 class="dash-title">CraneIQ Dashboard</h1>
        <div class="subtitle">AI-assisted crane safety monitoring — operator action verification</div>
        """,
        unsafe_allow_html=True,
    )
with h_right:
    st.write("")
    st.button("Deploy", use_container_width=True)
# ---------------------------------------------------------------------------
# ALERT BANNER — green for MATCH, red for MISMATCH
# ---------------------------------------------------------------------------
alert_timestamp = last_update_dt.strftime("%H:%M:%S · %b %d %Y").upper()
if is_safe:
    st.markdown(
        f"""
        <div class="alert">
            <div class="alert-icon">✓</div>
            <div class="alert-text"><b style="font-family:'IBM Plex Mono',monospace;">SAFE</b>
             — Operator action matches detected gesture</div>
            <div class="alert-time">{alert_timestamp}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="alert alert-danger">
            <div class="alert-icon">!</div>
            <div class="alert-text"><b style="font-family:'IBM Plex Mono',monospace;">ALERT</b>
             — Operator action does NOT match detected gesture</div>
            <div class="alert-time">{alert_timestamp}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
# ---------------------------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">Detected Gesture</div>
                <div class="kpi-value">{gesture}</div>
            </div>""",
        unsafe_allow_html=True,
    )
# Dynamic tag: green MATCH or red MISMATCH
tag_class = "match" if is_safe else "mismatch"
tag_label = "MATCH" if is_safe else "MISMATCH"
with c2:
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">Operator Action
                    <span class="kpi-tag {tag_class}">{tag_label}</span>
                </div>
                <div class="kpi-value">{operator_action}</div>
            </div>""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">Confidence</div>
                <div class="kpi-value">{confidence:.1f}%</div>
            </div>""",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""<div class="kpi-card">
                <div class="kpi-label">Last Update</div>
                <div class="kpi-value stack">{date_display}<br>{time_display}</div>
            </div>""",
        unsafe_allow_html=True,
    )
st.write("")
# ---------------------------------------------------------------------------
# CONFIDENCE GAUGE
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="panel">
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;">
            <div><span class="panel-eyebrow">Model Output</span>
                 <span class="panel-title">Confidence Level</span></div>
            <div class="gauge-reading">{confidence:.1f}%</div>
        </div>
    """,
    unsafe_allow_html=True,
)
st.progress(confidence / 100)
st.markdown(
    """
        <div class="gauge-ticks"><span>0</span><span>25</span><span>50</span><span>75</span><span>100</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
# ---------------------------------------------------------------------------
# SYSTEM HEALTH  (static — infrastructure status doesn't come from the event log)
# ---------------------------------------------------------------------------
health = {
    "Dashboard": ("Healthy", True),
    "Camera":    ("Online",  True),
    "AI Model":  ("Ready",   True),
    "MediaPipe": ("Running", True),
}
st.markdown(
    '<div class="panel"><span class="panel-eyebrow">Infrastructure</span>'
    '<span class="panel-title">System Health</span><div style="height:16px;"></div>',
    unsafe_allow_html=True,
)
h1, h2, h3, h4 = st.columns(4)
for col, (label, (value, ok)) in zip((h1, h2, h3, h4), health.items()):
    with col:
        st.markdown(
            f"""<div class="health-item">
                    <div class="health-label">{label}</div>
                    <div class="health-value"><span class="dot"></span>{value}</div>
                </div>""",
            unsafe_allow_html=True,
        )
st.markdown("</div>", unsafe_allow_html=True)
# ---------------------------------------------------------------------------
# RECENT EVENTS  — last 10 from logs/events.jsonl, newest first
# ---------------------------------------------------------------------------
events_html = (
    '<div class="panel">'
    '<span class="panel-eyebrow">Log</span>'
    '<span class="panel-title">Recent Events</span>'
    '<div style="height:12px;"></div>'
)
for ev_time, ev_gesture, ev_operator, ev_conf, ev_state in all_events:
    badge_class = "badge-safe" if ev_state == "MATCH" else "badge-mismatch"
    badge_label = "MATCH" if ev_state == "MATCH" else "MISMATCH"
    ev_text = (
        f"Gesture: <b>{ev_gesture}</b> · "
        f"Operator: <b>{ev_operator}</b> · "
        f"Confidence: {ev_conf:.1f}%"
    )
    events_html += f"""
        <div class="event-row">
            <span class="event-time">{ev_time}</span>
            <span class="event-badge {badge_class}">{badge_label}</span>
            <span class="event-text">{ev_text}</span>
        </div>"""
events_html += "</div>"
st.markdown(events_html, unsafe_allow_html=True)
