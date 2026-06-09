from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.analytics.price_trends import add_price_features


GREEN = "#1b8a3a"
GREEN_LIGHT = "#27ae4f"
GOLD = "#d4920a"
BLUE = "#1565c0"
RED = "#c0392b"
INK = "#111d14"
MUTED = "#5e7963"
GRID = "#e2ede4"
CARD_BG = "#ffffff"
BAND_GREEN = "rgba(27,138,58,0.10)"
BAND_GOLD = "rgba(212,146,10,0.12)"


def _base_layout() -> dict:
    """Shared layout config for all charts."""
    return dict(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(family="Inter, Segoe UI, sans-serif", color=INK, size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.03,
            xanchor="right", x=1,
            font=dict(size=11, color=MUTED),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=GRID,
            borderwidth=1,
            itemsizing="constant",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=CARD_BG,
            bordercolor=GRID,
            font=dict(family="Inter, Segoe UI, sans-serif", size=12, color=INK),
        ),
    )


def _polish_chart(fig: go.Figure, title: str, height: int, bottom_margin: int = 42) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=INK, family="Inter, Segoe UI, sans-serif"),
            x=0.01, xanchor="left",
            pad=dict(b=8),
        ),
        height=height,
        margin=dict(l=56, r=20, t=68, b=bottom_margin),
        **_base_layout(),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False,
        linecolor=GRID, linewidth=1,
        title_font=dict(color=MUTED, size=11),
        tickfont=dict(color=MUTED, size=10),
    )
    fig.update_yaxes(
        gridcolor=GRID, gridwidth=1,
        zeroline=False,
        linecolor=GRID, linewidth=1,
        title_font=dict(color=MUTED, size=11),
        tickfont=dict(color=MUTED, size=10),
    )
    return fig


def price_trend_chart(df: pd.DataFrame, title: str) -> go.Figure:
    featured = add_price_features(df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=featured["date"], y=featured["modal_price"],
        mode="lines", name="Modal price",
        line=dict(color=GREEN, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=featured["date"], y=featured["ma_7"],
        mode="lines", name="7-day avg",
        line=dict(color=GOLD, dash="dash", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=featured["date"], y=featured["ma_30"],
        mode="lines", name="30-day avg",
        line=dict(color=BLUE, dash="dot", width=1.5),
    ))
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="INR / quintal")
    return _polish_chart(fig, title, 400)


def price_band_chart(df: pd.DataFrame, title: str) -> go.Figure:
    data = df.sort_values("date")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data["date"], y=data["max_price"],
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=data["date"], y=data["min_price"],
        fill="tonexty", fillcolor=BAND_GREEN,
        line=dict(width=0), name="Min-max band",
    ))
    fig.add_trace(go.Scatter(
        x=data["date"], y=data["modal_price"],
        mode="lines", name="Modal price",
        line=dict(color=GREEN, width=2.5),
    ))
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="INR / quintal")
    return _polish_chart(fig, title, 380)


def forecast_chart(history: pd.DataFrame, forecast: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=history["date"], y=history["modal_price"],
        mode="lines", name="Actual",
        line=dict(color=GREEN, width=2.5),
    ))

    future = forecast[forecast["is_future"] == True] if "is_future" in forecast.columns else forecast.tail(30)
    if not future.empty:
        fig.add_trace(go.Scatter(
            x=future["ds"], y=future["yhat"],
            mode="lines", name="Forecast",
            line=dict(color=GOLD, width=2.5, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=future["ds"], y=future["yhat_upper"],
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=future["ds"], y=future["yhat_lower"],
            fill="tonexty", fillcolor=BAND_GOLD,
            line=dict(width=0), name="Forecast range",
        ))

    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="INR / quintal")
    return _polish_chart(fig, title, 400)


def mandi_comparison_chart(comparison: pd.DataFrame, title: str) -> go.Figure:
    data = comparison.head(10).sort_values("avg_price")
    fig = go.Figure(go.Bar(
        x=data["avg_price"],
        y=data["market"],
        orientation="h",
        marker=dict(
            color=GREEN,
            line=dict(color=GREEN_LIGHT, width=1),
        ),
        text=[f"₹{v:,.0f}" for v in data["avg_price"]],
        textposition="auto",
        textfont=dict(size=11, color=INK),
    ))
    fig.update_xaxes(title_text="Average modal price (INR)")
    fig.update_yaxes(title_text="", tickfont=dict(size=11))
    return _polish_chart(fig, title, 400, bottom_margin=36)


def movers_chart(movers: pd.DataFrame, title: str) -> go.Figure:
    data = movers.copy()
    if data.empty:
        return go.Figure()
    data["label"] = data["commodity"] + " · " + data["market"]
    colors = [GREEN if v >= 0 else RED for v in data["change_pct"]]
    fig = go.Figure(go.Bar(
        x=data["label"],
        y=data["change_pct"],
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:+.1f}%" for v in data["change_pct"]],
        textposition="outside",
        textfont=dict(size=10, color=INK),
    ))
    fig.update_xaxes(title_text="", tickangle=-40, tickfont=dict(size=10))
    fig.update_yaxes(title_text="Change %")
    return _polish_chart(fig, title, 380, bottom_margin=100)
