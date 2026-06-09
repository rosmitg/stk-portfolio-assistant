import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="STK Portfolio Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp { background-color: #0D1117; color: #E6EDF3; }

    [data-testid="stSidebar"] { background-color: #161B22; }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #161B22;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] { color: #8B949E; font-weight: 500; }
    .stTabs [aria-selected="true"] {
        background-color: #00C853;
        color: #0D1117 !important;
        border-radius: 6px;
    }

    .stTextInput > div > div > input {
        background-color: #161B22;
        color: #E6EDF3;
        border: 1px solid #30363D;
        border-radius: 8px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #00C853;
        box-shadow: 0 0 0 2px rgba(0,200,83,0.2);
    }

    .stButton > button {
        background-color: #00C853;
        color: #0D1117;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: background-color 0.15s;
    }
    .stButton > button:hover { background-color: #00E676; color: #0D1117; }

    [data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 1rem;
    }
    [data-testid="stMetricValue"] { color: #00C853; }

    .chat-user { display: flex; justify-content: flex-end; margin: 8px 0; }
    .chat-user .bubble {
        background-color: #00C853;
        color: #0D1117;
        padding: 10px 16px;
        border-radius: 18px 18px 4px 18px;
        max-width: 70%;
        font-size: 0.95rem;
        font-weight: 500;
        word-wrap: break-word;
    }
    .chat-ai { display: flex; justify-content: flex-start; margin: 8px 0; }
    .chat-ai .bubble {
        background-color: #1C2128;
        color: #E6EDF3;
        padding: 10px 16px;
        border-radius: 18px 18px 18px 4px;
        max-width: 70%;
        font-size: 0.95rem;
        border: 1px solid #30363D;
        word-wrap: break-word;
    }
    .chat-label { font-size: 0.75rem; color: #8B949E; margin-bottom: 3px; }

    .source-chip {
        display: inline-block;
        background-color: #1C2128;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.75rem;
        color: #8B949E;
        margin: 2px;
    }

    .error-box {
        background-color: #2D1B1B;
        border: 1px solid #FF4B4B;
        border-radius: 8px;
        padding: 1rem;
        color: #FF8080;
    }

    [data-testid="stDataFrame"] { border: 1px solid #30363D; border-radius: 8px; }

    hr { border-color: #30363D; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def backend_get(path: str):
    try:
        r = requests.get(f"{BACKEND_URL}{path}", timeout=5)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the backend. Make sure the API server is running on " + BACKEND_URL
    except requests.exceptions.Timeout:
        return None, "Backend request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        return None, f"Backend returned {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def backend_post(path: str, payload: dict):
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=30)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the backend. Make sure the API server is running on " + BACKEND_URL
    except requests.exceptions.Timeout:
        return None, "Request timed out — the AI is taking too long to respond."
    except requests.exceptions.HTTPError as e:
        return None, f"Backend returned {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <span style="font-size:1.6rem; font-weight:700; color:#E6EDF3;">📈 STK Portfolio Assistant</span><br>
    <span style="font-size:0.9rem; color:#8B949E;">AI-powered portfolio analysis &amp; insights</span>
</div>
""", unsafe_allow_html=True)

tab_chat, tab_portfolio = st.tabs(["💬  Chat", "📊  Portfolio"])

# ── Chat tab ──────────────────────────────────────────────────────────────────
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center; padding:3rem 0; color:#8B949E;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">🤖</div>
            <div style="font-size:1rem; font-weight:500; color:#E6EDF3;">Ask me about your portfolio</div>
            <div style="font-size:0.85rem; margin-top:0.5rem;">
                Try: "What's my biggest holding?" or "Analyse my portfolio risk"
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <div>
                        <div class="chat-label" style="text-align:right;">You</div>
                        <div class="bubble">{msg["content"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                sources_html = ""
                if msg.get("sources"):
                    chips = "".join(
                        f'<span class="source-chip">{s}</span>' for s in msg["sources"]
                    )
                    sources_html = f'<div style="margin-top:6px;">{chips}</div>'
                st.markdown(f"""
                <div class="chat-ai">
                    <div>
                        <div class="chat-label">STK Assistant</div>
                        <div class="bubble">{msg["content"]}{sources_html}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_input = st.text_input(
                "message",
                placeholder="Ask about your portfolio…",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        with st.spinner("Thinking…"):
            data, err = backend_post("/api/v1/chat", {"message": user_input.strip()})
        if err:
            st.markdown(f'<div class="error-box">⚠️ {err}</div>', unsafe_allow_html=True)
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": data["answer"],
                "sources": data.get("sources", []),
            })
        st.rerun()

    if st.session_state.messages:
        if st.button("Clear chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()

# ── Portfolio tab ─────────────────────────────────────────────────────────────
with tab_portfolio:
    data, err = backend_get("/api/v1/portfolio")

    if err:
        st.markdown(f'<div class="error-box">⚠️ {err}</div>', unsafe_allow_html=True)
    else:
        df = pd.DataFrame(data)

        total_value = df["market_value"].sum()
        total_gain = df["gain_loss"].sum()
        total_cost = (df["avg_cost"] * df["shares"]).sum()
        total_gain_pct = (total_gain / total_cost * 100) if total_cost else 0.0
        best = df.loc[df["gain_loss_pct"].idxmax()]
        worst = df.loc[df["gain_loss_pct"].idxmin()]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Portfolio Value", f"${total_value:,.2f}")
        c2.metric("Total Gain / Loss", f"${total_gain:+,.2f}", f"{total_gain_pct:+.2f}%")
        c3.metric("Best Performer", best["ticker"], f"{best['gain_loss_pct']:+.2f}%")
        c4.metric("Worst Performer", worst["ticker"], f"{worst['gain_loss_pct']:+.2f}%")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        col_pie, col_bar = st.columns(2)

        _DARK_BG = "#0D1117"
        _FONT = "#E6EDF3"
        _MUTED = "#8B949E"
        _GRID = "#21262D"
        _GREEN_PALETTE = ["#00C853", "#00E676", "#69F0AE", "#1B5E20", "#33691E",
                          "#00BFA5", "#76FF03", "#B9F6CA"]

        with col_pie:
            fig_pie = px.pie(
                df,
                names="ticker",
                values="market_value",
                title="Portfolio Allocation",
                hole=0.55,
                color_discrete_sequence=_GREEN_PALETTE,
            )
            fig_pie.update_layout(
                paper_bgcolor=_DARK_BG,
                plot_bgcolor=_DARK_BG,
                font_color=_FONT,
                title_font_color=_FONT,
                legend=dict(font=dict(color=_MUTED)),
                margin=dict(t=50, b=10, l=10, r=10),
            )
            fig_pie.update_traces(textfont_color="#0D1117", textfont_size=12)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_bar:
            bar_colors = ["#00C853" if g >= 0 else "#FF4B4B" for g in df["gain_loss_pct"]]
            fig_bar = go.Figure(go.Bar(
                x=df["ticker"],
                y=df["gain_loss_pct"],
                marker_color=bar_colors,
                text=[f"{v:+.1f}%" for v in df["gain_loss_pct"]],
                textposition="outside",
                textfont=dict(color=_FONT, size=12),
            ))
            fig_bar.update_layout(
                title="Gain / Loss %",
                paper_bgcolor=_DARK_BG,
                plot_bgcolor=_DARK_BG,
                font_color=_FONT,
                title_font_color=_FONT,
                xaxis=dict(color=_MUTED, gridcolor=_GRID, showgrid=False),
                yaxis=dict(color=_MUTED, gridcolor=_GRID, ticksuffix="%"),
                margin=dict(t=50, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("#### Holdings")
        display_df = df.rename(columns={
            "ticker": "Ticker",
            "name": "Name",
            "shares": "Shares",
            "avg_cost": "Avg Cost",
            "current_price": "Price",
            "market_value": "Market Value",
            "gain_loss": "Gain / Loss",
            "gain_loss_pct": "G/L %",
        }).copy()
        display_df["Avg Cost"] = display_df["Avg Cost"].map("${:,.2f}".format)
        display_df["Price"] = display_df["Price"].map("${:,.2f}".format)
        display_df["Market Value"] = display_df["Market Value"].map("${:,.2f}".format)
        display_df["Gain / Loss"] = display_df["Gain / Loss"].map("${:+,.2f}".format)
        display_df["G/L %"] = display_df["G/L %"].map("{:+.2f}%".format)

        st.dataframe(display_df, use_container_width=True, hide_index=True)
