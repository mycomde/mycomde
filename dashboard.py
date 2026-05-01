#!/usr/bin/env python3
"""
Market Heatmap Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━
Tracks S&P 500, Dow Jones, and NASDAQ 100 in real time.
Data from Polygon.io. Runs in your browser at http://127.0.0.1:8050
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, date
from dotenv import load_dotenv

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

load_dotenv()

# ─── API ─────────────────────────────────────────────────────────────────────

API_KEY  = os.getenv("POLYGON_API_KEY", "")
BASE_URL = "https://api.polygon.io"

# ─── Stock Lists ─────────────────────────────────────────────────────────────

DOW_30 = [
    "AAPL", "AMGN", "AXP",  "BA",   "CAT",  "CRM",  "CSCO", "CVX",  "DIS",  "DOW",
    "GS",   "HD",   "HON",  "IBM",  "INTC", "JNJ",  "JPM",  "KO",   "MCD",  "MMM",
    "MRK",  "MSFT", "NKE",  "PG",   "TRV",  "UNH",  "V",    "VZ",   "WBA",  "WMT",
]

NASDAQ_100 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META",  "TSLA", "GOOGL","GOOG", "AVGO", "COST",
    "NFLX", "AMD",  "ADBE", "ASML", "PEP",   "QCOM", "CSCO", "TMUS", "INTC", "INTU",
    "CMCSA","TXN",  "AMGN", "AMAT", "ISRG",  "MU",   "LRCX", "KLAC", "MELI", "REGN",
    "PANW", "SNPS", "CDNS", "ADI",  "ABNB",  "CRWD", "MRNA", "FTNT", "MRVL", "KDP",
    "ORLY", "CEG",  "CTAS", "MAR",  "AZN",   "MNST", "PAYX", "CHTR", "NXPI", "WDAY",
    "DXCM", "FANG", "ODFL", "CPRT", "ROST",  "IDXX", "PCAR", "FAST", "VRSK", "EXC",
    "BIIB", "DLTR", "ALGN", "ANSS", "DDOG",  "ILMN", "ZS",   "TEAM", "ENPH", "VRTX",
    "GEHC", "TTWO", "EBAY", "LULU", "OKTA",  "CTSH", "MCHP", "ON",   "GILD", "AEP",
    "XEL",  "CSGP", "CCEP", "SBUX", "PYPL",  "MDLZ", "WBD",  "JD",   "PDD",  "SIRI",
    "BIDU", "NTES", "ZM",   "SPLK", "TTWO",  "MTCH", "RIVN", "LCID", "COIN", "HOOD",
]

SP500 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META",  "GOOGL","GOOG", "TSLA", "UNH",  "XOM",
    "JPM",  "JNJ",  "V",    "PG",   "MA",    "HD",   "CVX",  "MRK",  "ABBV", "AVGO",
    "COST", "LLY",  "PEP",  "KO",   "ADBE",  "WMT",  "MCD",  "CRM",  "BAC",  "TMO",
    "CSCO", "ACN",  "ABT",  "NKE",  "DHR",   "TXN",  "PM",   "NEE",  "DIS",  "CMCSA",
    "VZ",   "RTX",  "BMY",  "QCOM", "T",     "HON",  "AMGN", "LOW",  "UPS",  "INTC",
    "CAT",  "MS",   "GS",   "SBUX", "IBM",   "BLK",  "AXP",  "SPGI", "DE",   "GILD",
    "MDLZ", "MMC",  "INTU", "ELV",  "PLD",   "TJX",  "ADI",  "NOW",  "ISRG", "LRCX",
    "REGN", "MU",   "ZTS",  "CI",   "SYK",   "AMAT", "HUM",  "ADP",  "KLAC", "ITW",
    "MO",   "PANW", "APH",  "MELI", "EOG",   "FDX",  "SLB",  "NOC",  "GE",   "HCA",
    "EW",   "MMM",  "APD",  "BSX",  "SNPS",  "CDNS", "CME",  "FTNT", "CTAS", "ORLY",
    "MRNA", "NXPI", "PAYX", "WM",   "PSA",   "F",    "GM",   "GD",   "LMT",  "BA",
    "UBER", "ABNB", "COIN", "PLTR", "SNOW",  "DDOG", "NET",  "CRWD", "ZS",   "HLT",
    "MAR",  "CCI",  "AMT",  "EQIX", "PH",    "EMR",  "ETN",  "ROK",  "FAST", "ODFL",
    "CSX",  "NSC",  "UNP",  "KMB",  "CL",    "CHD",  "GIS",  "SYY",  "MCK",  "CVS",
    "WBA",  "DGX",  "LH",   "IQV",  "CNC",   "MOH",  "HIG",  "AFL",  "CB",   "ALL",
    "MET",  "PRU",  "AIG",  "TRV",  "C",     "WFC",  "USB",  "PNC",  "TFC",  "FITB",
    "KEY",  "CFG",  "RF",   "HBAN", "MTB",   "NFLX", "AMD",  "PYPL", "RIVN", "LCID",
    "NIO",  "XPEV", "LI",   "DKNG", "RBLX",  "U",    "PTON", "ROKU", "SPOT", "SHOP",
    "DOCU", "ZM",   "TWLO", "OKTA", "SPLK",  "CTSH", "MCHP", "ON",   "GILD", "AEP",
    "XEL",  "WBD",  "SIRI", "BIDU", "NTES",  "TEAM", "ENPH", "VRTX", "GEHC", "DOW",
]
SP500 = list(dict.fromkeys(SP500))  # Remove duplicates, preserve order

# ─── Approximate market caps (billions USD) ───────────────────────────────────
# Used to size boxes in the heatmap. Updated periodically — not real-time.

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
    "BIDU":35,  "NTES":25,  "JD":22,    "PDD":200,  "SGEN":30,  "ILMN":25,
    "ALGN":20,  "ANSS":15,  "ZS":35,    "EBAY":25,  "LULU":55,  "MTCH":12,
    "WDAY":55,  "DXCM":30,  "FANG":35,  "CPRT":55,  "ROST":45,  "IDXX":30,
    "PCAR":40,  "VRSK":35,  "EXC":35,   "BIIB":38,  "DLTR":22,  "TTWO":20,
    "KDP":45,   "CEG":40,   "MAR":65,   "AZN":220,  "MNST":55,  "PAYX":55,
    "CHTR":50,  "EMR":45,   "ETN":65,   "ROK":25,   "PH":55,    "EQIX":75,
    "PYPL":75,  "MDLZ":90,  "WBD":25,   "CCEP":30,  "CSGP":25,  "XEL":30,
    "HOOD":8,   "LCID":7,   "PTON":5,   "U":12,     "TWLO":10,  "SPOT":35,
}

# ─── Index config ─────────────────────────────────────────────────────────────

INDICES = {
    "sp500": {"name": "S&P 500",    "tickers": SP500,      "proxy": "SPY"},
    "dji":   {"name": "Dow Jones",  "tickers": DOW_30,     "proxy": "DIA"},
    "ndq":   {"name": "NASDAQ 100", "tickers": NASDAQ_100, "proxy": "QQQ"},
}

# ─── Data fetching ────────────────────────────────────────────────────────────

def _get(url, params=None, timeout=10):
    if params is None:
        params = {}
    params["apiKey"] = API_KEY
    try:
        r = requests.get(f"{BASE_URL}{url}", params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  API error [{url}]: {e}")
        return {}


def fetch_snapshots(tickers):
    """Return dict of ticker -> {price, pct_change, volume} for all tickers."""
    results = {}
    for i in range(0, len(tickers), 200):
        batch = tickers[i : i + 200]
        data  = _get(
            "/v2/snapshot/locale/us/markets/stocks/tickers",
            {"tickers": ",".join(batch)},
        )
        for item in data.get("tickers", []):
            sym       = item.get("ticker", "")
            day       = item.get("day", {})
            prev_day  = item.get("prevDay", {})
            last      = item.get("lastTrade", {})

            price      = day.get("c") or last.get("p") or 0
            prev_close = prev_day.get("c") or 0
            pct        = ((price - prev_close) / prev_close * 100) if prev_close else 0

            results[sym] = {
                "price":      round(price, 2),
                "pct_change": round(pct,   2),
                "volume":     day.get("v", 0),
            }
        time.sleep(0.15)
    return results


def fetch_intraday(proxy):
    """Return DataFrame of {time, close} for today's minute bars of the proxy ETF."""
    today = date.today().isoformat()
    data  = _get(
        f"/v2/aggs/ticker/{proxy}/range/1/minute/{today}/{today}",
        {"adjusted": "true", "sort": "asc", "limit": 500},
    )
    bars = data.get("results", [])
    if not bars:
        return pd.DataFrame()
    df           = pd.DataFrame(bars)
    df["time"]   = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert("US/Eastern")
    df["close"]  = df["c"]
    return df[["time", "close"]]

# ─── Chart builders ───────────────────────────────────────────────────────────

def build_heatmap(index_key, snapshots):
    tickers = INDICES[index_key]["tickers"]

    rows = []
    for sym in tickers:
        snap = snapshots.get(sym)
        if not snap:
            continue
        mcap  = MARKET_CAPS.get(sym, 5)  # default 5B for unknown
        rows.append({
            "sym":        sym,
            "pct":        snap["pct_change"],
            "mcap":       max(mcap, 0.5),
            "price":      snap["price"],
            "label":      f"{sym}  {snap['pct_change']:+.2f}%",
        })

    fig = go.Figure()

    if not rows:
        fig.add_annotation(
            text="No data — check API key in .env file",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#FF3333", size=16),
            xref="paper", yref="paper",
        )
    else:
        df      = pd.DataFrame(rows)
        max_abs = max(df["pct"].abs().max(), 0.5)

        fig.add_trace(go.Treemap(
            labels=df["label"],
            parents=[""] * len(df),
            values=df["mcap"],
            customdata=list(zip(df["sym"], df["pct"], df["price"])),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Change: %{customdata[1]:+.2f}%<br>"
                "Price:  $%{customdata[2]:.2f}"
                "<extra></extra>"
            ),
            marker=dict(
                colors=df["pct"],
                colorscale=[
                    [0.00, "#8B0000"],
                    [0.35, "#CC2222"],
                    [0.48, "#550000"],
                    [0.50, "#111111"],
                    [0.52, "#005500"],
                    [0.65, "#22CC22"],
                    [1.00, "#00FF44"],
                ],
                cmid=0,
                cmin=-max_abs,
                cmax=max_abs,
                showscale=False,
                pad=dict(t=3, b=3, l=3, r=3),
            ),
            textfont=dict(color="#FFFFFF", size=11, family="monospace"),
            tiling=dict(squarifyratio=1),
        ))

    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(t=0, b=0, l=0, r=0),
        font=dict(color="#FFFFFF", family="monospace"),
    )
    return fig


def build_line_chart(proxy, snapshots):
    df = fetch_intraday(proxy)

    snap       = snapshots.get(proxy, {})
    price      = snap.get("price", 0)
    pct        = snap.get("pct_change", 0)
    pct_str    = f"{pct:+.2f}%" if pct else ""
    price_str  = f"${price:.2f}" if price else ""

    fig = go.Figure()

    if not df.empty:
        open_price = df["close"].iloc[0]

        # Fill area: green above open, red below open
        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df["close"],
            mode="lines",
            line=dict(color="#FF3333", width=1),
            fill="tozeroy",
            fillcolor="rgba(255,51,51,0.05)",
            hovertemplate="%{x|%H:%M}<br>$%{y:.2f}<extra></extra>",
        ))

        # Open price reference line
        fig.add_hline(
            y=open_price,
            line_dash="dot",
            line_color="#333333",
            line_width=1,
        )

        # Current price label at right edge
        if price:
            color = "#22CC22" if pct >= 0 else "#FF3333"
            fig.add_annotation(
                x=df["time"].iloc[-1],
                y=price,
                text=f" {price_str}  {pct_str}",
                showarrow=False,
                xanchor="left",
                font=dict(color=color, size=11, family="monospace"),
            )
    else:
        fig.add_annotation(
            text="Market closed or no intraday data yet",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#444444", size=13, family="monospace"),
            xref="paper", yref="paper",
        )

    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(t=5, b=5, l=70, r=80),
        font=dict(color="#555555", family="monospace"),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(color="#444444", size=10),
            tickformat="%H:%M",
            rangeslider=dict(visible=False),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            tickfont=dict(color="#444444", size=10),
            tickprefix="$",
            side="left",
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#111111", font_color="#CCCCCC", font_family="monospace"),
        dragmode="pan",
    )
    return fig

# ─── App layout ───────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    title="Market Heatmap",
    update_title=None,
)

app.layout = html.Div(
    style={
        "backgroundColor": "#000000",
        "height": "100vh",
        "fontFamily": "monospace",
        "padding": "10px 12px",
        "boxSizing": "border-box",
        "display": "flex",
        "flexDirection": "column",
    },
    children=[

        # ── Header ──────────────────────────────────────────────────────────
        html.Div(
            style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
            children=[
                html.Span(
                    "MARKET HEATMAP",
                    style={"color": "#FF3333", "fontSize": "13px", "letterSpacing": "4px"},
                ),
                html.Span(
                    id="last-updated",
                    style={"color": "#333333", "fontSize": "11px", "marginLeft": "20px"},
                ),
                html.Span(
                    id="market-status",
                    style={"color": "#555555", "fontSize": "11px", "marginLeft": "12px"},
                ),
            ],
        ),

        # ── Tabs ────────────────────────────────────────────────────────────
        dcc.Tabs(
            id="tab",
            value="sp500",
            style={"marginBottom": "8px"},
            colors={"border": "#000000", "primary": "#FF3333", "background": "#000000"},
            children=[
                dcc.Tab(
                    label="S&P 500",    value="sp500",
                    style={"color": "#555555", "backgroundColor": "#000000", "fontSize": "11px"},
                    selected_style={"color": "#FF3333", "backgroundColor": "#000000",
                                    "borderTop": "2px solid #FF3333", "fontSize": "11px"},
                ),
                dcc.Tab(
                    label="Dow Jones",  value="dji",
                    style={"color": "#555555", "backgroundColor": "#000000", "fontSize": "11px"},
                    selected_style={"color": "#FF3333", "backgroundColor": "#000000",
                                    "borderTop": "2px solid #FF3333", "fontSize": "11px"},
                ),
                dcc.Tab(
                    label="NASDAQ 100", value="ndq",
                    style={"color": "#555555", "backgroundColor": "#000000", "fontSize": "11px"},
                    selected_style={"color": "#FF3333", "backgroundColor": "#000000",
                                    "borderTop": "2px solid #FF3333", "fontSize": "11px"},
                ),
            ],
        ),

        # ── Heatmap ─────────────────────────────────────────────────────────
        dcc.Graph(
            id="heatmap",
            config={"displayModeBar": False, "scrollZoom": True},
            style={"flex": "1 1 60%", "minHeight": "0"},
        ),

        # ── Divider ─────────────────────────────────────────────────────────
        html.Div(style={"borderTop": "1px solid #111111", "margin": "6px 0"}),

        # ── Line chart label ────────────────────────────────────────────────
        html.Span(
            id="line-label",
            style={"color": "#FF3333", "fontSize": "10px", "letterSpacing": "2px",
                   "marginBottom": "2px"},
        ),

        # ── Intraday line chart ──────────────────────────────────────────────
        dcc.Graph(
            id="line-chart",
            config={"displayModeBar": False, "scrollZoom": True},
            style={"flex": "0 0 28%", "minHeight": "0"},
        ),

        # ── Auto-refresh timers ──────────────────────────────────────────────
        # Heatmap: every 60 seconds
        dcc.Interval(id="tick-heatmap", interval=60_000,  n_intervals=0),
        # Line chart: every 5 minutes
        dcc.Interval(id="tick-line",    interval=300_000, n_intervals=0),
    ],
)

# ─── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(
    Output("heatmap",       "figure"),
    Output("last-updated",  "children"),
    Output("market-status", "children"),
    Input("tab",            "value"),
    Input("tick-heatmap",   "n_intervals"),
)
def refresh_heatmap(index_key, _):
    tickers   = INDICES[index_key]["tickers"]
    snapshots = fetch_snapshots(tickers)

    fig = build_heatmap(index_key, snapshots)

    now    = datetime.now().strftime("%H:%M:%S")
    loaded = len(snapshots)
    total  = len(tickers)
    status = f"{loaded}/{total} stocks loaded"

    return fig, f"last updated {now}", status


@app.callback(
    Output("line-chart", "figure"),
    Output("line-label",  "children"),
    Input("tab",          "value"),
    Input("tick-line",    "n_intervals"),
)
def refresh_line(index_key, _):
    cfg   = INDICES[index_key]
    proxy = cfg["proxy"]

    # Fetch current snapshot for the proxy ETF to show price/% on label
    snap_data = fetch_snapshots([proxy])
    snap      = snap_data.get(proxy, {})
    price     = snap.get("price", 0)
    pct       = snap.get("pct_change", 0)

    pct_color = "#22CC22" if pct >= 0 else "#FF3333"
    label = (
        f"{cfg['name']}  ·  {proxy}  ·  "
        f"${price:.2f}  {pct:+.2f}%  ·  INTRADAY"
        if price else
        f"{cfg['name']}  ·  {proxy}  ·  INTRADAY"
    )

    fig = build_line_chart(proxy, snap_data)
    return fig, label

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bar = "━" * 50
    print(f"\n{bar}")
    print("  MARKET HEATMAP DASHBOARD")
    print(bar)

    if not API_KEY or API_KEY == "your_api_key_here":
        print("\n  ⚠  No API key found!")
        print("  1. Open the .env file in this folder")
        print("  2. Replace 'your_api_key_here' with your Polygon.io key")
        print("  3. Run this script again")
    else:
        print(f"\n  API key: {'*' * 20}{API_KEY[-4:]}")
        print(f"  Opening:  http://127.0.0.1:8050")
        print(f"  Stop:     Press Ctrl+C")

    print(f"{bar}\n")

    app.run(debug=False, host="127.0.0.1", port=8050)
