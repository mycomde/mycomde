#!/usr/bin/env python3
"""
Market Heatmap Dashboard
Uses Finviz Elite API — gets all stocks in one call.
Runs in your browser at http://127.0.0.1:8050
"""

import os
import io
import json
import requests
import pandas as pd
from datetime import datetime, date
from dotenv import load_dotenv

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

load_dotenv()

API_KEY = os.getenv("FINVIZ_API_KEY", "")

INDICES = {
    "sp500": {"name": "S&P 500",    "filter": "idx_sp500", "proxy": "SPY"},
    "dji":   {"name": "Dow Jones",  "filter": "idx_dji",   "proxy": "DIA"},
    "ndq":   {"name": "NASDAQ 100", "filter": "idx_ndx",   "proxy": "QQQ"},
}

# Approximate market caps in billions USD — fallback when Finviz data is missing
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

# Stores (datetime, weighted_pct) snapshots for each index — builds the line chart
_index_history: dict[str, list] = {"sp500": [], "dji": [], "ndq": []}
_history_lock = __import__("threading").Lock()

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")


def load_history():
    """Load today's history from disk on startup."""
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
    """Persist today's history to disk."""
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
        # Use hardcoded fallback for any ticker where Finviz didn't return a cap
        df["market_cap"] = df.apply(
            lambda row: MARKET_CAPS.get(row["sym"], 5)
            if row["market_cap"] <= 1.0
            else row["market_cap"],
            axis=1
        )
        return df[["sym", "price", "pct_change", "market_cap"]]
    except Exception as e:
        print(f"  Finviz error: {e}")
        return pd.DataFrame()


def compute_weighted_pct(df):
    """Market-cap weighted average % change — same weighting as the heatmap boxes."""
    if df.empty:
        return None
    total = df["market_cap"].sum()
    if total == 0:
        return None
    return (df["pct_change"] * df["market_cap"]).sum() / total


def store_snapshot(index_key, wpct):
    """Append a weighted % snapshot, discard old days, then save to disk."""
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
            font=dict(color="#FF3333", size=15, family="monospace"),
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
                pad=dict(t=3, b=3, l=3, r=3)),
            textfont=dict(color="#FFFFFF", size=11, family="monospace"),
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
            text="Weighted line builds up during market hours — updates every 60s",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#333333", size=12, family="monospace"),
            xref="paper", yref="paper")
    else:
        times  = [h[0] for h in history]
        values = [h[1] for h in history]
        last   = values[-1]
        color  = "#22CC22" if last >= 0 else "#FF3333"

        fig.add_trace(go.Scatter(
            x=times, y=values,
            mode="lines",
            line=dict(color="#FF3333", width=1.5),
            fill="tozeroy",
            fillcolor="rgba(255,51,51,0.05)",
            hovertemplate="%{x|%H:%M}<br>%{y:+.3f}%<extra></extra>",
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="#2a2a2a", line_width=1)
        fig.add_annotation(
            x=times[-1], y=last,
            text=f"  {last:+.2f}%",
            showarrow=False, xanchor="left",
            font=dict(color=color, size=11, family="monospace"))

    fig.update_layout(
        paper_bgcolor="#000000", plot_bgcolor="#000000",
        margin=dict(t=5,b=5,l=70,r=90),
        font=dict(color="#555555", family="monospace"),
        xaxis=dict(showgrid=False, zeroline=False, showline=False,
                   tickfont=dict(color="#444444",size=10),
                   tickformat="%H:%M", rangeslider=dict(visible=False)),
        yaxis=dict(showgrid=False, zeroline=False, showline=False,
                   tickfont=dict(color="#444444",size=10),
                   ticksuffix="%", side="left"),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#111111",font_color="#CCCCCC",font_family="monospace"),
        dragmode="pan")
    return fig


app = dash.Dash(__name__, title="Market Heatmap", update_title=None)
app.layout = html.Div(
    style={"backgroundColor":"#000000","height":"100vh","fontFamily":"monospace",
           "padding":"10px 12px","boxSizing":"border-box",
           "display":"flex","flexDirection":"column"},
    children=[
        html.Div(style={"display":"flex","alignItems":"center","marginBottom":"8px"},
            children=[
                html.Span("MARKET HEATMAP",
                    style={"color":"#FF3333","fontSize":"13px","letterSpacing":"4px"}),
                html.Span(id="last-updated",
                    style={"color":"#333333","fontSize":"11px","marginLeft":"20px"}),
                html.Span(id="stocks-loaded",
                    style={"color":"#444444","fontSize":"11px","marginLeft":"12px"}),
            ]),
        dcc.Tabs(id="tab", value="sp500", style={"marginBottom":"8px"},
            colors={"border":"#000000","primary":"#FF3333","background":"#000000"},
            children=[
                dcc.Tab(label="S&P 500",    value="sp500",
                    style={"color":"#555555","backgroundColor":"#000000","fontSize":"11px"},
                    selected_style={"color":"#FF3333","backgroundColor":"#000000",
                                    "borderTop":"2px solid #FF3333","fontSize":"11px"}),
                dcc.Tab(label="Dow Jones",  value="dji",
                    style={"color":"#555555","backgroundColor":"#000000","fontSize":"11px"},
                    selected_style={"color":"#FF3333","backgroundColor":"#000000",
                                    "borderTop":"2px solid #FF3333","fontSize":"11px"}),
                dcc.Tab(label="NASDAQ 100", value="ndq",
                    style={"color":"#555555","backgroundColor":"#000000","fontSize":"11px"},
                    selected_style={"color":"#FF3333","backgroundColor":"#000000",
                                    "borderTop":"2px solid #FF3333","fontSize":"11px"}),
            ]),
        dcc.Graph(id="heatmap",
            config={"displayModeBar":False,"scrollZoom":True},
            style={"flex":"1 1 60%","minHeight":"0"}),
        html.Div(style={"borderTop":"1px solid #111111","margin":"6px 0"}),
        html.Span(id="line-label",
            style={"color":"#FF3333","fontSize":"10px",
                   "letterSpacing":"2px","marginBottom":"2px"}),
        dcc.Graph(id="line-chart",
            config={"displayModeBar":False,"scrollZoom":True},
            style={"flex":"0 0 28%","minHeight":"0"}),
        dcc.Interval(id="tick", interval=60_000, n_intervals=0),
    ])


@app.callback(
    Output("heatmap","figure"),
    Output("last-updated","children"),
    Output("stocks-loaded","children"),
    Input("tab","value"),
    Input("tick","n_intervals"))
def refresh_heatmap(index_key, _):
    df  = fetch_index_data(index_key)
    fig = build_heatmap(df)
    count = len(df) if not df.empty else 0
    now = datetime.now()

    wpct = compute_weighted_pct(df)
    if wpct is not None:
        store_snapshot(index_key, wpct)

    return fig, f"last updated {now.strftime('%H:%M:%S')}", f"{count} stocks loaded"


@app.callback(
    Output("line-chart","figure"),
    Output("line-label","children"),
    Input("tab","value"),
    Input("tick","n_intervals"))
def refresh_line(index_key, _):
    cfg = INDICES[index_key]
    fig = build_line_chart(index_key)

    with _history_lock:
        history = _index_history[index_key]
        last_wpct = history[-1][1] if history else None

    if last_wpct is not None:
        label = f"{cfg['name']}  ·  WEIGHTED INDEX  ·  {last_wpct:+.2f}%  ·  INTRADAY"
    else:
        label = f"{cfg['name']}  ·  WEIGHTED INDEX  ·  INTRADAY"

    return fig, label


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
