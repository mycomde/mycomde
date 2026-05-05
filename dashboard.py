#!/usr/bin/env python3
"""
Market Heatmap Dashboard
Uses Finviz Elite API — gets all stocks in one call.
Runs in your browser at http://127.0.0.1:8050
"""

import os
import io
import json
import time
import requests
import pandas as pd
from datetime import datetime, date
from dotenv import load_dotenv

import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go

_last_refresh_time = time.time()

load_dotenv()

API_KEY = os.getenv("FINVIZ_API_KEY", "")

INDICES = {
    "sp500": {"name": "S&P 500",    "filter": "idx_sp500"},
    "dji":   {"name": "Dow Jones",  "filter": "idx_dji"},
    "ndq":   {"name": "NASDAQ 100", "filter": "idx_ndx"},
}

MARKET_CAPS = {
    "AAPL":3000,"MSFT":3000,"NVDA":2500,"AMZN":2000,"META":1400,"GOOGL":1900,
    "GOOG":1900,"TSLA":800, "UNH":500,  "XOM":490,  "JPM":600,  "JNJ":390,
    "V":560,    "PG":370,   "MA":460,   "HD":370,   "CVX":340,  "MRK":310,
    "ABBV":300, "AVGO":820, "COST":380, "LLY":700,  "PEP":240,  "KO":260,
    "ADBE":275, "WMT":510,  "MCD":215,  "CRM":280,  "BAC":320,  "TMO":215,
    "CSCO":240, "ACN":225,  "ABT":195,  "NKE":145,  "DHR":205,  "TXN":175,
    "PM":155,   "NEE":125,  "DIS":195,  "CMCSA":175,"VZ":165,   "RTX":155,
    "BMY":145,  "QCOM":200, "T":145,    "HON":135,  "AMGN":175, "LOW":145,
    "UPS":125,  "INTC":115, "CAT":165,  "MS":195,   "GS":175,   "SBUX":95,
    "IBM":155,  "BLK":135,  "AXP":165,  "SPGI":125, "DE":105,   "GILD":88,
    "MDLZ":90,  "MMC":95,   "INTU":175, "ELV":105,  "PLD":95,   "TJX":115,
    "ADI":95,   "NOW":195,  "ISRG":155, "LRCX":95,  "REGN":85,  "MU":115,
    "ZTS":80,   "CI":90,    "SYK":125,  "AMAT":165, "HUM":75,   "ADP":115,
    "KLAC":95,  "ITW":80,   "MO":85,    "PANW":115, "APH":60,   "MELI":95,
    "EOG":55,   "FDX":60,   "SLB":55,   "NOC":70,   "GE":175,   "HCA":75,
    "EW":45,    "MMM":50,   "APD":50,   "BSX":65,   "SNPS":80,  "CDNS":75,
    "CME":70,   "FTNT":55,  "CTAS":75,  "ORLY":60,  "MRNA":45,  "NXPI":50,
    "PAYX":55,  "WM":65,    "PSA":50,   "F":45,     "GM":55,    "GD":75,
    "LMT":110,  "BA":95,    "UBER":80,  "ABNB":70,  "COIN":45,  "PLTR":60,
    "SNOW":50,  "DDOG":40,  "NET":38,   "CRWD":95,  "ZS":35,    "HLT":55,
    "MAR":65,   "CCI":45,   "AMT":90,   "EQIX":75,  "NFLX":290, "AMD":290,
    "PYPL":75,  "RIVN":15,  "LCID":7,   "NIO":12,   "XPEV":10,  "LI":20,
    "DKNG":15,  "RBLX":25,  "ROKU":12,  "SPOT":35,  "SHOP":80,  "DOCU":15,
    "ZM":20,    "OKTA":18,  "SPLK":22,  "CTSH":35,  "MCHP":40,  "ON":30,
    "AEP":42,   "XEL":30,   "WBD":25,   "SIRI":12,  "TEAM":50,  "ENPH":20,
    "VRTX":95,  "GEHC":40,  "DOW":40,   "WBA":18,   "TRV":48,   "AIG":48,
    "MET":50,   "PRU":40,   "AFL":45,   "CB":75,    "ALL":45,   "HIG":30,
    "CNC":40,   "MOH":22,   "IQV":35,   "LH":18,    "DGX":14,   "CVS":80,
    "MCK":65,   "SYY":20,   "GIS":35,   "CL":50,    "KMB":40,   "UNP":130,
    "NSC":60,   "CSX":55,   "ODFL":45,  "FAST":38,  "ASML":300, "TMUS":200,
    "BIDU":35,  "NTES":25,  "JD":22,    "PDD":200,  "ILMN":25,  "ALGN":20,
    "ANSS":15,  "EBAY":25,  "LULU":55,  "MTCH":12,  "WDAY":55,  "DXCM":30,
    "FANG":35,  "CPRT":55,  "ROST":45,  "IDXX":30,  "PCAR":40,  "VRSK":35,
    "EXC":35,   "BIIB":38,  "DLTR":22,  "TTWO":20,  "KDP":45,   "CEG":40,
    "AZN":220,  "MNST":55,  "CHTR":50,  "EMR":45,   "ETN":65,   "ROK":25,
    "HOOD":8,   "PTON":5,   "U":12,     "TWLO":10,  "PH":55,
    "WFC":230,  "USB":60,   "PNC":70,   "TFC":50,   "FITB":25,
    "KEY":18,   "CFG":20,   "RF":20,    "HBAN":18,  "MTB":25,   "C":145,
}

_index_history: dict[str, list] = {"sp500": [], "dji": [], "ndq": []}
_history_lock = __import__("threading").Lock()
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            raw = json.load(f)
        today = date.today().isoformat()
        for key in _index_history:
            entries = raw.get(key, [])
            _index_history[key] = [
                (datetime.fromisoformat(t), v)
                for t, v in entries
                if t[:10] == today
            ]
    except Exception:
        pass


def save_history():
    try:
        raw = {
            key: [(t.isoformat(), v) for t, v in vals]
            for key, vals in _index_history.items()
        }
        with open(HISTORY_FILE, "w") as f:
            json.dump(raw, f)
    except Exception:
        pass


load_history()


def parse_market_cap(value):
    try:
        v = str(value).strip()
        if v.endswith("T"): return float(v[:-1]) * 1000
        if v.endswith("B"): return float(v[:-1])
        if v.endswith("M"): return float(v[:-1]) / 1000
        return 0.0
    except:
        return 0.0


def parse_change(value):
    try:
        return float(str(value).replace("%", "").strip())
    except:
        return 0.0


def fetch_index_data(index_key):
    idx_filter = INDICES[index_key]["filter"]
    url = f"https://elite.finviz.com/export?v=111&f={idx_filter}&auth={API_KEY}"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df = df.rename(columns={
            "Ticker":     "sym",
            "Price":      "price",
            "Change":     "pct_change",
            "Market Cap": "market_cap",
        })
        df["pct_change"] = df["pct_change"].apply(parse_change)
        df["market_cap"] = df["market_cap"].apply(parse_market_cap)
        df["price"]      = pd.to_numeric(df["price"], errors="coerce").fillna(0)
        df["market_cap"] = df.apply(
            lambda row: MARKET_CAPS.get(row["sym"], 5)
            if row["market_cap"] <= 1.0
            else row["market_cap"],
            axis=1
        )
        return df[["sym", "price", "pct_change", "market_cap"]]
    except Exception as e:
        print(f"  Finviz error [{index_key}]: {e}")
        return pd.DataFrame()


def compute_weighted_pct(df):
    if df.empty:
        return None
    total = df["market_cap"].sum()
    if total == 0:
        return None
    return (df["pct_change"] * df["market_cap"]).sum() / total


def store_snapshot(index_key, wpct):
    now = datetime.now()
    today = now.date()
    with _history_lock:
        _index_history[index_key].append((now, wpct))
        _index_history[index_key] = [
            (t, v) for t, v in _index_history[index_key]
            if t.date() == today
        ]
    save_history()


def build_heatmap(df):
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(
            text="Loading data...",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#FF3333", size=13, family="monospace"),
            xref="paper", yref="paper")
    else:
        max_abs = max(df["pct_change"].abs().max(), 0.5)
        df = df.copy()
        df["label"] = df["sym"] + "  " + df["pct_change"].apply(lambda x: f"{x:+.2f}%")
        fig.add_trace(go.Treemap(
            labels=df["label"],
            parents=[""] * len(df),
            values=df["market_cap"].clip(lower=0.1),
            customdata=list(zip(df["sym"], df["pct_change"], df["price"])),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Change: %{customdata[1]:+.2f}%<br>"
                "Price:  $%{customdata[2]:.2f}<extra></extra>"
            ),
            marker=dict(
                colors=df["pct_change"],
                colorscale=[
                    [0.00,"#8B0000"],[0.35,"#CC2222"],[0.48,"#550000"],
                    [0.50,"#111111"],[0.52,"#005500"],[0.65,"#22CC22"],[1.00,"#00FF44"],
                ],
                cmid=0, cmin=-max_abs, cmax=max_abs, showscale=False,
                pad=dict(t=2, b=2, l=2, r=2)),
            textfont=dict(color="#FFFFFF", size=10, family="monospace"),
            tiling=dict(squarifyratio=1)))
    fig.update_layout(
        paper_bgcolor="#000000", plot_bgcolor="#000000",
        margin=dict(t=0,b=0,l=0,r=0),
        font=dict(color="#FFFFFF", family="monospace"))
    return fig


def build_line_chart(index_key):
    with _history_lock:
        history = list(_index_history[index_key])
    fig = go.Figure()
    if len(history) < 2:
        fig.add_annotation(
            text="Builds during market hours",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#333333", size=11, family="monospace"),
            xref="paper", yref="paper")
    else:
        times  = [h[0] for h in history]
        values = [h[1] for h in history]
        last   = values[-1]
        color  = "#22CC22" if last >= 0 else "#FF3333"
        fig.add_trace(go.Scatter(
            x=times, y=values, mode="lines",
            line=dict(color="#FF3333", width=1.5),
            fill="tozeroy", fillcolor="rgba(255,51,51,0.05)",
            hovertemplate="%{x|%H:%M}<br>%{y:+.3f}%<extra></extra>"))
        fig.add_hline(y=0, line_dash="dot", line_color="#2a2a2a", line_width=1)
        fig.add_annotation(
            x=times[-1], y=last,
            text=f"  {last:+.2f}%",
            showarrow=False, xanchor="left",
            font=dict(color=color, size=11, family="monospace"))
    fig.update_layout(
        paper_bgcolor="#000000", plot_bgcolor="#000000",
        margin=dict(t=5,b=5,l=55,r=70),
        font=dict(color="#555555", family="monospace"),
        xaxis=dict(showgrid=False, zeroline=False, showline=False,
                   tickfont=dict(color="#444444",size=9),
                   tickformat="%H:%M", rangeslider=dict(visible=False)),
        yaxis=dict(showgrid=False, zeroline=False, showline=False,
                   tickfont=dict(color="#444444",size=9),
                   ticksuffix="%", side="left"),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#111111",font_color="#CCCCCC",font_family="monospace"),
        dragmode="pan",
        uirevision=index_key)
    return fig


# ─── Styles ───────────────────────────────────────────────────────────────────

BTN_BASE = {
    "background": "#111111",
    "color": "#555555",
    "border": "1px solid #222222",
    "borderRadius": "3px",
    "padding": "3px 8px",
    "fontSize": "11px",
    "fontFamily": "monospace",
    "cursor": "pointer",
    "marginLeft": "4px",
}
BTN_ACTIVE = {**BTN_BASE, "background": "#FF3333", "color": "#FFFFFF", "border": "1px solid #FF3333"}

TAB_STYLE         = {"color":"#555555","backgroundColor":"#000000","fontSize":"11px"}
TAB_SELECTED      = {"color":"#FF3333","backgroundColor":"#000000",
                     "borderTop":"2px solid #FF3333","fontSize":"11px"}

INDEX_KEYS = ["sp500", "dji", "ndq"]
INDEX_NAMES = {"sp500": "S&P 500", "dji": "Dow Jones", "ndq": "NASDAQ 100"}

# ─── App ──────────────────────────────────────────────────────────────────────

app = dash.Dash(__name__, title="Market Heatmap", update_title=None)

app.layout = html.Div(
    style={"backgroundColor":"#000000","height":"100vh","fontFamily":"monospace",
           "padding":"10px 12px","boxSizing":"border-box",
           "display":"flex","flexDirection":"column"},
    children=[

        # ── Header ────────────────────────────────────────────────────────────
        html.Div(
            style={"display":"flex","alignItems":"center","marginBottom":"8px","flexShrink":"0"},
            children=[
                html.Span("MARKET HEATMAP",
                    style={"color":"#FF3333","fontSize":"13px","letterSpacing":"4px"}),
                html.Span(id="last-updated",
                    style={"color":"#333333","fontSize":"11px","marginLeft":"20px"}),
                html.Span(id="stocks-loaded",
                    style={"color":"#444444","fontSize":"11px","marginLeft":"12px"}),
                # Layout buttons — right side
                html.Div(
                    style={"marginLeft":"auto","display":"flex","alignItems":"center"},
                    children=[
                        html.Span(id="countdown",
                            style={"color":"#555555","fontSize":"10px","fontFamily":"monospace",
                                   "letterSpacing":"1px","marginRight":"16px"}),
                        html.Span("LAYOUT", style={"color":"#333","fontSize":"10px",
                                                    "letterSpacing":"2px","marginRight":"6px"}),
                        html.Button("1", id="btn-1", n_clicks=0, style=BTN_ACTIVE),
                        html.Button("2", id="btn-2", n_clicks=0, style=BTN_BASE),
                        html.Button("3", id="btn-3", n_clicks=0, style=BTN_BASE),
                    ]
                ),
            ]),

        # State stores
        dcc.Store(id="layout-store", data="1"),
        dcc.Store(id="pair-store", data=["sp500", "dji"]),

        # ── Layout 1: single index with tabs ──────────────────────────────────
        html.Div(id="view-1",
            style={"display":"flex","flexDirection":"column","flex":"1","minHeight":"0"},
            children=[
                dcc.Tabs(id="tab", value="sp500", style={"marginBottom":"6px","flexShrink":"0"},
                    colors={"border":"#000000","primary":"#FF3333","background":"#000000"},
                    children=[
                        dcc.Tab(label="S&P 500",    value="sp500",
                            style=TAB_STYLE, selected_style=TAB_SELECTED),
                        dcc.Tab(label="Dow Jones",  value="dji",
                            style=TAB_STYLE, selected_style=TAB_SELECTED),
                        dcc.Tab(label="NASDAQ 100", value="ndq",
                            style=TAB_STYLE, selected_style=TAB_SELECTED),
                    ]),
                dcc.Graph(id="heatmap-1",
                    config={"displayModeBar":False,"scrollZoom":True},
                    style={"flex":"1 1 62%","minHeight":"0"}),
                html.Div(style={"borderTop":"1px solid #111","margin":"4px 0","flexShrink":"0"}),
                html.Span(id="line-label-1",
                    style={"color":"#FF3333","fontSize":"10px","letterSpacing":"2px",
                           "marginBottom":"2px","flexShrink":"0"}),
                dcc.Graph(id="line-1",
                    config={"displayModeBar":False,"scrollZoom":True},
                    style={"flex":"0 0 28%","minHeight":"0"}),
            ]),

        # ── Layout 2: pick any 2 indices ──────────────────────────────────────
        html.Div(id="view-2",
            style={"display":"none","flexDirection":"column","flex":"1","minHeight":"0"},
            children=[
                # Picker row
                html.Div(id="picker-2",
                    style={"display":"flex","gap":"6px","marginBottom":"6px","flexShrink":"0"},
                    children=[
                        html.Span("SHOW:", style={"color":"#333","fontSize":"10px",
                                                   "letterSpacing":"2px","alignSelf":"center"}),
                        html.Button("S&P 500",    id="p2-sp500", n_clicks=0,
                            style={**BTN_ACTIVE, "marginLeft":"6px"}),
                        html.Button("Dow Jones",  id="p2-dji",   n_clicks=0,
                            style={**BTN_ACTIVE}),
                        html.Button("NASDAQ 100", id="p2-ndq",   n_clicks=0,
                            style={**BTN_BASE}),
                    ]),
                # Two panels side by side
                html.Div(style={"display":"flex","flex":"1 1 62%","gap":"4px","minHeight":"0"},
                    children=[
                        html.Div(style={"flex":"1","display":"flex","flexDirection":"column","minHeight":"0"},
                            children=[
                                html.Span(id="label-2a",
                                    style={"color":"#FF3333","fontSize":"10px","letterSpacing":"2px",
                                           "marginBottom":"2px","flexShrink":"0"}),
                                dcc.Graph(id="heatmap-2a",
                                    config={"displayModeBar":False,"scrollZoom":True},
                                    style={"flex":"1","minHeight":"0"}),
                            ]),
                        html.Div(style={"flex":"1","display":"flex","flexDirection":"column","minHeight":"0"},
                            children=[
                                html.Span(id="label-2b",
                                    style={"color":"#FF3333","fontSize":"10px","letterSpacing":"2px",
                                           "marginBottom":"2px","flexShrink":"0"}),
                                dcc.Graph(id="heatmap-2b",
                                    config={"displayModeBar":False,"scrollZoom":True},
                                    style={"flex":"1","minHeight":"0"}),
                            ]),
                    ]),
                html.Div(style={"borderTop":"1px solid #111","margin":"4px 0","flexShrink":"0"}),
                html.Div(style={"display":"flex","flex":"0 0 28%","gap":"4px","minHeight":"0"},
                    children=[
                        dcc.Graph(id="line-2a",
                            config={"displayModeBar":False,"scrollZoom":True},
                            style={"flex":"1","minHeight":"0"}),
                        dcc.Graph(id="line-2b",
                            config={"displayModeBar":False,"scrollZoom":True},
                            style={"flex":"1","minHeight":"0"}),
                    ]),
            ]),

        # ── Layout 3: all 3 indices ────────────────────────────────────────────
        html.Div(id="view-3",
            style={"display":"none","flexDirection":"column","flex":"1","minHeight":"0"},
            children=[
                html.Div(style={"display":"flex","flex":"1 1 62%","gap":"4px","minHeight":"0"},
                    children=[
                        html.Div(style={"flex":"1","display":"flex","flexDirection":"column","minHeight":"0"},
                            children=[
                                html.Span("S&P 500",
                                    style={"color":"#FF3333","fontSize":"10px","letterSpacing":"2px",
                                           "marginBottom":"2px","flexShrink":"0"}),
                                dcc.Graph(id="heatmap-3a",
                                    config={"displayModeBar":False,"scrollZoom":True},
                                    style={"flex":"1","minHeight":"0"}),
                            ]),
                        html.Div(style={"flex":"1","display":"flex","flexDirection":"column","minHeight":"0"},
                            children=[
                                html.Span("DOW JONES",
                                    style={"color":"#FF3333","fontSize":"10px","letterSpacing":"2px",
                                           "marginBottom":"2px","flexShrink":"0"}),
                                dcc.Graph(id="heatmap-3b",
                                    config={"displayModeBar":False,"scrollZoom":True},
                                    style={"flex":"1","minHeight":"0"}),
                            ]),
                        html.Div(style={"flex":"1","display":"flex","flexDirection":"column","minHeight":"0"},
                            children=[
                                html.Span("NASDAQ 100",
                                    style={"color":"#FF3333","fontSize":"10px","letterSpacing":"2px",
                                           "marginBottom":"2px","flexShrink":"0"}),
                                dcc.Graph(id="heatmap-3c",
                                    config={"displayModeBar":False,"scrollZoom":True},
                                    style={"flex":"1","minHeight":"0"}),
                            ]),
                    ]),
                html.Div(style={"borderTop":"1px solid #111","margin":"4px 0","flexShrink":"0"}),
                html.Div(style={"display":"flex","flex":"0 0 28%","gap":"4px","minHeight":"0"},
                    children=[
                        dcc.Graph(id="line-3a",
                            config={"displayModeBar":False,"scrollZoom":True},
                            style={"flex":"1","minHeight":"0"}),
                        dcc.Graph(id="line-3b",
                            config={"displayModeBar":False,"scrollZoom":True},
                            style={"flex":"1","minHeight":"0"}),
                        dcc.Graph(id="line-3c",
                            config={"displayModeBar":False,"scrollZoom":True},
                            style={"flex":"1","minHeight":"0"}),
                    ]),
            ]),

        dcc.Interval(id="tick", interval=60_000, n_intervals=0),
        dcc.Interval(id="tick-1s", interval=1_000, n_intervals=0),
    ])


# ─── Layout toggle ────────────────────────────────────────────────────────────

@app.callback(
    Output("layout-store", "data"),
    Output("view-1", "style"),
    Output("view-2", "style"),
    Output("view-3", "style"),
    Output("btn-1", "style"),
    Output("btn-2", "style"),
    Output("btn-3", "style"),
    Input("btn-1", "n_clicks"),
    Input("btn-2", "n_clicks"),
    Input("btn-3", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_layout(n1, n2, n3):
    triggered = ctx.triggered_id
    show  = {"display":"flex","flexDirection":"column","flex":"1","minHeight":"0"}
    hide  = {"display":"none"}
    if triggered == "btn-2":
        return "2", hide, show, hide, BTN_BASE, BTN_ACTIVE, BTN_BASE
    if triggered == "btn-3":
        return "3", hide, hide, show, BTN_BASE, BTN_BASE, BTN_ACTIVE
    return "1", show, hide, hide, BTN_ACTIVE, BTN_BASE, BTN_BASE


# ─── Layout 2 pair picker ─────────────────────────────────────────────────────

@app.callback(
    Output("pair-store",  "data"),
    Output("p2-sp500", "style"),
    Output("p2-dji",   "style"),
    Output("p2-ndq",   "style"),
    Input("p2-sp500", "n_clicks"),
    Input("p2-dji",   "n_clicks"),
    Input("p2-ndq",   "n_clicks"),
    State("pair-store", "data"),
    prevent_initial_call=True,
)
def pick_pair(n_sp, n_dji, n_ndq, current_pair):
    triggered = ctx.triggered_id
    key_map = {"p2-sp500": "sp500", "p2-dji": "dji", "p2-ndq": "ndq"}
    clicked = key_map[triggered]

    pair = list(current_pair)
    if clicked in pair:
        if len(pair) > 1:
            pair.remove(clicked)
    else:
        if len(pair) >= 2:
            pair.pop(0)
        pair.append(clicked)

    styles = {
        "p2-sp500": BTN_ACTIVE if "sp500" in pair else BTN_BASE,
        "p2-dji":   BTN_ACTIVE if "dji"   in pair else BTN_BASE,
        "p2-ndq":   BTN_ACTIVE if "ndq"   in pair else BTN_BASE,
    }
    return pair, styles["p2-sp500"], styles["p2-dji"], styles["p2-ndq"]


# ─── Layout 1 callbacks ───────────────────────────────────────────────────────

@app.callback(
    Output("heatmap-1",    "figure"),
    Output("last-updated", "children"),
    Output("stocks-loaded","children"),
    Input("tab",  "value"),
    Input("tick", "n_intervals"),
)
def refresh_heatmap_1(index_key, _):
    global _last_refresh_time
    df  = fetch_index_data(index_key)
    fig = build_heatmap(df)
    wpct = compute_weighted_pct(df)
    if wpct is not None:
        store_snapshot(index_key, wpct)
    count = len(df) if not df.empty else 0
    _last_refresh_time = time.time()
    return fig, f"last updated {datetime.now().strftime('%H:%M:%S')}", f"{count} stocks"


@app.callback(
    Output("line-1",       "figure"),
    Output("line-label-1", "children"),
    Input("tab",  "value"),
    Input("tick", "n_intervals"),
)
def refresh_line_1(index_key, _):
    fig = build_line_chart(index_key)
    with _history_lock:
        h = _index_history[index_key]
        last = h[-1][1] if h else None
    name = INDEX_NAMES[index_key]
    label = f"{name}  ·  WEIGHTED  ·  {last:+.2f}%" if last is not None else f"{name}  ·  WEIGHTED"
    return fig, label


# ─── Layout 2 callbacks ───────────────────────────────────────────────────────

@app.callback(
    Output("heatmap-2a", "figure"),
    Output("heatmap-2b", "figure"),
    Output("line-2a",    "figure"),
    Output("line-2b",    "figure"),
    Output("label-2a",   "children"),
    Output("label-2b",   "children"),
    Input("tick",         "n_intervals"),
    Input("pair-store",   "data"),
    State("layout-store", "data"),
)
def refresh_layout_2(_, pair, layout):
    if layout != "2":
        raise dash.exceptions.PreventUpdate
    keys = (pair + ["sp500", "dji"])[:2]
    dfs  = [fetch_index_data(k) for k in keys]
    for k, df in zip(keys, dfs):
        wpct = compute_weighted_pct(df)
        if wpct is not None:
            store_snapshot(k, wpct)
    heatmaps = [build_heatmap(df) for df in dfs]
    lines    = [build_line_chart(k) for k in keys]
    labels   = [INDEX_NAMES[k].upper() for k in keys]
    return heatmaps[0], heatmaps[1], lines[0], lines[1], labels[0], labels[1]


# ─── Layout 3 callbacks ───────────────────────────────────────────────────────

@app.callback(
    Output("heatmap-3a", "figure"),
    Output("heatmap-3b", "figure"),
    Output("heatmap-3c", "figure"),
    Output("line-3a",    "figure"),
    Output("line-3b",    "figure"),
    Output("line-3c",    "figure"),
    Input("tick",         "n_intervals"),
    State("layout-store", "data"),
)
def refresh_layout_3(_, layout):
    if layout != "3":
        raise dash.exceptions.PreventUpdate
    keys = ["sp500", "dji", "ndq"]
    dfs  = [fetch_index_data(k) for k in keys]
    for k, df in zip(keys, dfs):
        wpct = compute_weighted_pct(df)
        if wpct is not None:
            store_snapshot(k, wpct)
    heatmaps = [build_heatmap(df) for df in dfs]
    lines    = [build_line_chart(k) for k in keys]
    return heatmaps[0], heatmaps[1], heatmaps[2], lines[0], lines[1], lines[2]


# ─── Countdown callback ───────────────────────────────────────────────────────

@app.callback(
    Output("countdown", "children"),
    Input("tick-1s", "n_intervals"),
)
def update_countdown(_):
    elapsed = int(time.time() - _last_refresh_time)
    remaining = max(0, 60 - elapsed)
    return f"NEXT UPDATE  {remaining}s"


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*52)
    print("  MARKET HEATMAP  —  Finviz Elite")
    print("="*52)
    if not API_KEY or API_KEY == "your_api_key_here":
        print("\n  WARNING: No API key!")
        print("  Open .env and add your FINVIZ_API_KEY\n")
    else:
        print(f"\n  Opening: http://127.0.0.1:8050")
        print(f"  Stop:    Ctrl+C\n")
    app.run(debug=False, host="127.0.0.1", port=8050)
