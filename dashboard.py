#!/usr/bin/env python3
"""
Market Heatmap Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━
Tracks S&P 500, Dow Jones, and NASDAQ 100 in real time.
Data from Finnhub (free). Runs in your browser at http://127.0.0.1:8050
"""

import os
import time
import threading
import requests
import pandas as pd
from datetime import datetime, date, timezone
from dotenv import load_dotenv

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

load_dotenv()

# ─── API ─────────────────────────────────────────────────────────────────────

API_KEY  = os.getenv("FINNHUB_API_KEY", "")
BASE_URL = "https://finnhub.io/api/v1"

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
SP500 = list(dict.fromkeys(SP500))

# ─── Approximate market caps (billions USD) ───────────────────────────────────

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
    "HOOD":8,   "LCID":7,   "PTON":5,   "U":12,     "TWLO":10,
}

# ─── Index config ─────────────────────────────────────────────────────────────

INDICES = {
    "sp500": {"name": "S&P 500",    "tickers": SP500,      "proxy": "SPY"},
    "dji":   {"name": "Dow Jones",  "tickers": DOW_30,     "proxy": "DIA"},
    "ndq":   {"name": "NASDAQ 100", "tickers": NASDAQ_100, "proxy": "QQQ"},
}

# All unique tickers across every index
ALL_TICKERS = list(dict.fromkeys(SP500 + DOW_30 + NASDAQ_100 + ["SPY", "DIA", "QQQ"]))

# ─── Live data cache ──────────────────────────────────────────────────────────
# Background thread fills this continuously. Dashboard reads from it.

_cache      = {}        # {ticker: {price, pct_change}}
_cache_lock = threading.Lock()
_intraday   = {}        # {proxy: DataFrame}
_intraday_lock = threading.Lock()

# ─── Finnhub API helpers ──────────────────────────────────────────────────────

def _get(endpoint, params=None):
    if params is None:
        params = {}
    params["token"] = API_KEY
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  API error [{endpoint}]: {e}")
        return {}


def fetch_quote(ticker):
    """Fetch real-time quote for one ticker. Returns dict or None."""
    data = _get("/quote", {"symbol": ticker})
    price      = data.get("c", 0)   # current price
    prev_close = data.get("pc", 0)  # previous close
    if not price or not prev_close:
        return None
    pct = (price - prev_close) / prev_close * 100
    return {"price": round(price, 2), "pct_change": round(pct, 2)}


def fetch_candles(ticker):
    """Fetch today's 1-minute bars for the given ticker."""
    now   = int(datetime.now(timezone.utc).timestamp())
    # Market open: 9:30 AM ET = 13:30 UTC
    today = datetime.now(timezone.utc).replace(hour=13, minute=30, second=0, microsecond=0)
    from_ts = int(today.timestamp())
    data  = _get("/stock/candle", {
        "symbol":     ticker,
        "resolution": "1",
        "from":       from_ts,
        "to":         now,
    })
    if data.get("s") != "ok" or not data.get("t"):
        return pd.DataFrame()
    df = pd.DataFrame({
        "time":  pd.to_datetime(data["t"], unit="s", utc=True).tz_convert("US/Eastern"),
        "close": data["c"],
    })
    return df

# ─── Background data fetcher ──────────────────────────────────────────────────

def _background_loop():
    """
    Runs forever in a background thread.
    Cycles through all tickers one by one, updating the cache.
    Finnhub free tier = 60 calls/minute → sleep 1.1s between calls.
    """
    proxies = ["SPY", "DIA", "QQQ"]
    while True:
        # Refresh intraday candles for each proxy ETF (once per cycle)
        for proxy in proxies:
            df = fetch_candles(proxy)
            with _intraday_lock:
                _intraday[proxy] = df
            time.sleep(1.1)

        # Refresh quotes for all stock tickers
        for ticker in ALL_TICKERS:
            quote = fetch_quote(ticker)
            if quote:
                with _cache_lock:
                    _cache[ticker] = quote
            time.sleep(1.1)


def start_background_fetcher():
    t = threading.Thread(target=_background_loop, daemon=True)
    t.start()
    print("  Background data fetcher started.")

# ─── Chart builders ───────────────────────────────────────────────────────────

def build_heatmap(index_key):
    tickers = INDICES[index_key]["tickers"]

    rows = []
    with _cache_lock:
        snapshot = dict(_cache)

    for sym in tickers:
        data = snapshot.get(sym)
        if not data:
            continue
        rows.append({
            "sym":   sym,
            "pct":   data["pct_change"],
            "mcap":  max(MARKET_CAPS.get(sym, 5), 0.5),
            "price": data["price"],
            "label": f"{sym}  {data['pct_change']:+.2f}%",
        })

    fig = go.Figure()

    if not rows:
        fig.add_annotation(
            text="Loading data... (takes ~30 seconds on first launch)",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#FF3333", size=15, family="monospace"),
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


def build_line_chart(proxy):
    with _intraday_lock:
        df = _intraday.get(proxy, pd.DataFrame()).copy()

    with _cache_lock:
        snap = _cache.get(proxy, {})

    price = snap.get("price", 0)
    pct   = snap.get("pct_change", 0)

    fig = go.Figure()

    if not df.empty:
        open_price = df["close"].iloc[0]

        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df["close"],
            mode="lines",
            line=dict(color="#FF3333", width=1),
            fill="tozeroy",
            fillcolor="rgba(255,51,51,0.05)",
            hovertemplate="%{x|%H:%M}<br>$%{y:.2f}<extra></extra>",
        ))

        fig.add_hline(
            y=open_price,
            line_dash="dot",
            line_color="#2a2a2a",
            line_width=1,
        )

        if price:
            color = "#22CC22" if pct >= 0 else "#FF3333"
            fig.add_annotation(
                x=df["time"].iloc[-1],
                y=price,
                text=f"  ${price:.2f}  {pct:+.2f}%",
                showarrow=False,
                xanchor="left",
                font=dict(color=color, size=11, family="monospace"),
            )
    else:
        fig.add_annotation(
            text="Market closed or data loading...",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#333333", size=13, family="monospace"),
            xref="paper", yref="paper",
        )

    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(t=5, b=5, l=70, r=90),
        font=dict(color="#555555", family="monospace"),
        xaxis=dict(
            showgrid=False, zeroline=False, showline=False,
            tickfont=dict(color="#444444", size=10),
            tickformat="%H:%M",
            rangeslider=dict(visible=False),
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showline=False,
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

app = dash.Dash(__name__, title="Market Heatmap", update_title=None)

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
        # Header
        html.Div(
            style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
            children=[
                html.Span("MARKET HEATMAP",
                          style={"color": "#FF3333", "fontSize": "13px", "letterSpacing": "4px"}),
                html.Span(id="last-updated",
                          style={"color": "#333333", "fontSize": "11px", "marginLeft": "20px"}),
                html.Span(id="stocks-loaded",
                          style={"color": "#444444", "fontSize": "11px", "marginLeft": "12px"}),
            ],
        ),

        # Tabs
        dcc.Tabs(
            id="tab", value="sp500",
            style={"marginBottom": "8px"},
            colors={"border": "#000000", "primary": "#FF3333", "background": "#000000"},
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
            ],
        ),

        # Heatmap
        dcc.Graph(id="heatmap",
                  config={"displayModeBar": False, "scrollZoom": True},
                  style={"flex": "1 1 60%", "minHeight": "0"}),

        # Divider
        html.Div(style={"borderTop": "1px solid #111111", "margin": "6px 0"}),

        # Line chart label
        html.Span(id="line-label",
                  style={"color":"#FF3333","fontSize":"10px","letterSpacing":"2px","marginBottom":"2px"}),

        # Intraday line chart
        dcc.Graph(id="line-chart",
                  config={"displayModeBar": False, "scrollZoom": True},
                  style={"flex": "0 0 28%", "minHeight": "0"}),

        # Refresh every 30 seconds (reads from cache — no extra API calls)
        dcc.Interval(id="tick", interval=30_000, n_intervals=0),
    ],
)

# ─── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(
    Output("heatmap",      "figure"),
    Output("last-updated", "children"),
    Output("stocks-loaded","children"),
    Input("tab",           "value"),
    Input("tick",          "n_intervals"),
)
def refresh_heatmap(index_key, _):
    fig     = build_heatmap(index_key)
    now     = datetime.now().strftime("%H:%M:%S")
    with _cache_lock:
        loaded = len(_cache)
    total   = len(ALL_TICKERS)
    status  = f"{loaded}/{total} tickers cached"
    return fig, f"last updated {now}", status


@app.callback(
    Output("line-chart", "figure"),
    Output("line-label",  "children"),
    Input("tab",          "value"),
    Input("tick",         "n_intervals"),
)
def refresh_line(index_key, _):
    cfg   = INDICES[index_key]
    proxy = cfg["proxy"]
    fig   = build_line_chart(proxy)
    with _cache_lock:
        snap = _cache.get(proxy, {})
    price = snap.get("price", 0)
    pct   = snap.get("pct_change", 0)
    label = (
        f"{cfg['name']}  ·  {proxy}  ·  ${price:.2f}  {pct:+.2f}%  ·  INTRADAY"
        if price else
        f"{cfg['name']}  ·  {proxy}  ·  INTRADAY"
    )
    return fig, label

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bar = "━" * 52
    print(f"\n{bar}")
    print("  MARKET HEATMAP DASHBOARD  —  Finnhub (free)")
    print(bar)

    if not API_KEY or API_KEY == "your_api_key_here":
        print("\n  WARNING: No API key found!")
        print("  1. Sign up free at https://finnhub.io")
        print("  2. Copy your API key from the dashboard")
        print("  3. Open the .env file and paste it in")
        print("  4. Run this script again\n")
    else:
        print(f"\n  API key: {'*' * 20}{API_KEY[-4:]}")
        print(f"  Tickers: {len(ALL_TICKERS)} total")
        print(f"  Opening: http://127.0.0.1:8050")
        print(f"  Stop:    Ctrl+C")
        print(f"\n  Data refreshes every ~{len(ALL_TICKERS) * 1.1 / 60:.0f} min per full cycle")
        print(f"  Dashboard updates every 30 seconds from local cache")

    print(f"{bar}\n")

    start_background_fetcher()
    app.run(debug=False, host="127.0.0.1", port=8050)
