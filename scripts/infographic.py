"""narrative(서술) JSON + market_data(수치) JSON을 카드형 인포그래픽 PNG로 렌더링한다."""
from __future__ import annotations

import base64
from pathlib import Path

from .config import ROOT_DIR

FONTS_DIR = ROOT_DIR / "assets" / "fonts"

UP_COLOR = "#d62728"  # 국내 관행: 상승 = 빨강
DOWN_COLOR = "#1f5fd6"  # 하락 = 파랑
FLAT_COLOR = "#666666"

CANVAS_WIDTH = 1080

CARD_COLORS = {
    "blue": "#3b6fe0",
    "purple": "#8b5cf6",
    "green": "#16a34a",
    "orange": "#f97316",
    "red": "#dc2626",
    "gray": "#6b7280",
}


def _font_face_css() -> str:
    faces = []
    for weight, filename in [(400, "NotoSansKR-Regular.ttf"), (700, "NotoSansKR-Bold.ttf")]:
        path = FONTS_DIR / filename
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        faces.append(
            f"""
            @font-face {{
              font-family: 'Noto Sans KR';
              font-weight: {weight};
              src: url(data:font/ttf;base64,{b64}) format('truetype');
            }}
            """
        )
    return "\n".join(faces)


def _sign_color(change_pct: float | None) -> str:
    if change_pct is None:
        return FLAT_COLOR
    if change_pct > 0:
        return UP_COLOR
    if change_pct < 0:
        return DOWN_COLOR
    return FLAT_COLOR


SPARKLINE_LINE_COLOR = "#c9ccd3"  # de-emphasis: 선 자체는 무채색, 끝점만 방향색(accent)


def _sparkline_svg(history: list[float], color: str, width: int = 88, height: int = 26) -> str:
    """최근 추이를 보여주는 미니 라인차트. 선은 무채색(de-emphasis), 마지막 점만
    등락 방향색(accent)으로 강조한다 - dataviz 스킬의 stat-tile trend 스펙을 따름."""
    if len(history) < 2:
        return ""
    lo, hi = min(history), max(history)
    span = (hi - lo) or 1
    n = len(history)
    pts = [
        (i / (n - 1) * width, height - 3 - ((v - lo) / span) * (height - 6))
        for i, v in enumerate(history)
    ]
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    last_x, last_y = pts[-1]
    return f"""
    <svg width="{width}" height="{height}" style="display:block;margin:4px auto 0;">
      <polyline points="{path}" fill="none" stroke="{SPARKLINE_LINE_COLOR}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3.5" fill="{color}" stroke="#fff" stroke-width="1.5" />
    </svg>
    """


def _badge(label: str, change_pct: float | None, value_str: str | None = None, history: list[float] | None = None) -> str:
    """value_str이 있으면 값+등락률을, 없으면 등락률만 크게 보여준다. history가 있으면 스파크라인 추가."""
    color = _sign_color(change_pct)
    value_html = f'<div style="font-weight:700;font-size:14px;color:#111;margin-bottom:2px;">{value_str}</div>' if value_str else ""
    change_str = ""
    if change_pct is not None:
        sign = "+" if change_pct > 0 else ""
        pct_size = "16px" if value_str else "20px"
        change_str = f'<div style="color:{color};font-weight:700;font-size:{pct_size};">{sign}{change_pct:.2f}%</div>'
    sparkline_html = _sparkline_svg(history, color) if history else ""
    return f"""
    <div style="background:#f7f8fa;border-radius:10px;padding:10px 6px;text-align:center;flex:1;min-width:100px;">
      <div style="color:#555;font-size:12px;margin-bottom:4px;">{label}</div>
      {value_html}
      {change_str}
      {sparkline_html}
    </div>
    """


def _badge_row(badges_html: list[str]) -> str:
    return f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">{"".join(badges_html)}</div>'


def _stat_row(label: str, value_str: str, change_pct: float | None = None) -> str:
    color = _sign_color(change_pct)
    change_html = ""
    if change_pct is not None:
        sign = "+" if change_pct > 0 else ""
        change_html = f'<span style="color:{color};font-weight:700;font-size:13px;margin-left:8px;">{sign}{change_pct:.2f}%</span>'
    return f"""
    <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #f0f0f0;">
      <span style="color:#444;font-size:14px;">{label}</span>
      <span style="font-size:14px;">
        <span style="font-weight:700;">{value_str}</span>{change_html}
      </span>
    </div>
    """


def _paragraph(text: str, muted: bool = False) -> str:
    color = "#666" if muted else "#222"
    return f'<p style="margin:6px 0;color:{color};font-size:14px;line-height:1.55;">{text}</p>'


def _analyst_box(label: str, text: str, bg: str) -> str:
    return f"""
    <div style="background:{bg};border-radius:8px;padding:10px 12px;margin-top:8px;">
      <div style="font-size:12px;font-weight:700;color:#555;margin-bottom:4px;">{label}</div>
      <div style="font-size:13px;color:#333;line-height:1.5;">{text}</div>
    </div>
    """


def _card(number: int, icon: str, title: str, color_key: str, body_html: str, span2: bool = False) -> str:
    color = CARD_COLORS.get(color_key, CARD_COLORS["blue"])
    col_span = "grid-column: span 2;" if span2 else ""
    return f"""
    <div style="background:#fff;border-radius:14px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,0.08);border-top:4px solid {color};{col_span}">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <span style="background:{color};color:#fff;width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0;">{number}</span>
        <span style="font-size:16px;font-weight:700;color:#111;">{icon} {title}</span>
      </div>
      {body_html}
    </div>
    """


def _checklist(items: list[str], icon: str = "✅") -> str:
    rows = "".join(
        f'<div style="display:flex;gap:8px;align-items:flex-start;padding:5px 0;font-size:14px;color:#333;">'
        f'<span>{icon}</span><span>{item}</span></div>'
        for item in items
    )
    return rows


def _events_list(events: list[dict]) -> str:
    rows = []
    for e in events:
        rows.append(
            f"""
            <div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #f0f0f0;">
              <div style="background:#eef2ff;color:#3b6fe0;font-weight:700;font-size:12px;border-radius:6px;padding:4px 8px;white-space:nowrap;height:fit-content;">{e.get('date', '')}</div>
              <div>
                <div style="font-weight:700;font-size:14px;color:#111;">{e.get('name', '')}</div>
                <div style="font-size:12px;color:#777;margin-top:2px;">{e.get('note', '')}</div>
              </div>
            </div>
            """
        )
    return "".join(rows)


def _risks_list(risks: list[dict]) -> str:
    rows = []
    for r in risks:
        rows.append(
            f"""
            <div style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
              <div style="font-weight:700;font-size:14px;color:#b91c1c;">⚠️ {r.get('title', '')}</div>
              <div style="font-size:13px;color:#555;margin-top:2px;line-height:1.5;">{r.get('detail', '')}</div>
            </div>
            """
        )
    return "".join(rows)


def build_html(market_data: dict, narrative: dict) -> str:
    date_str = narrative.get("date") or market_data.get("date", "")

    quote = narrative.get("quote")
    quote_html = ""
    if quote:
        quote_html = f"""
        <div style="background:#fff7e6;border-radius:12px;padding:14px 18px;max-width:320px;">
          <div style="font-size:13px;color:#333;line-height:1.5;font-style:italic;">“{quote['text']}”</div>
          <div style="font-size:12px;color:#999;margin-top:6px;text-align:right;">- {quote.get('source', '')}</div>
        </div>
        """

    header_html = f"""
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:14px;flex-wrap:wrap;">
      <div>
        <h1 style="font-size:26px;margin:0;color:#111;">{narrative.get('title', 'KR Market Report')}</h1>
        <div style="font-size:14px;color:#666;margin-top:6px;">{narrative.get('subtitle', '')}</div>
      </div>
      {quote_html}
    </div>
    """

    cards = []
    n = 1

    if narrative.get("summary"):
        cards.append(_card(n, "\U0001F3AF", "오늘 시장 한 줄 요약", "blue", _paragraph(narrative["summary"]), span2=True))
        n += 1

    us_indices = market_data.get("us_indices", [])
    us_market = narrative.get("us_market", {})
    if us_indices or us_market.get("analysis"):
        badges = [_badge(q["label"], q["change_pct"], history=q.get("history")) for q in us_indices]
        body = _badge_row(badges) + _paragraph(us_market.get("analysis", ""))
        cards.append(_card(n, "\U0001F1FA\U0001F1F8", "미국 증시가 국내장에 주는 영향", "purple", body))
        n += 1

    kr_indices = market_data.get("indices", [])
    domestic_mood = narrative.get("domestic_mood", {})
    if kr_indices or domestic_mood.get("analysis"):
        badges = [
            _badge(i["label"], i["change_rate"], value_str=f'{i["price"]:,.2f}', history=i.get("history"))
            for i in kr_indices
        ]
        body = _badge_row(badges) + _paragraph(domestic_mood.get("analysis", ""))
        cards.append(_card(n, "\U0001F1F0\U0001F1F7", "국내 증시 출발 분위기", "green", body))
        n += 1

    sector = narrative.get("sector_highlight")
    watchlist = market_data.get("watchlist", [])
    if sector or watchlist:
        bullets = ""
        if sector and sector.get("bullets"):
            bullets = _checklist(sector["bullets"], icon="✔️")
        badges = [_badge(q["label"], q["change_pct"], history=q.get("history")) for q in watchlist]
        body = bullets + (_badge_row(badges) if badges else "") + _paragraph((sector or {}).get("analysis", ""))
        title = (sector or {}).get("title", "관심 섹터 핵심 포인트")
        cards.append(_card(n, "\U0001F4BE", title, "orange", body, span2=True))
        n += 1

    fx_rows = "".join(_stat_row(f["label"], f'{f["deal_bas_r"]:,.2f} 원') for f in market_data.get("fx_rates", []))
    rate_rows = "".join(_stat_row(r["label"], f'{r["value"]:.2f}%') for r in market_data.get("rates", []))
    oil_rows = "".join(_stat_row(o["label"], f'${o["value"]:,.2f}') for o in market_data.get("oil_prices", []))
    if fx_rows or rate_rows or oil_rows:
        body = fx_rows + rate_rows + oil_rows
        cards.append(_card(n, "\U0001F4B1", "환율·금리·유가", "gray", body))
        n += 1

    events = narrative.get("events", [])
    if events:
        cards.append(_card(n, "\U0001F4C5", "이번 주 눈여겨볼 이벤트", "blue", _events_list(events)))
        n += 1

    risks = narrative.get("risks", [])
    if risks:
        cards.append(_card(n, "⚠️", "체크해야 할 리스크", "red", _risks_list(risks)))
        n += 1

    grid_html = f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">{"".join(cards)}</div>'

    checkpoints = narrative.get("checkpoints", [])
    checkpoints_html = ""
    if checkpoints:
        items = "".join(
            f'<div style="flex:1;min-width:140px;background:#fff;border-radius:10px;padding:10px 14px;'
            f'box-shadow:0 1px 3px rgba(0,0,0,0.06);font-size:13px;color:#333;">✅ {c}</div>'
            for c in checkpoints
        )
        checkpoints_html = f"""
        <div style="background:#1f2a44;border-radius:14px;padding:16px 20px;margin-top:16px;">
          <div style="color:#fff;font-weight:700;font-size:14px;margin-bottom:10px;">\U0001F4CB 오늘 장중 체크포인트</div>
          <div style="display:flex;gap:10px;flex-wrap:wrap;">{items}</div>
        </div>
        """

    disclaimer = narrative.get(
        "disclaimer",
        "※ 이 리포트는 투자 권유가 아니라 공개된 시장 데이터를 기반으로 한 자동 해석입니다. 투자 판단의 책임은 투자자 본인에게 있습니다.",
    )

    return f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          {_font_face_css()}
          * {{ font-family: 'Noto Sans KR', sans-serif; box-sizing: border-box; }}
          body {{ margin: 0; background: #f2f3f6; }}
        </style>
      </head>
      <body>
        <div style="width:{CANVAS_WIDTH}px;padding:22px;background:#f2f3f6;">
          {header_html}
          {grid_html}
          {checkpoints_html}
          <div style="text-align:center;font-size:11px;color:#999;margin-top:18px;">{disclaimer}</div>
          <div style="text-align:center;font-size:11px;color:#bbb;margin-top:6px;">{date_str}</div>
        </div>
      </body>
    </html>
    """


def render_png(html: str, out_path: Path) -> Path:
    from playwright.sync_api import sync_playwright

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": CANVAS_WIDTH, "height": 800})
        page.set_content(html, wait_until="load")
        page.screenshot(path=str(out_path), full_page=True)
        browser.close()
    return out_path
