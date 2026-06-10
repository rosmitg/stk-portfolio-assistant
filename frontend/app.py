import os

import markdown as _md
import plotly.graph_objects as go
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

_GREEN_PALETTE = [
    "#00D084", "#00B872", "#00E896", "#33D69A",
    "#66E0B2", "#009960", "#00D0A0", "#4DFFB8",
]

st.set_page_config(
    page_title="STK — Portfolio Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def md_render(text: str) -> str:
    return _md.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )


# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background-color: #0A0A0F !important;
    color: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.5;
}

/* Kill all Streamlit chrome */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.stApp > header { display: none !important; }
section[data-testid="stMain"] > div { padding-top: 0 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Scrollbars ── */
* { scrollbar-width: thin; scrollbar-color: #1E1E2E #0A0A0F; }
*::-webkit-scrollbar { width: 4px; height: 4px; }
*::-webkit-scrollbar-track { background: #0A0A0F; }
*::-webkit-scrollbar-thumb { background: #1E1E2E; border-radius: 4px; }
*::-webkit-scrollbar-thumb:hover { background: #2A2A3E; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background-color: #111118 !important;
    color: #FFFFFF !important;
    border: 1px solid #1E1E2E !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    padding: 8px 12px !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #00D084 !important;
    box-shadow: 0 0 0 2px rgba(0,208,132,0.15) !important;
    outline: none !important;
}
.stTextInput label, .stNumberInput label {
    color: #8B8FA8 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stNumberInputStepDown"],
[data-testid="stNumberInputStepUp"] {
    background: #1E1E2E !important;
    border: none !important;
    color: #8B8FA8 !important;
}

/* ── Primary buttons ── */
.stButton > button,
[data-testid="stFormSubmitButton"] > button {
    background-color: #00D084 !important;
    color: #0A0A0F !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.01em !important;
    padding: 8px 16px !important;
    cursor: pointer !important;
    transition: background-color 0.15s, transform 0.1s !important;
}
.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #00E896 !important;
    color: #0A0A0F !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active,
[data-testid="stFormSubmitButton"] > button:active { transform: translateY(0) !important; }

/* ── Secondary form submit button (Clear) ── */
button[kind="secondaryFormSubmit"] {
    background-color: transparent !important;
    color: #8B8FA8 !important;
    border: 1px solid #1E1E2E !important;
    transform: none !important;
}
button[kind="secondaryFormSubmit"]:hover {
    background-color: #15151E !important;
    color: #FFFFFF !important;
    border-color: #8B8FA8 !important;
    transform: none !important;
}

/* ── Outlined add button ── */
.add-outlined > button {
    background-color: transparent !important;
    color: #00D084 !important;
    border: 1px solid #00D084 !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 6px 14px !important;
    transform: none !important;
}
.add-outlined > button:hover {
    background-color: rgba(0,208,132,0.08) !important;
    transform: none !important;
}

/* ── Delete button ── */
.del-btn > button {
    background-color: transparent !important;
    color: #8B8FA8 !important;
    border: none !important;
    padding: 3px 7px !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    border-radius: 6px !important;
    min-height: unset !important;
    height: 26px !important;
    width: 26px !important;
    transform: none !important;
    letter-spacing: 0 !important;
}
.del-btn > button:hover {
    background-color: rgba(255,71,87,0.12) !important;
    color: #FF4757 !important;
    transform: none !important;
}

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {
    background-color: #111118 !important;
    border: 1px dashed #1E1E2E !important;
    border-radius: 10px !important;
    color: #8B8FA8 !important;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: #00D084 !important; }

/* ── Form ── */
[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] > div { color: #8B8FA8 !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 13px !important; }

/* ── Column gaps ── */
[data-testid="stHorizontalBlock"] { gap: 0 !important; }

/* ── Navbar ── */
.navbar {
    background: #111118;
    border-bottom: 1px solid #1E1E2E;
    padding: 0 24px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}
.navbar-logo { font-size: 18px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.03em; display: flex; align-items: center; gap: 8px; }
.navbar-logo .accent { color: #00D084; }
.navbar-right { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #8B8FA8; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.status-dot.online  { background: #00D084; box-shadow: 0 0 6px rgba(0,208,132,0.6); }
.status-dot.offline { background: #FF4757; }

/* ── Portfolio value hero ── */
.port-value-block { padding: 0 0 14px; border-bottom: 1px solid #1E1E2E; margin-bottom: 14px; }
.port-value-label { font-size: 11px; font-weight: 600; color: #8B8FA8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
.port-value-number { font-size: 30px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.03em; line-height: 1.1; }
.port-value-change { font-size: 13px; font-weight: 600; margin-top: 4px; }

/* ── Holdings ── */
.holdings-header { font-size: 11px; font-weight: 700; color: #8B8FA8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.holding-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border-radius: 10px; transition: background 0.12s; }
.holding-row:hover { background: #15151E; }
.holding-left .ticker { font-size: 14px; font-weight: 700; color: #FFFFFF; }
.holding-left .company { font-size: 11px; color: #8B8FA8; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
.holding-mid { font-size: 12px; color: #8B8FA8; text-align: center; }
.holding-right { text-align: right; }
.holding-right .value { font-size: 14px; font-weight: 700; color: #FFFFFF; }
.holding-right .pct { font-size: 12px; font-weight: 600; margin-top: 1px; }
.holding-divider { height: 1px; background: linear-gradient(to right, transparent, #00D084, transparent); opacity: 0.15; margin: 2px 12px; }

/* ── Charts section ── */
.charts-header { font-size: 11px; font-weight: 700; color: #8B8FA8; text-transform: uppercase; letter-spacing: 0.08em; margin: 14px 0 4px; }

/* ── Chat bubbles ── */
.msg-user { display: flex; justify-content: flex-end; margin: 6px 0; }
.msg-user .bubble {
    background: #00D084; color: #0A0A0F;
    padding: 10px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 72%; font-size: 13px; font-weight: 500; line-height: 1.5; word-wrap: break-word;
}
.msg-ai { display: flex; justify-content: flex-start; margin: 6px 0; gap: 10px; }
.ai-avatar {
    width: 28px; height: 28px; border-radius: 8px;
    background: #1E1E2E; border: 1px solid #2A2A3E;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 800; color: #00D084;
    flex-shrink: 0; margin-top: 2px;
}
.msg-ai .bubble {
    background: #111118; color: #FFFFFF;
    padding: 12px 16px;
    border-radius: 4px 18px 18px 18px;
    max-width: 74%; font-size: 13px;
    border: 1px solid #1E1E2E; line-height: 1.55; word-wrap: break-word;
}

/* ── Markdown inside AI bubble ── */
.msg-ai .bubble p { margin: 0 0 8px; }
.msg-ai .bubble p:last-child { margin-bottom: 0; }
.msg-ai .bubble h1, .msg-ai .bubble h2, .msg-ai .bubble h3 {
    font-size: 14px; font-weight: 700; color: #FFFFFF; margin: 10px 0 5px;
}
.msg-ai .bubble h1:first-child, .msg-ai .bubble h2:first-child, .msg-ai .bubble h3:first-child { margin-top: 0; }
.msg-ai .bubble ul, .msg-ai .bubble ol { padding-left: 18px; margin: 6px 0; }
.msg-ai .bubble li { margin: 3px 0; color: #E0E6F0; }
.msg-ai .bubble strong { color: #FFFFFF; font-weight: 700; }
.msg-ai .bubble em { color: #C0C7D6; font-style: italic; }
.msg-ai .bubble code {
    background: #1E1E2E; border-radius: 4px; padding: 1px 6px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 12px; color: #00D084;
}
.msg-ai .bubble pre { background: #1E1E2E; border-radius: 8px; padding: 10px 12px; overflow-x: auto; margin: 8px 0; }
.msg-ai .bubble pre code { background: transparent; padding: 0; color: #E0E6F0; }
.msg-ai .bubble table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 12px; }
.msg-ai .bubble th { background: #1E1E2E; color: #8B8FA8; font-weight: 600; padding: 6px 10px; text-align: left; border: 1px solid #2A2A3E; }
.msg-ai .bubble td { border: 1px solid #1E1E2E; padding: 6px 10px; color: #E0E6F0; }
.msg-ai .bubble tr:nth-child(even) td { background: rgba(255,255,255,0.02); }
.msg-ai .bubble a { color: #00D084; text-decoration: none; }
.msg-ai .bubble a:hover { text-decoration: underline; }
.msg-ai .bubble blockquote {
    border-left: 3px solid #00D084; padding-left: 12px; margin: 8px 0;
    color: #8B8FA8; font-style: italic;
}
.msg-ai .bubble hr { border-color: #1E1E2E; margin: 10px 0; }

/* ── Source pills ── */
.source-pills { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px; }
.source-pill {
    background: rgba(0,208,132,0.08); border: 1px solid rgba(0,208,132,0.25);
    border-radius: 20px; padding: 2px 10px;
    font-size: 11px; color: #00D084; font-weight: 500;
}

/* ── Onboarding ── */
.ob-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #00D084; margin-bottom: 1rem; }
.ob-headline { font-size: 3rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.04em; line-height: 1.1; margin-bottom: 0.75rem; text-align: center; }
.ob-sub { font-size: 1rem; color: #8B8FA8; margin-bottom: 3rem; text-align: center; }
.ob-card { background: #111118; border: 1px solid #1E1E2E; border-radius: 14px; padding: 1.75rem 1.5rem; text-align: center; transition: border-color 0.15s, background 0.15s, transform 0.15s; }
.ob-card:hover { border-color: #00D084; background: rgba(0,208,132,0.04); transform: translateY(-2px); }
.ob-card.active { border-color: #00D084; background: rgba(0,208,132,0.06); }
.ob-card-icon { font-size: 1.75rem; margin-bottom: 0.75rem; }
.ob-card-title { font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem; }
.ob-card-desc { font-size: 0.8rem; color: #8B8FA8; line-height: 1.5; margin-bottom: 1.25rem; }

/* ── Prompt chips ── */
.prompt-chips-label { font-size: 11px; color: #8B8FA8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }

/* ── Error box ── */
.err-box { background: rgba(255,71,87,0.08); border: 1px solid rgba(255,71,87,0.3); border-radius: 8px; padding: 10px 14px; color: #FF4757; font-size: 13px; margin: 8px 0; }

hr { border-color: #1E1E2E; }
</style>
""", unsafe_allow_html=True)


# ── Backend helpers ────────────────────────────────────────────────────────────
def backend_get(path: str):
    try:
        r = requests.get(f"{BACKEND_URL}{path}", timeout=5)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot reach backend at {BACKEND_URL}"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, str(e)


def backend_post(path: str, payload: dict):
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=30)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot reach backend at {BACKEND_URL}"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, str(e)


def backend_upload(path: str, file_bytes: bytes, filename: str):
    try:
        r = requests.post(
            f"{BACKEND_URL}{path}",
            files={"file": (filename, file_bytes, "text/csv")},
            timeout=30,
        )
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot reach backend at {BACKEND_URL}"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, str(e)


def backend_delete(path: str):
    try:
        r = requests.delete(f"{BACKEND_URL}{path}", timeout=5)
        r.raise_for_status()
        return True, None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot reach backend at {BACKEND_URL}"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, str(e)


def _send_chat(message: str, portfolio_ctx: list) -> None:
    st.session_state.messages.append({"role": "user", "content": message})
    with st.spinner("Thinking…"):
        data, err = backend_post("/api/v1/chat", {
            "message": message,
            "portfolio_holdings": portfolio_ctx,
        })
    if err:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠ {err}",
            "sources": [],
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": data["answer"],
            "sources": data.get("sources", []),
        })


# ── Fetch portfolio + connection status ────────────────────────────────────────
portfolio, port_err = backend_get("/api/v1/portfolio")
has_portfolio = bool(portfolio) and not port_err
connected = port_err is None


# ── Navbar ─────────────────────────────────────────────────────────────────────
dot_class = "online" if connected else "offline"
dot_label = "Connected" if connected else "Disconnected"
st.markdown(f"""
<div class="navbar">
    <div class="navbar-logo">
        <span class="accent">STK</span>
        <span style="color:#8B8FA8; font-weight:400; font-size:14px;">Portfolio Assistant</span>
    </div>
    <div class="navbar-right">
        <span class="status-dot {dot_class}"></span>
        <span>{dot_label}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Stage 1 — Onboarding
# ══════════════════════════════════════════════════════════════════════════════
if not has_portfolio:

    if port_err:
        st.markdown(f'<div class="err-box">⚠ {port_err}</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem 2.5rem;">
        <div class="ob-eyebrow">AI-Powered Portfolio Intelligence</div>
        <div class="ob-headline">Your portfolio.<br>Explained by AI.</div>
        <div class="ob-sub">Connect your holdings and ask anything</div>
    </div>
    """, unsafe_allow_html=True)

    if "ob_panel" not in st.session_state:
        st.session_state.ob_panel = None
    if "ob_manual_added" not in st.session_state:
        st.session_state.ob_manual_added = []

    _, cards_col, _ = st.columns([1, 6, 1])
    with cards_col:
        c1, c2, c3 = st.columns(3, gap="large")

        alpaca_active = st.session_state.ob_panel == "alpaca"
        csv_active    = st.session_state.ob_panel == "csv"
        manual_active = st.session_state.ob_panel == "manual"

        with c1:
            st.markdown(f"""
            <div class="ob-card{'  active' if alpaca_active else ''}">
                <div class="ob-card-icon">⚡</div>
                <div class="ob-card-title">Connect Alpaca</div>
                <div class="ob-card-desc">Pull live positions from your Alpaca paper trading account in one click.</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Sync Alpaca", use_container_width=True, key="ob_alpaca"):
                with st.spinner("Syncing positions…"):
                    result, err = backend_post("/api/v1/portfolio/sync-alpaca", {})
                if err:
                    st.error(err)
                else:
                    st.rerun()

        with c2:
            st.markdown(f"""
            <div class="ob-card{'  active' if csv_active else ''}">
                <div class="ob-card-icon">📂</div>
                <div class="ob-card-title">Upload CSV</div>
                <div class="ob-card-desc">Import holdings from a CSV with columns: ticker, shares, avg_cost.</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Upload CSV", use_container_width=True, key="ob_csv"):
                st.session_state.ob_panel = "csv" if not csv_active else None
                st.rerun()

        with c3:
            st.markdown(f"""
            <div class="ob-card{'  active' if manual_active else ''}">
                <div class="ob-card-icon">✏️</div>
                <div class="ob-card-title">Add Manually</div>
                <div class="ob-card-desc">Enter each holding by ticker, share count, and average cost.</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Add Manually", use_container_width=True, key="ob_manual"):
                st.session_state.ob_panel = "manual" if not manual_active else None
                st.rerun()

    if st.session_state.ob_panel in ("csv", "manual"):
        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
        _, ep_col, _ = st.columns([1, 4, 1])
        with ep_col:
            st.markdown('<div style="background:#111118; border:1px solid #1E1E2E; border-radius:14px; padding:24px;">', unsafe_allow_html=True)

            if st.session_state.ob_panel == "csv":
                st.markdown("""
                <div style="margin-bottom:14px;">
                    <div style="font-size:14px; font-weight:700; color:#FFFFFF; margin-bottom:4px;">Upload your CSV file</div>
                    <div style="font-size:12px; color:#8B8FA8;">
                        Required columns:
                        <code style="background:#1E1E2E;padding:1px 6px;border-radius:4px;color:#00D084;">ticker</code>
                        <code style="background:#1E1E2E;padding:1px 6px;border-radius:4px;color:#00D084;">shares</code>
                        <code style="background:#1E1E2E;padding:1px 6px;border-radius:4px;color:#00D084;">avg_cost</code>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                uploaded = st.file_uploader("CSV file", type=["csv"], label_visibility="collapsed")
                if uploaded:
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    if st.button("Import CSV", use_container_width=True):
                        with st.spinner("Importing…"):
                            result, err = backend_upload(
                                "/api/v1/portfolio/upload-csv",
                                uploaded.getvalue(),
                                uploaded.name,
                            )
                        if err:
                            st.error(err)
                        else:
                            st.success(f"Imported {len(result)} holding(s)!")
                            st.rerun()

            if st.session_state.ob_panel == "manual":
                st.markdown("""
                <div style="margin-bottom:14px;">
                    <div style="font-size:14px; font-weight:700; color:#FFFFFF; margin-bottom:4px;">Add holdings manually</div>
                    <div style="font-size:12px; color:#8B8FA8;">Add as many as you like — click Done when finished.</div>
                </div>
                """, unsafe_allow_html=True)

                for note in st.session_state.ob_manual_added:
                    st.success(note)

                with st.form("ob_manual_form", clear_on_submit=True):
                    m_ticker = st.text_input("Ticker", placeholder="e.g. AAPL")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        m_shares = st.number_input("Shares", min_value=0.0001, step=0.001, format="%.4f", value=1.0)
                    with col_b:
                        m_cost = st.number_input("Avg cost ($)", min_value=0.01, step=0.01, format="%.2f", value=100.0)
                    add_btn = st.form_submit_button("Add Holding", use_container_width=True)

                if add_btn:
                    if not m_ticker.strip():
                        st.error("Ticker is required.")
                    else:
                        result, err = backend_post("/api/v1/portfolio", {
                            "ticker": m_ticker.strip().upper(),
                            "name":   m_ticker.strip().upper(),
                            "shares": m_shares,
                            "avg_cost": m_cost,
                        })
                        if err:
                            st.error(err)
                        else:
                            st.session_state.ob_manual_added.append(
                                f"Added {result['ticker']} — {m_shares:g} shares @ ${m_cost:.2f}"
                            )
                            st.rerun()

                if st.session_state.ob_manual_added:
                    if st.button("Done — View Portfolio →", use_container_width=True):
                        st.session_state.ob_manual_added = []
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Stage 2 — Main App
# ══════════════════════════════════════════════════════════════════════════════
else:
    # ── Portfolio maths ────────────────────────────────────────────────────────
    total_value    = sum(h["market_value"] for h in portfolio)
    total_gain     = sum(h["gain_loss"] for h in portfolio)
    total_cost     = sum(h["avg_cost"] * h["shares"] for h in portfolio)
    total_gain_pct = (total_gain / total_cost * 100) if total_cost else 0.0
    gain_color = "#00D084" if total_gain >= 0 else "#FF4757"
    gain_arrow = "▲" if total_gain >= 0 else "▼"

    portfolio_ctx = [
        {
            "ticker":        h["ticker"],
            "shares":        h["shares"],
            "avg_cost":      h["avg_cost"],
            "current_price": h["current_price"],
            "market_value":  h["market_value"],
            "gain_loss":     h["gain_loss"],
            "gain_loss_pct": h["gain_loss_pct"],
        }
        for h in portfolio
    ]

    # ── Session state ──────────────────────────────────────────────────────────
    if "messages" not in st.session_state:
        preview = ", ".join(f"{h['ticker']} ({h['shares']:g} sh)" for h in portfolio[:4])
        if len(portfolio) > 4:
            preview += f" +{len(portfolio) - 4} more"
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Portfolio loaded: {preview}.\n\nAsk me anything about your holdings — performance, risk, news, or strategy.",
                "sources": [],
            }
        ]
    if "show_add" not in st.session_state:
        st.session_state.show_add = False
    if "add_tab" not in st.session_state:
        st.session_state.add_tab = "manual"

    # ── Handle auto-send from prompt chips ────────────────────────────────────
    if st.session_state.get("pending_message"):
        msg = st.session_state.pop("pending_message")
        _send_chat(msg, portfolio_ctx)
        st.rerun()

    # ── Two-column layout ──────────────────────────────────────────────────────
    col_left, col_right = st.columns([35, 65])

    # ══════════════════════════════════════════════════════════════════════════
    # Left sidebar
    # ══════════════════════════════════════════════════════════════════════════
    with col_left:
        st.markdown('<div style="padding: 20px 16px 0;">', unsafe_allow_html=True)

        # ── Portfolio value ────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="port-value-block">
            <div class="port-value-label">Portfolio Value</div>
            <div class="port-value-number">${total_value:,.2f}</div>
            <div class="port-value-change" style="color:{gain_color};">
                {gain_arrow} ${abs(total_gain):,.2f} &nbsp;({total_gain_pct:+.2f}%)
                <span style="font-size:11px; color:#8B8FA8; font-weight:400;"> all time</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Holdings list ──────────────────────────────────────────────────────
        st.markdown('<div class="holdings-header">Holdings</div>', unsafe_allow_html=True)

        holdings_h = min(380, max(100, len(portfolio) * 68 + 16))
        holdings_box = st.container(height=holdings_h)
        with holdings_box:
            for i, h in enumerate(portfolio):
                gl_color = "#00D084" if h["gain_loss_pct"] >= 0 else "#FF4757"
                gl_arrow = "▲" if h["gain_loss_pct"] >= 0 else "▼"
                col_row, col_del = st.columns([11, 1])
                with col_row:
                    st.markdown(f"""
                    <div class="holding-row">
                        <div class="holding-left">
                            <div class="ticker">{h['ticker']}</div>
                            <div class="company">{h.get('name', h['ticker'])}</div>
                        </div>
                        <div class="holding-mid">{h['shares']:g} sh</div>
                        <div class="holding-right">
                            <div class="value">${h['market_value']:,.2f}</div>
                            <div class="pct" style="color:{gl_color};">{gl_arrow} {abs(h['gain_loss_pct']):.2f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if i < len(portfolio) - 1:
                        st.markdown('<div class="holding-divider"></div>', unsafe_allow_html=True)
                with col_del:
                    st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                    if st.button("×", key=f"del_{h['ticker']}"):
                        _, err = backend_delete(f"/api/v1/portfolio/{h['ticker']}")
                        if err:
                            st.error(err)
                        else:
                            del st.session_state["messages"]
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        # ── Charts ─────────────────────────────────────────────────────────────
        tickers = [h["ticker"] for h in portfolio]
        mkt_vals = [h["market_value"] for h in portfolio]
        gl_pcts  = [h["gain_loss_pct"] for h in portfolio]

        _BG = "#111118"
        _FONT_COLOR = "#8B8FA8"
        _CHART_MARGIN = dict(t=28, b=8, l=8, r=8)

        st.markdown('<div class="charts-header">Allocation</div>', unsafe_allow_html=True)
        fig_donut = go.Figure(go.Pie(
            labels=tickers,
            values=mkt_vals,
            hole=0.58,
            marker=dict(colors=_GREEN_PALETTE[:len(tickers)], line=dict(color=_BG, width=2)),
            textfont=dict(size=11, color="#FFFFFF"),
            hovertemplate="<b>%{label}</b><br>%{value:$,.0f}<br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            paper_bgcolor=_BG, plot_bgcolor=_BG,
            font=dict(color=_FONT_COLOR, size=11),
            margin=_CHART_MARGIN,
            height=190,
            showlegend=True,
            legend=dict(
                font=dict(size=10, color=_FONT_COLOR),
                bgcolor="rgba(0,0,0,0)",
                orientation="v",
                x=1.0, y=0.5,
            ),
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="charts-header">Gain / Loss %</div>', unsafe_allow_html=True)
        bar_colors = ["#00D084" if g >= 0 else "#FF4757" for g in gl_pcts]
        fig_bar = go.Figure(go.Bar(
            x=tickers,
            y=gl_pcts,
            marker_color=bar_colors,
            text=[f"{v:+.1f}%" for v in gl_pcts],
            textposition="outside",
            textfont=dict(size=10, color=_FONT_COLOR),
            hovertemplate="<b>%{x}</b><br>%{y:+.2f}%<extra></extra>",
        ))
        fig_bar.update_layout(
            paper_bgcolor=_BG, plot_bgcolor=_BG,
            font=dict(color=_FONT_COLOR, size=11),
            margin=dict(t=28, b=8, l=8, r=8),
            height=180,
            xaxis=dict(color=_FONT_COLOR, showgrid=False, tickfont=dict(size=11)),
            yaxis=dict(color=_FONT_COLOR, showgrid=True, gridcolor="#1E1E2E", ticksuffix="%", tickfont=dict(size=10)),
        )
        fig_bar.add_hline(y=0, line_color="#2A2A3E", line_width=1)
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

        # ── Add Holdings toggle ────────────────────────────────────────────────
        st.markdown('<div class="add-outlined">', unsafe_allow_html=True)
        add_label = "— Close" if st.session_state.show_add else "+ Add Holdings"
        if st.button(add_label, use_container_width=True, key="toggle_add"):
            st.session_state.show_add = not st.session_state.show_add
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.show_add:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown('<div style="background:#111118; border:1px solid #1E1E2E; border-radius:12px; padding:14px;">', unsafe_allow_html=True)

            tc1, tc2, tc3 = st.columns(3)
            with tc1:
                if st.button("Manual", use_container_width=True, key="tab_manual"):
                    st.session_state.add_tab = "manual"
                    st.rerun()
            with tc2:
                if st.button("Alpaca", use_container_width=True, key="tab_alpaca"):
                    st.session_state.add_tab = "alpaca"
                    st.rerun()
            with tc3:
                if st.button("CSV", use_container_width=True, key="tab_csv"):
                    st.session_state.add_tab = "csv"
                    st.rerun()

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            if st.session_state.add_tab == "manual":
                with st.form("add_manual_form", clear_on_submit=True):
                    a_ticker = st.text_input("Ticker", placeholder="e.g. TSLA")
                    ac1, ac2 = st.columns(2)
                    with ac1:
                        a_shares = st.number_input("Shares", min_value=0.0001, step=0.001, format="%.4f", value=1.0)
                    with ac2:
                        a_cost = st.number_input("Avg cost ($)", min_value=0.01, step=0.01, format="%.2f", value=100.0)
                    if st.form_submit_button("Add", use_container_width=True):
                        if not a_ticker.strip():
                            st.error("Ticker required.")
                        else:
                            result, err = backend_post("/api/v1/portfolio", {
                                "ticker": a_ticker.strip().upper(),
                                "name":   a_ticker.strip().upper(),
                                "shares": a_shares,
                                "avg_cost": a_cost,
                            })
                            if err:
                                st.error(err)
                            else:
                                st.success(f"Added {result['ticker']}!")
                                del st.session_state["messages"]
                                st.rerun()

            elif st.session_state.add_tab == "alpaca":
                st.markdown('<div style="font-size:12px; color:#8B8FA8; margin-bottom:10px;">Sync live positions from your Alpaca account.</div>', unsafe_allow_html=True)
                if st.button("Sync from Alpaca", use_container_width=True, key="sidebar_alpaca"):
                    with st.spinner("Syncing…"):
                        result, err = backend_post("/api/v1/portfolio/sync-alpaca", {})
                    if err:
                        st.error(err)
                    else:
                        st.success(f"Synced {len(result)} holding(s)!")
                        del st.session_state["messages"]
                        st.rerun()

            elif st.session_state.add_tab == "csv":
                up = st.file_uploader("CSV file", type=["csv"], label_visibility="collapsed", key="sidebar_csv")
                if up:
                    if st.button("Import", use_container_width=True, key="sidebar_csv_import"):
                        with st.spinner("Importing…"):
                            result, err = backend_upload("/api/v1/portfolio/upload-csv", up.getvalue(), up.name)
                        if err:
                            st.error(err)
                        else:
                            st.success(f"Imported {len(result)} holding(s)!")
                            del st.session_state["messages"]
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # Right chat area
    # ══════════════════════════════════════════════════════════════════════════
    with col_right:
        # ── Message history ────────────────────────────────────────────────────
        chat_h = 460 if st.session_state.show_add else 520
        chat_box = st.container(height=chat_h)
        with chat_box:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="msg-user">
                        <div class="bubble">{msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    content_html = md_render(msg["content"])
                    sources_html = ""
                    if msg.get("sources"):
                        pills = "".join(
                            f'<span class="source-pill">{s}</span>'
                            for s in msg["sources"]
                        )
                        sources_html = f'<div class="source-pills">{pills}</div>'
                    st.markdown(f"""
                    <div class="msg-ai">
                        <div class="ai-avatar">STK</div>
                        <div class="bubble">{content_html}{sources_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Suggested prompt chips (shown when only the context message exists) ─
        if len(st.session_state.messages) == 1:
            st.markdown('<div class="prompt-chips-label" style="padding: 8px 0 4px;">Try asking:</div>', unsafe_allow_html=True)
            chip_suggestions = [
                ("Analyse my risk",          "Analyse my risk exposure and portfolio diversification"),
                ("Best performer?",          "What's my best performing holding and why?"),
                ("Latest news",              "What's the latest news on my holdings?"),
                ("Should I rebalance?",      "Should I rebalance my portfolio? What changes would you suggest?"),
            ]
            ch1, ch2, ch3, ch4 = st.columns(4)
            for col, (label, full_prompt) in zip([ch1, ch2, ch3, ch4], chip_suggestions):
                with col:
                    if st.button(label, use_container_width=True, key=f"chip_{label}"):
                        st.session_state.pending_message = full_prompt
                        st.rerun()

        # ── Input row: [text input] [Send] [Clear] ─────────────────────────────
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        with st.form("chat_form", clear_on_submit=True):
            inp_col, send_col, clr_col = st.columns([7, 1, 1])
            with inp_col:
                user_input = st.text_input(
                    "message",
                    placeholder="Ask about your portfolio…",
                    label_visibility="collapsed",
                )
            with send_col:
                send = st.form_submit_button("Send", use_container_width=True)
            with clr_col:
                clear = st.form_submit_button(
                    "Clear", use_container_width=True, type="secondary"
                )

        if send and user_input.strip():
            _send_chat(user_input.strip(), portfolio_ctx)
            st.rerun()

        if clear:
            del st.session_state["messages"]
            st.rerun()
