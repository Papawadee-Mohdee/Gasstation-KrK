"""
app.py — Fuel Station Analytics Dashboard
=========================================
Web Application (Streamlit) อ่านข้อมูลจาก warehouse.duckdb เท่านั้น
โดยดึงจาก Dimension / Fact / Mart ที่ออกแบบไว้ (ไม่แตะตาราง stg_* / ref_* โดยตรง)

รัน:  python build_warehouse.py   แล้ว   streamlit run app.py
"""

from __future__ import annotations

import os
from datetime import date

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# ค่าคงที่ / ธีมสี (น้ำเงินเข้ม + ขาว)
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warehouse.duckdb")

NAVY_950 = "#050D1F"
NAVY_900 = "#0A1730"
NAVY_800 = "#0E2244"
NAVY_700 = "#16325F"
LINE = "rgba(255,255,255,0.09)"
INK = "#EAF1FB"
MUTED = "#9CB3D1"
BLUE = "#3B82F6"
SKY = "#60A5FA"
CYAN = "#22D3EE"
GOLD = "#F5B942"
GREEN = "#34D399"
RED = "#F87171"
VIOLET = "#A78BFA"

PALETTE = [BLUE, CYAN, SKY, VIOLET, GOLD, GREEN, RED, "#94A3B8"]
BLUE_SCALE = [[0.0, "#0E2244"], [0.35, "#1D4ED8"], [0.7, "#3B82F6"], [1.0, "#7DD3FC"]]

WEEKDAY_TH = {
    "Monday": "จันทร์", "Tuesday": "อังคาร", "Wednesday": "พุธ", "Thursday": "พฤหัสบดี",
    "Friday": "ศุกร์", "Saturday": "เสาร์", "Sunday": "อาทิตย์",
}
WEEKDAY_ORDER = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

st.set_page_config(
    page_title="Fuel Station Analytics",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<style>
  .stApp {{
      background:
        radial-gradient(1100px 600px at 12% -12%, #123262 0%, rgba(18,50,98,0) 58%),
        radial-gradient(900px 520px at 92% 0%, #0F2E5C 0%, rgba(15,46,92,0) 55%),
        {NAVY_950};
      color: {INK};
  }}
  [data-testid="stSidebar"] {{
      background: linear-gradient(180deg, {NAVY_900} 0%, {NAVY_950} 100%);
      border-right: 1px solid {LINE};
  }}
  [data-testid="stHeader"] {{ background: transparent; }}
  .block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1500px; }}

  h1, h2, h3, h4 {{ color: #FFFFFF; letter-spacing: .2px; }}

  .hero {{
      background: linear-gradient(120deg, {NAVY_800} 0%, {NAVY_700} 55%, #1E4B92 100%);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 20px; padding: 22px 26px; margin-bottom: 18px;
      box-shadow: 0 18px 40px rgba(0,0,0,.38);
  }}
  .hero h1 {{ margin: 0; font-size: 1.75rem; font-weight: 800; }}
  .hero p  {{ margin: 6px 0 0; color: {MUTED}; font-size: .93rem; }}
  .pill {{
      display:inline-block; margin-top:12px; margin-right:8px; padding:4px 12px;
      border-radius:999px; font-size:.75rem; font-weight:600;
      background: rgba(59,130,246,.18); color:{SKY};
      border:1px solid rgba(96,165,250,.35);
  }}

  .kpi {{
      background: linear-gradient(160deg, rgba(22,50,95,.92) 0%, rgba(10,23,48,.92) 100%);
      border: 1px solid {LINE}; border-left: 3px solid {BLUE};
      border-radius: 16px; padding: 16px 18px; height: 100%;
      box-shadow: 0 10px 26px rgba(0,0,0,.30);
  }}
  .kpi .label {{ color:{MUTED}; font-size:.78rem; font-weight:600; letter-spacing:.4px;
                 text-transform:uppercase; }}
  .kpi .value {{ color:#FFFFFF; font-size:1.65rem; font-weight:800; margin-top:6px;
                 line-height:1.15; }}
  .kpi .unit  {{ font-size:.85rem; color:{MUTED}; font-weight:600; margin-left:4px; }}
  .kpi .delta {{ font-size:.80rem; font-weight:700; margin-top:6px; }}
  .up   {{ color:{GREEN}; }}
  .down {{ color:{RED}; }}
  .flat {{ color:{MUTED}; }}

  .panel {{
      background: rgba(14,34,68,.62); border:1px solid {LINE};
      border-radius:16px; padding:16px 18px 6px; margin-bottom: 6px;
  }}
  .panel h4 {{ margin:0 0 2px; font-size:1rem; font-weight:700; }}
  .panel .sub {{ color:{MUTED}; font-size:.8rem; margin:0 0 10px; }}

  .stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid {LINE}; }}
  .stTabs [data-baseweb="tab"] {{
      background: rgba(255,255,255,.03); border-radius: 10px 10px 0 0;
      padding: 10px 16px; color: {MUTED}; font-weight: 600;
  }}
  .stTabs [aria-selected="true"] {{
      background: linear-gradient(180deg, rgba(59,130,246,.28), rgba(59,130,246,.06));
      color: #FFFFFF !important; border-bottom: 2px solid {BLUE};
  }}
  [data-testid="stDataFrame"] {{ border:1px solid {LINE}; border-radius:12px; }}
  .stAlert {{ border-radius: 12px; }}
  footer, #MainMenu {{ visibility: hidden; }}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data access layer — อ่านจาก dim_* / fact_* / mart_* เท่านั้น
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_con() -> duckdb.DuckDBPyConnection:
    if not os.path.exists(DB_PATH):
        st.error("ไม่พบ warehouse.duckdb — กรุณารัน `python build_warehouse.py` ก่อน")
        st.stop()
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(show_spinner=False)
def q(sql: str, params: tuple | None = None) -> pd.DataFrame:
    return get_con().execute(sql, params or []).df()


def panel(title: str, sub: str = "") -> None:
    st.markdown(
        f'<div class="panel"><h4>{title}</h4><p class="sub">{sub}</p></div>',
        unsafe_allow_html=True,
    )


def style(fig: go.Figure, height: int = 340, legend_top: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, 'IBM Plex Sans Thai', sans-serif", color=INK, size=12.5),
        hoverlabel=dict(bgcolor=NAVY_800, bordercolor=BLUE, font_color=INK),
        colorway=PALETTE,
    )
    if legend_top:
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                        bgcolor="rgba(0,0,0,0)", title_text="")
        )
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE, tickfont_color=MUTED,
                     title_font_color=MUTED)
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE, tickfont_color=MUTED,
                     title_font_color=MUTED)
    return fig


def kpi(col, label: str, value: str, unit: str = "", delta: float | None = None,
        delta_label: str = "vs ช่วงก่อนหน้า") -> None:
    if delta is None:
        d_html = f'<div class="delta flat">{delta_label}: —</div>'
    else:
        cls = "up" if delta > 0.0005 else ("down" if delta < -0.0005 else "flat")
        arrow = "▲" if delta > 0.0005 else ("▼" if delta < -0.0005 else "▬")
        d_html = f'<div class="delta {cls}">{arrow} {abs(delta) * 100:,.1f}% <span style="color:{MUTED};font-weight:500">{delta_label}</span></div>'
    col.markdown(
        f'<div class="kpi"><div class="label">{label}</div>'
        f'<div class="value">{value}<span class="unit">{unit}</span></div>{d_html}</div>',
        unsafe_allow_html=True,
    )


def pct_change(cur: float, prev: float) -> float | None:
    if prev in (None, 0) or pd.isna(prev):
        return None
    return (cur - prev) / prev


# ---------------------------------------------------------------------------
# Sidebar filters  (ค่าตัวเลือกทั้งหมดมาจาก Dimension)
# ---------------------------------------------------------------------------
dim_station = q("select gasstation_id, gasstation_name from dim_gasstation "
                "where not is_unknown_member order by gasstation_id")
dim_prod = q("select product_id, product_name, product_type, is_fuel from dim_product "
             "where not is_unknown_member order by is_fuel desc, product_id")
dim_dates = q("select min(date_day) as d0, max(date_day) as d1 from dim_date where date_key <> -1")

D0, D1 = dim_dates.iloc[0, 0], dim_dates.iloc[0, 1]

with st.sidebar:
    st.markdown(
        f'<div style="font-size:1.15rem;font-weight:800;color:#fff;margin-bottom:2px">⛽ Fuel Analytics</div>'
        f'<div style="color:{MUTED};font-size:.78rem;margin-bottom:14px">Star Schema · DuckDB · dbt marts</div>',
        unsafe_allow_html=True,
    )
    st.markdown("##### 🗓️ ช่วงวันที่")
    date_range = st.date_input(
        "เลือกช่วงวันที่", value=(D0, D1), min_value=D0, max_value=D1,
        label_visibility="collapsed",
    )
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_d, end_d = date_range
    else:
        start_d, end_d = D0, D1

    st.markdown("##### 🏪 สถานีบริการ")
    st_names = st.multiselect(
        "สถานี", dim_station["gasstation_name"].tolist(),
        default=dim_station["gasstation_name"].tolist(), label_visibility="collapsed",
    )
    st.markdown("##### 🛢️ สินค้า")
    fuel_only = st.toggle("เฉพาะน้ำมันเชื้อเพลิง", value=True)
    prod_pool = dim_prod[dim_prod["is_fuel"]] if fuel_only else dim_prod
    prod_names = st.multiselect(
        "สินค้า", prod_pool["product_name"].tolist(),
        default=prod_pool["product_name"].tolist(), label_visibility="collapsed",
    )
    st.divider()
    st.caption(
        "ข้อมูลทั้งหมดดึงจากตาราง Dimension / Fact / Mart ที่ออกแบบไว้ "
        "และตัดแถวที่ติดธง `is_data_quality_flagged` ออกจากการวิเคราะห์"
    )

if not st_names:
    st.warning("กรุณาเลือกอย่างน้อย 1 สถานี")
    st.stop()
if not prod_names:
    st.warning("กรุณาเลือกอย่างน้อย 1 สินค้า")
    st.stop()

sid_list = dim_station.loc[dim_station["gasstation_name"].isin(st_names), "gasstation_id"].tolist()
pid_list = dim_prod.loc[dim_prod["product_name"].isin(prod_names), "product_id"].tolist()
k0 = int(pd.Timestamp(start_d).strftime("%Y%m%d"))
k1 = int(pd.Timestamp(end_d).strftime("%Y%m%d"))
span = (pd.Timestamp(end_d) - pd.Timestamp(start_d)).days + 1
p0 = int((pd.Timestamp(start_d) - pd.Timedelta(days=span)).strftime("%Y%m%d"))
p1 = int((pd.Timestamp(start_d) - pd.Timedelta(days=1)).strftime("%Y%m%d"))

S = tuple(sid_list)
P = tuple(pid_list)
def dk(a: int, b: int) -> tuple:
    """พารามิเตอร์มาตรฐาน: สถานี, สินค้า, ช่วง date_key"""
    return (list(S), list(P), a, b)


BASE_WHERE = """
    f.gasstation_id = any(?) and f.product_id = any(?)
    and f.date_key between ? and ? and not f.is_data_quality_flagged
"""

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<div class="hero">
  <h1>⛽ แดชบอร์ดวิเคราะห์สถานีบริการน้ำมัน</h1>
  <p>ยอดขาย · พฤติกรรมลูกค้า · ประสิทธิภาพพนักงาน · การบริหารคลังน้ำมัน &nbsp;|&nbsp;
     ข้อมูล {start_d:%d %b %Y} – {end_d:%d %b %Y}</p>
  <span class="pill">{len(sid_list)} สถานี</span>
  <span class="pill">{len(pid_list)} สินค้า</span>
  <span class="pill">{span} วัน</span>
  <span class="pill">Source: dim_ / fact_ / mart_</span>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI แถวบน  (fact_sales + fact_invoice)
# ---------------------------------------------------------------------------
KPI_SQL = f"""
select
    coalesce(sum(f.total_price), 0)                       as sales_amount,
    coalesce(sum(case when p.is_fuel then f.quantity_sold end), 0) as fuel_liters,
    count(distinct f.invoice_id)                          as bill_count,
    count(distinct f.customer_id)                         as customer_count
from fact_sales f
join dim_product p on f.product_id = p.product_id
where {BASE_WHERE}
"""
cur = q(KPI_SQL, dk(k0, k1)).iloc[0]
prev = q(KPI_SQL, dk(p0, p1)).iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
kpi(c1, "ยอดขายรวม", f"{cur.sales_amount:,.0f}", " ฿",
    pct_change(cur.sales_amount, prev.sales_amount))
kpi(c2, "ปริมาณน้ำมันที่ขาย", f"{cur.fuel_liters:,.0f}", " ลิตร",
    pct_change(cur.fuel_liters, prev.fuel_liters))
kpi(c3, "จำนวนบิล", f"{cur.bill_count:,.0f}", " บิล",
    pct_change(cur.bill_count, prev.bill_count))
avg_bill = cur.sales_amount / cur.bill_count if cur.bill_count else 0
avg_bill_p = prev.sales_amount / prev.bill_count if prev.bill_count else 0
kpi(c4, "ยอดขายเฉลี่ย/บิล", f"{avg_bill:,.0f}", " ฿", pct_change(avg_bill, avg_bill_p))
kpi(c5, "ลูกค้าที่ใช้บริการ", f"{cur.customer_count:,.0f}", " ราย",
    pct_change(cur.customer_count, prev.customer_count))

st.write("")

TAB1, TAB2, TAB3, TAB4, TAB5, TAB6 = st.tabs(
    ["📊 ภาพรวม", "⛽ การขาย", "👥 ลูกค้า", "🧑‍💼 พนักงาน & การชำระเงิน",
     "🛢️ คลังน้ำมัน", "✅ คุณภาพข้อมูล"]
)

# ===========================================================================
# TAB 1 — ภาพรวม
# ===========================================================================
with TAB1:
    left, right = st.columns([1.85, 1])

    with left:
        panel("แนวโน้มยอดขายรายวัน", "fact_sales × dim_date · เส้นประคือค่าเฉลี่ยเคลื่อนที่ 7 วัน")
        daily = q(f"""
            select d.date_day, sum(f.total_price) as sales_amount,
                   count(distinct f.invoice_id) as bill_count
            from fact_sales f
            join dim_date d on f.date_key = d.date_key
            where {BASE_WHERE}
            group by 1 order by 1
        """, dk(k0, k1))
        daily["ma7"] = daily["sales_amount"].rolling(7, min_periods=1).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["date_day"], y=daily["sales_amount"], name="ยอดขายรายวัน",
            mode="lines", line=dict(color=SKY, width=2.2),
            fill="tozeroy", fillcolor="rgba(96,165,250,.16)",
            hovertemplate="%{x|%d %b}<br>%{y:,.0f} ฿<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=daily["date_day"], y=daily["ma7"], name="ค่าเฉลี่ย 7 วัน",
            mode="lines", line=dict(color=GOLD, width=2, dash="dash"),
            hovertemplate="%{y:,.0f} ฿<extra></extra>",
        ))
        fig.update_yaxes(title_text="บาท")
        st.plotly_chart(style(fig, 330), width="stretch")

    with right:
        panel("ยอดขายตามสถานี", "จัดอันดับจาก fact_sales × dim_gasstation")
        by_st = q(f"""
            select g.gasstation_name, sum(f.total_price) as sales_amount
            from fact_sales f
            join dim_gasstation g on f.gasstation_id = g.gasstation_id
            where {BASE_WHERE}
            group by 1 order by 2
        """, dk(k0, k1))
        fig = px.bar(by_st, x="sales_amount", y="gasstation_name", orientation="h",
                     text=by_st["sales_amount"].map(lambda v: f"{v/1e6:,.2f} ล.฿"))
        fig.update_traces(marker=dict(color=by_st["sales_amount"], colorscale=BLUE_SCALE,
                                      line=dict(width=0)),
                          textposition="inside", insidetextanchor="end",
                          textfont=dict(color="#fff", size=11),
                          hovertemplate="%{y}<br>%{x:,.0f} ฿<extra></extra>")
        fig.update_layout(showlegend=False)
        fig.update_xaxes(title_text="บาท")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 330, legend_top=False), width="stretch")

    a, b = st.columns([1, 1.6])

    with a:
        panel("สัดส่วนยอดขายตามชนิดสินค้า", "fact_sales × dim_product")
        mix = q(f"""
            select p.product_name, sum(f.total_price) as sales_amount
            from fact_sales f
            join dim_product p on f.product_id = p.product_id
            where {BASE_WHERE}
            group by 1 order by 2 desc
        """, dk(k0, k1))
        fig = go.Figure(go.Pie(
            labels=mix["product_name"], values=mix["sales_amount"], hole=.62,
            marker=dict(colors=PALETTE, line=dict(color=NAVY_950, width=2)),
            textinfo="percent", textfont=dict(color="#fff", size=11),
            hovertemplate="%{label}<br>%{value:,.0f} ฿ (%{percent})<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{mix['sales_amount'].sum()/1e6:,.1f}</b><br>"
                                f"<span style='font-size:11px;color:{MUTED}'>ล้านบาท</span>",
                           showarrow=False, font=dict(size=20, color="#fff"))
        st.plotly_chart(style(fig, 360), width="stretch")

    with b:
        panel("ความหนาแน่นของการขาย: ชั่วโมง × วันในสัปดาห์",
              "fact_sales × dim_date × dim_hour — สีเข้ม = จำนวนบิลมาก")
        hm = q(f"""
            select d.weekday_name, d.iso_weekday, f.hour_of_day,
                   count(distinct f.invoice_id) as bill_count
            from fact_sales f
            join dim_date d on f.date_key = d.date_key
            where {BASE_WHERE}
            group by 1, 2, 3
        """, dk(k0, k1))
        hm["wd"] = hm["weekday_name"].map(WEEKDAY_TH)
        piv = (hm.pivot_table(index="wd", columns="hour_of_day", values="bill_count",
                              aggfunc="sum", fill_value=0)
                 .reindex(WEEKDAY_ORDER).fillna(0))
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=[f"{h:02d}" for h in piv.columns], y=piv.index,
            colorscale=BLUE_SCALE, xgap=2, ygap=2,
            colorbar=dict(title="บิล", outlinewidth=0, tickfont=dict(color=MUTED)),
            hovertemplate="%{y} %{x}:00<br>%{z:,.0f} บิล<extra></extra>",
        ))
        fig.update_xaxes(title_text="ชั่วโมง")
        fig.update_yaxes(autorange="reversed", title_text="")
        st.plotly_chart(style(fig, 360, legend_top=False), width="stretch")

    panel("ยอดขายรายวันแยกตามสถานี", "int_sales_daily × dim_date × dim_gasstation (aggregate layer)")
    st_daily = q(f"""
        select d.date_day, g.gasstation_name, sum(s.sales_amount) as sales_amount
        from int_sales_daily s
        join dim_date d on s.date_key = d.date_key
        join dim_gasstation g on s.gasstation_id = g.gasstation_id
        where s.gasstation_id = any(?) and s.product_id = any(?) and s.date_key between ? and ?
        group by 1, 2 order by 1
    """, dk(k0, k1))
    fig = px.area(st_daily, x="date_day", y="sales_amount", color="gasstation_name")
    fig.update_traces(line=dict(width=1.2), hovertemplate="%{y:,.0f} ฿<extra>%{fullData.name}</extra>")
    fig.update_yaxes(title_text="บาท")
    fig.update_xaxes(title_text="")
    st.plotly_chart(style(fig, 320), width="stretch")

# ===========================================================================
# TAB 2 — การขาย (Q1, Q2, Q9)
# ===========================================================================
with TAB2:
    st.markdown("#### Q1 · สถานีใดสร้างยอดขายสูงสุดในแต่ละวัน และมาจากน้ำมันชนิดใด")
    c1, c2 = st.columns([1, 1.35])

    with c1:
        panel("จำนวนวันที่ครองอันดับ 1", "mart_01_station_product_daily (station_day_rank = 1)")
        top_days = q("""
            select g.gasstation_name, count(distinct m.date_day) as days_rank1
            from mart_01_station_product_daily m
            join dim_gasstation g on m.gasstation_id = g.gasstation_id
            where m.station_day_rank = 1
              and m.gasstation_id = any(?)
              and m.date_day between ? and ?
            group by 1 order by 2 desc
        """, (list(S), start_d, end_d))
        fig = px.bar(top_days, x="gasstation_name", y="days_rank1", text="days_rank1")
        fig.update_traces(marker_color=BLUE, textposition="outside",
                          textfont=dict(color=INK),
                          hovertemplate="%{x}<br>%{y} วัน<extra></extra>")
        fig.update_xaxes(title_text="", tickangle=-18)
        fig.update_yaxes(title_text="จำนวนวัน")
        st.plotly_chart(style(fig, 340, legend_top=False), width="stretch")

    with c2:
        panel("โครงสร้างยอดขาย: สถานี → ชนิดน้ำมัน",
              "mart_01 × dim_product — ขนาดกล่อง = ยอดขายรวมในช่วงที่เลือก")
        tree = q("""
            select g.gasstation_name, p.product_name, sum(m.sales_amount) as sales_amount
            from mart_01_station_product_daily m
            join dim_gasstation g on m.gasstation_id = g.gasstation_id
            join dim_product p on m.product_id = p.product_id
            where m.gasstation_id = any(?) and m.product_id = any(?)
              and m.date_day between ? and ?
            group by 1, 2
        """, (list(S), list(P), start_d, end_d))
        fig = px.treemap(tree, path=["gasstation_name", "product_name"], values="sales_amount",
                         color="sales_amount", color_continuous_scale=BLUE_SCALE)
        fig.update_traces(marker=dict(line=dict(color=NAVY_950, width=2)),
                          textfont=dict(color="#fff", size=12),
                          hovertemplate="<b>%{label}</b><br>%{value:,.0f} ฿<extra></extra>")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style(fig, 340, legend_top=False), width="stretch")

    st.divider()
    st.markdown("#### Q2 · ช่วงเวลาขายหนาแน่นของแต่ละสถานี")
    sel_station = st.selectbox("เลือกสถานีเพื่อดูรูปแบบรายชั่วโมง", st_names, key="q2_station")
    sel_sid = int(dim_station.loc[dim_station["gasstation_name"] == sel_station, "gasstation_id"].iloc[0])

    c1, c2 = st.columns([1.55, 1])
    with c1:
        panel(f"ปริมาณขายเฉลี่ยต่อชั่วโมง — {sel_station}",
              "mart_02_hourly_demand (สรุปทั้งช่วงข้อมูล) · หน่วย: ลิตรต่อชั่วโมงที่มีการขาย")
        h2 = q("""
            select hour_of_day, weekday_name, iso_weekday, avg_qty_per_hour_observed
            from mart_02_hourly_demand where gasstation_id = ?
        """, (sel_sid,))
        h2["wd"] = h2["weekday_name"].map(WEEKDAY_TH)
        piv = (h2.pivot_table(index="wd", columns="hour_of_day",
                              values="avg_qty_per_hour_observed", aggfunc="mean")
                 .reindex(WEEKDAY_ORDER))
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=[f"{h:02d}" for h in piv.columns], y=piv.index,
            colorscale=BLUE_SCALE, xgap=2, ygap=2,
            colorbar=dict(title="ลิตร/ชม.", outlinewidth=0, tickfont=dict(color=MUTED)),
            hovertemplate="%{y} %{x}:00<br>%{z:,.0f} ลิตร<extra></extra>",
        ))
        fig.update_xaxes(title_text="ชั่วโมง")
        fig.update_yaxes(autorange="reversed", title_text="")
        st.plotly_chart(style(fig, 330, legend_top=False), width="stretch")

    with c2:
        panel("จำนวนบิลตามช่วงเวลาของวัน", "fact_sales × dim_hour (day_part)")
        dp = q(f"""
            select h.day_part, count(distinct f.invoice_id) as bill_count
            from fact_sales f
            join dim_hour h on f.hour_of_day = h.hour_of_day
            where {BASE_WHERE}
            group by 1
        """, dk(k0, k1))
        order = ["เช้า", "เที่ยง", "บ่าย", "เย็น", "กลางคืน"]
        dp["day_part"] = pd.Categorical(dp["day_part"], order, ordered=True)
        dp = dp.sort_values("day_part")
        fig = go.Figure(go.Barpolar(
            r=dp["bill_count"], theta=dp["day_part"].astype(str),
            marker=dict(color=dp["bill_count"], colorscale=BLUE_SCALE,
                        line=dict(color=NAVY_950, width=1.5)),
            hovertemplate="%{theta}<br>%{r:,.0f} บิล<extra></extra>",
        ))
        fig.update_layout(polar=dict(
            bgcolor="rgba(255,255,255,.03)",
            radialaxis=dict(gridcolor=LINE, tickfont=dict(color=MUTED, size=9), angle=90),
            angularaxis=dict(gridcolor=LINE, tickfont=dict(color=INK, size=11)),
        ))
        st.plotly_chart(style(fig, 330, legend_top=False), width="stretch")

    st.divider()
    st.markdown("#### Q9 · ยอดขายเปลี่ยนแปลงจากวันเดียวกันในสัปดาห์ก่อนเท่าใด")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        panel("ผลต่างยอดขายรายวัน เทียบ 7 วันก่อน",
              "mart_09_wow_sales_change — แท่งเขียว = โตขึ้น / แดง = ลดลง")
        wow = q("""
            select date_day, sum(sales_diff) as sales_diff
            from mart_09_wow_sales_change
            where gasstation_id = any(?) and product_id = any(?)
              and date_day between ? and ?
            group by 1 order by 1
        """, (list(S), list(P), start_d, end_d))
        fig = go.Figure(go.Bar(
            x=wow["date_day"], y=wow["sales_diff"],
            marker_color=[GREEN if v >= 0 else RED for v in wow["sales_diff"]],
            hovertemplate="%{x|%d %b}<br>%{y:+,.0f} ฿<extra></extra>",
        ))
        fig.add_hline(y=0, line_color=MUTED, line_width=1)
        fig.update_yaxes(title_text="ผลต่าง (บาท)")
        fig.update_xaxes(title_text="")
        st.plotly_chart(style(fig, 330, legend_top=False), width="stretch")

    with c2:
        panel("ชนิดน้ำมันที่ขับเคลื่อนการเปลี่ยนแปลง", "mart_09 — ผลรวมผลต่างรายสินค้า")
        wow_p = q("""
            select p.product_name, sum(m.sales_diff) as sales_diff
            from mart_09_wow_sales_change m
            join dim_product p on m.product_id = p.product_id
            where m.gasstation_id = any(?) and m.product_id = any(?)
              and m.date_day between ? and ?
            group by 1 order by 2
        """, (list(S), list(P), start_d, end_d))
        fig = go.Figure(go.Bar(
            x=wow_p["sales_diff"], y=wow_p["product_name"], orientation="h",
            marker_color=[GREEN if v >= 0 else RED for v in wow_p["sales_diff"]],
            hovertemplate="%{y}<br>%{x:+,.0f} ฿<extra></extra>",
        ))
        fig.add_vline(x=0, line_color=MUTED, line_width=1)
        fig.update_xaxes(title_text="ผลต่างสะสม (บาท)")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 330, legend_top=False), width="stretch")

# ===========================================================================
# TAB 3 — ลูกค้า (Q3, Q5, Q6, Q7, Q10)
# ===========================================================================
with TAB3:
    st.markdown("#### Q3 · ลูกค้าแต่ละประเภทรถนิยมน้ำมันชนิดใด")
    c1, c2 = st.columns([1.4, 1])
    with c1:
        panel("สัดส่วนปริมาณขายตามประเภทรถ × ชนิดน้ำมัน",
              "mart_03_vehicle_product_mix — แกน Y เป็นสัดส่วน 100% ในแต่ละกลุ่มรถ")
        vp = q("""
            select vehicle_category, product_name, sum(quantity_sold) as quantity_sold
            from mart_03_vehicle_product_mix
            where gasstation_id = any(?) and product_id = any(?)
            group by 1, 2
        """, (list(S), list(P)))
        tot = vp.groupby("vehicle_category")["quantity_sold"].transform("sum")
        vp["share"] = vp["quantity_sold"] / tot
        fig = px.bar(vp, x="vehicle_category", y="share", color="product_name",
                     custom_data=["quantity_sold"])
        fig.update_traces(hovertemplate="%{x}<br>%{y:.1%} (%{customdata[0]:,.0f} ลิตร)"
                                        "<extra>%{fullData.name}</extra>")
        fig.update_yaxes(tickformat=".0%", title_text="สัดส่วนปริมาณ")
        fig.update_xaxes(title_text="")
        st.plotly_chart(style(fig, 350), width="stretch")

    with c2:
        panel("ปริมาณเฉลี่ยต่อบิลตามประเภทรถ", "mart_03 — ลิตรต่อบิล")
        avgq = q("""
            select vehicle_category,
                   sum(quantity_sold) / nullif(sum(bill_count), 0) as avg_qty
            from mart_03_vehicle_product_mix
            where gasstation_id = any(?) and product_id = any(?)
            group by 1 order by 2 desc
        """, (list(S), list(P)))
        fig = px.bar(avgq, x="avg_qty", y="vehicle_category", orientation="h",
                     text=avgq["avg_qty"].map(lambda v: f"{v:,.1f} ล."))
        fig.update_traces(marker=dict(color=avgq["avg_qty"], colorscale=BLUE_SCALE),
                          textposition="outside", textfont=dict(color=INK, size=11),
                          hovertemplate="%{y}<br>%{x:,.1f} ลิตร/บิล<extra></extra>")
        fig.update_xaxes(title_text="ลิตร/บิล")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 350, legend_top=False), width="stretch")

    st.divider()
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("#### Q5 · ลูกค้า 10 อันดับแรกของสถานี")
        sel_station5 = st.selectbox("เลือกสถานี", st_names, key="q5_station")
        sel_sid5 = int(dim_station.loc[dim_station["gasstation_name"] == sel_station5,
                                       "gasstation_id"].iloc[0])
        top10 = q("""
            select customer_name, vehicle_category, product_name, customer_sales,
                   bill_count, rank_in_station
            from mart_05_top10_customers
            where gasstation_id = ? order by rank_in_station
        """, (sel_sid5,)).sort_values("customer_sales")
        fig = px.bar(top10, x="customer_sales", y="customer_name", orientation="h",
                     color="vehicle_category",
                     custom_data=["product_name", "bill_count", "rank_in_station"])
        fig.update_traces(hovertemplate="อันดับ %{customdata[2]} · %{y}<br>%{x:,.0f} ฿ · "
                                        "%{customdata[1]} บิล<br>สินค้าหลัก: %{customdata[0]}"
                                        "<extra>%{fullData.name}</extra>")
        fig.update_xaxes(title_text="ยอดซื้อน้ำมันสะสม (บาท)")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 400), width="stretch")

    with c2:
        st.markdown("#### Q6 · อัตราการกลับมาซื้อซ้ำ")
        panel("Repeat rate ตามประเภทรถ",
              "mart_06_repeat_purchase — ลูกค้าที่ซื้อ ≥ 2 วัน ÷ ลูกค้าทั้งหมดในกลุ่ม")
        rp = q("""
            select vehicle_category,
                   sum(repeat_customers) as repeat_customers,
                   sum(total_customers)  as total_customers,
                   sum(repeat_customers) / nullif(sum(total_customers), 0) as repeat_rate
            from mart_06_repeat_purchase
            where gasstation_id = any(?)
            group by 1 order by 4 desc
        """, (list(S),))
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=rp["vehicle_category"], y=rp["repeat_rate"],
            marker=dict(color=rp["repeat_rate"], colorscale=BLUE_SCALE),
            text=[f"{v:.0%}" for v in rp["repeat_rate"]], textposition="outside",
            textfont=dict(color=INK),
            customdata=rp[["repeat_customers", "total_customers"]].values,
            hovertemplate="%{x}<br>%{y:.1%}<br>%{customdata[0]:,.0f} / %{customdata[1]:,.0f} ราย"
                          "<extra></extra>",
        ))
        fig.update_yaxes(tickformat=".0%", title_text="อัตราซื้อซ้ำ", range=[0, 1.05])
        fig.update_xaxes(title_text="", tickangle=-15)
        st.plotly_chart(style(fig, 400, legend_top=False), width="stretch")

    st.divider()
    c1, c2 = st.columns([1, 1.25])
    with c1:
        st.markdown("#### Q7 · ลูกค้าที่ใช้บริการหลายสถานี")
        panel("จำนวนลูกค้าแยกตามจำนวนสถานีที่ใช้บริการ", "mart_07_multi_station_customers")
        ms = q("""
            select station_count, count(distinct customer_id) as customers
            from mart_07_multi_station_customers
            group by 1 order by 1
        """)
        fig = px.bar(ms, x="station_count", y="customers", text="customers")
        fig.update_traces(marker=dict(color=ms["customers"], colorscale=BLUE_SCALE),
                          textposition="outside", textfont=dict(color=INK),
                          hovertemplate="ใช้บริการ %{x} สถานี<br>%{y:,.0f} ราย<extra></extra>")
        fig.update_xaxes(title_text="จำนวนสถานีที่ใช้บริการ", dtick=1)
        fig.update_yaxes(title_text="จำนวนลูกค้า")
        st.plotly_chart(style(fig, 360, legend_top=False), width="stretch")

    with c2:
        st.markdown("#### Q10 · คู่สินค้าที่พบร่วมกันในบิลเดียว")
        panel("Top 12 คู่สินค้า", "mart_10_product_pairs — นับคู่ละครั้งต่อบิล")
        pairs = q("""
            select product_name_a || '  +  ' || product_name_b as pair,
                   sum(bill_count_with_pair) as bills,
                   avg(avg_bill_value) as avg_bill_value
            from mart_10_product_pairs
            where gasstation_id = any(?)
            group by 1 order by 2 desc limit 12
        """, (list(S),)).sort_values("bills")
        fig = px.bar(pairs, x="bills", y="pair", orientation="h",
                     custom_data=["avg_bill_value"])
        fig.update_traces(marker=dict(color=pairs["bills"], colorscale=BLUE_SCALE),
                          hovertemplate="%{y}<br>%{x:,.0f} บิล<br>"
                                        "ยอดบิลเฉลี่ย %{customdata[0]:,.0f} ฿<extra></extra>")
        fig.update_xaxes(title_text="จำนวนบิลที่พบคู่นี้")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 360, legend_top=False), width="stretch")

# ===========================================================================
# TAB 4 — พนักงาน & การชำระเงิน (Q4, Q8)
# ===========================================================================
with TAB4:
    st.markdown("#### Q4 · วิธีชำระเงินสัมพันธ์กับมูลค่าการซื้ออย่างไร")
    c1, c2, c3 = st.columns([1, 1.25, 1.1])

    with c1:
        panel("สัดส่วนจำนวนบิลตามวิธีชำระเงิน", "mart_04_payment_behavior")
        pm = q("""
            select payment_method_label, sum(bill_count) as bill_count,
                   sum(total_amount) as total_amount
            from mart_04_payment_behavior where gasstation_id = any(?)
            group by 1 order by 2 desc
        """, (list(S),))
        fig = go.Figure(go.Pie(
            labels=pm["payment_method_label"], values=pm["bill_count"], hole=.6,
            marker=dict(colors=PALETTE, line=dict(color=NAVY_950, width=2)),
            textinfo="percent", textfont=dict(color="#fff", size=11),
            hovertemplate="%{label}<br>%{value:,.0f} บิล (%{percent})<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{pm['bill_count'].sum():,.0f}</b><br>"
                                f"<span style='font-size:11px;color:{MUTED}'>บิล</span>",
                           showarrow=False, font=dict(size=18, color="#fff"))
        st.plotly_chart(style(fig, 340), width="stretch")

    with c2:
        panel("ยอดขายเฉลี่ยต่อบิล: วิธีชำระ × ช่วงเวลา", "mart_04 — ค่าเฉลี่ยถ่วงน้ำหนักด้วยจำนวนบิล")
        pv = q("""
            select payment_method_label, day_part,
                   sum(total_amount) / nullif(sum(bill_count), 0) as avg_per_bill
            from mart_04_payment_behavior where gasstation_id = any(?)
            group by 1, 2
        """, (list(S),))
        order = ["เช้า", "เที่ยง", "บ่าย", "เย็น", "กลางคืน"]
        piv = pv.pivot(index="payment_method_label", columns="day_part",
                       values="avg_per_bill").reindex(columns=order)
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=piv.columns, y=piv.index, colorscale=BLUE_SCALE, xgap=3, ygap=3,
            text=[[f"{v:,.0f}" if pd.notna(v) else "" for v in row] for row in piv.values],
            texttemplate="%{text}", textfont=dict(color="#fff", size=11),
            colorbar=dict(title="฿/บิล", outlinewidth=0, tickfont=dict(color=MUTED)),
            hovertemplate="%{y} · %{x}<br>%{z:,.0f} ฿/บิล<extra></extra>",
        ))
        fig.update_yaxes(title_text="")
        fig.update_xaxes(title_text="")
        st.plotly_chart(style(fig, 340, legend_top=False), width="stretch")

    with c3:
        panel("วิธีชำระเงินตามประเภทรถ", "mart_04 — สัดส่วนบิลภายในแต่ละประเภทรถ")
        pvc = q("""
            select vehicle_category, payment_method_label, sum(bill_count) as bill_count
            from mart_04_payment_behavior where gasstation_id = any(?)
            group by 1, 2
        """, (list(S),))
        tot = pvc.groupby("vehicle_category")["bill_count"].transform("sum")
        pvc["share"] = pvc["bill_count"] / tot
        fig = px.bar(pvc, y="vehicle_category", x="share", color="payment_method_label",
                     orientation="h")
        fig.update_traces(hovertemplate="%{y}<br>%{x:.1%}<extra>%{fullData.name}</extra>")
        fig.update_xaxes(tickformat=".0%", title_text="")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 340), width="stretch")

    st.divider()
    st.markdown("#### Q8 · ปริมาณรายการขายของพนักงานและตำแหน่ง")
    c1, c2 = st.columns([1, 1.4])

    with c1:
        panel("จำนวนบิลเฉลี่ยต่อวันตามตำแหน่ง", "mart_08_employee_productivity × dim_employee")
        pos = q("""
            select position,
                   sum(bill_count) as bills,
                   count(distinct date_day) as days,
                   count(distinct employee_id) as employees
            from mart_08_employee_productivity
            where gasstation_id = any(?) and date_day between ? and ?
            group by 1
        """, (list(S), start_d, end_d))
        pos["bills_per_emp_day"] = pos["bills"] / (pos["days"] * pos["employees"])
        pos = pos.sort_values("bills_per_emp_day")
        fig = px.bar(pos, x="bills_per_emp_day", y="position", orientation="h",
                     text=pos["bills_per_emp_day"].map(lambda v: f"{v:,.1f}"))
        fig.update_traces(marker=dict(color=pos["bills_per_emp_day"], colorscale=BLUE_SCALE),
                          textposition="outside", textfont=dict(color=INK),
                          hovertemplate="%{y}<br>%{x:,.1f} บิล/คน/วัน<extra></extra>")
        fig.update_xaxes(title_text="บิล / คน / วัน")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 360, legend_top=False), width="stretch")

    with c2:
        panel("พนักงานรายบุคคล: จำนวนบิล vs ยอดขาย",
              "mart_08 — ขนาดจุด = ยอดขายเฉลี่ยต่อบิล")
        emp = q("""
            select e.employee_name, m.position, g.gasstation_name,
                   sum(m.bill_count) as bills, sum(m.sales_amount) as sales
            from mart_08_employee_productivity m
            join dim_employee e on m.employee_id = e.employee_id
            join dim_gasstation g on m.gasstation_id = g.gasstation_id
            where m.gasstation_id = any(?) and m.date_day between ? and ?
            group by 1, 2, 3
        """, (list(S), start_d, end_d))
        emp["avg_bill"] = emp["sales"] / emp["bills"]
        fig = px.scatter(emp, x="bills", y="sales", color="position", size="avg_bill",
                         size_max=22, hover_name="employee_name",
                         custom_data=["gasstation_name", "avg_bill"])
        fig.update_traces(marker=dict(line=dict(width=0.6, color=NAVY_950), opacity=.85),
                          hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<br>"
                                        "%{x:,.0f} บิล · %{y:,.0f} ฿<br>"
                                        "เฉลี่ย %{customdata[1]:,.0f} ฿/บิล<extra></extra>")
        fig.update_xaxes(title_text="จำนวนบิล")
        fig.update_yaxes(title_text="ยอดขาย (บาท)")
        st.plotly_chart(style(fig, 360), width="stretch")

# ===========================================================================
# TAB 5 — คลังน้ำมัน (Q11–Q15)
# ===========================================================================
with TAB5:
    st.markdown("#### Q15 · ควรเติมน้ำมันถังใดก่อน")
    reorder = q("""
        select gasstation_name, product_name, tank_id,
               latest_remaining_quantity, capacity_liters, pct_remaining,
               avg_daily_sales_qty_7d, estimated_days_to_stockout
        from mart_15_reorder_priority
        where gasstation_id = any(?) and product_id = any(?)
        order by estimated_days_to_stockout nulls last
    """, (list(S), list(P)))

    urgent = reorder[reorder["estimated_days_to_stockout"] < 3]
    if len(urgent):
        st.error(f"⚠️ มี {len(urgent)} ถังที่คาดว่าน้ำมันจะหมดภายใน 3 วัน — "
                 f"{', '.join(f'{r.gasstation_name} / {r.product_name}' for r in urgent.head(4).itertuples())}")

    c1, c2 = st.columns([1.45, 1])
    with c1:
        panel("จำนวนวันคงเหลือก่อนน้ำมันหมด (ประมาณการ)",
              "mart_15_reorder_priority — ยอดคงเหลือล่าสุด ÷ อัตราขายเฉลี่ย 7 วัน")
        show = reorder.dropna(subset=["estimated_days_to_stockout"]).head(18).copy()
        show["label"] = show["gasstation_name"].str.replace("สถานี", "", regex=False) \
                        + " · " + show["product_name"]
        show = show.sort_values("estimated_days_to_stockout", ascending=False)
        colors = [RED if v < 3 else (GOLD if v < 7 else GREEN)
                  for v in show["estimated_days_to_stockout"]]
        fig = go.Figure(go.Bar(
            x=show["estimated_days_to_stockout"], y=show["label"], orientation="h",
            marker_color=colors,
            text=[f"{v:,.1f} วัน" for v in show["estimated_days_to_stockout"]],
            textposition="outside", textfont=dict(color=INK, size=10),
            customdata=show[["latest_remaining_quantity", "avg_daily_sales_qty_7d"]].values,
            hovertemplate="%{y}<br>เหลือ %{customdata[0]:,.0f} ลิตร<br>"
                          "ขายเฉลี่ย %{customdata[1]:,.0f} ลิตร/วัน<br>"
                          "<b>%{x:,.1f} วัน</b><extra></extra>",
        ))
        fig.add_vline(x=3, line_color=RED, line_dash="dot",
                      annotation_text="เกณฑ์เร่งด่วน 3 วัน",
                      annotation_font_color=RED, annotation_font_size=10)
        fig.update_xaxes(title_text="วัน")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 470, legend_top=False), width="stretch")

    with c2:
        panel("ระดับน้ำมันคงเหลือเทียบความจุถัง",
              "mart_15 × dim_tank — เส้นประ = เกณฑ์ต่ำ 20%")
        lv = reorder.dropna(subset=["pct_remaining"]).sort_values("pct_remaining").head(18).copy()
        lv["label"] = lv["gasstation_name"].str.replace("สถานี", "", regex=False) \
                      + " · " + lv["product_name"]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[1] * len(lv), y=lv["label"], orientation="h",
            marker_color="rgba(255,255,255,.07)", hoverinfo="skip", showlegend=False,
        ))
        fig.add_trace(go.Bar(
            x=lv["pct_remaining"], y=lv["label"], orientation="h",
            marker_color=[RED if v < .2 else (GOLD if v < .35 else BLUE)
                          for v in lv["pct_remaining"]],
            customdata=lv[["latest_remaining_quantity", "capacity_liters"]].values,
            hovertemplate="%{y}<br>%{x:.1%} ของความจุ<br>"
                          "%{customdata[0]:,.0f} / %{customdata[1]:,.0f} ลิตร<extra></extra>",
            showlegend=False,
        ))
        fig.add_vline(x=.2, line_color=RED, line_dash="dot")
        fig.update_layout(barmode="overlay")
        fig.update_xaxes(tickformat=".0%", title_text="% ของความจุถัง", range=[0, 1])
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 470, legend_top=False), width="stretch")

    st.divider()
    st.markdown("#### Q12 · ถังใดมีระดับต่ำกว่าเกณฑ์บ่อยที่สุด")
    c1, c2 = st.columns([1.1, 1.3])
    with c1:
        panel("จำนวนครั้งที่ระดับต่ำกว่า 20% (สถานี × ชนิดน้ำมัน)",
              "mart_12_low_fuel_frequency — นับรายถัง-วัน-ชั่วโมง")
        low = q("""
            select gasstation_name, product_name,
                   count(*) filter (where is_below_threshold) as low_events
            from mart_12_low_fuel_frequency
            where gasstation_id = any(?) and product_id = any(?)
              and date_day between ? and ?
            group by 1, 2
        """, (list(S), list(P), start_d, end_d))
        piv = low.pivot(index="gasstation_name", columns="product_name",
                        values="low_events").fillna(0)
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=piv.columns, y=piv.index, colorscale=BLUE_SCALE, xgap=3, ygap=3,
            text=[[f"{int(v)}" for v in row] for row in piv.values],
            texttemplate="%{text}", textfont=dict(color="#fff", size=11),
            colorbar=dict(title="ครั้ง", outlinewidth=0, tickfont=dict(color=MUTED)),
            hovertemplate="%{y}<br>%{x}<br>%{z:,.0f} ครั้ง<extra></extra>",
        ))
        fig.update_xaxes(title_text="", tickangle=-20)
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 360, legend_top=False), width="stretch")

    with c2:
        panel("ช่วงเวลาที่เกิดเหตุระดับต่ำ", "mart_12 — กระจายตามชั่วโมงของวัน")
        low_h = q("""
            select hour_of_day, count(*) filter (where is_below_threshold) as low_events
            from mart_12_low_fuel_frequency
            where gasstation_id = any(?) and product_id = any(?)
              and date_day between ? and ?
            group by 1 order by 1
        """, (list(S), list(P), start_d, end_d))
        fig = px.bar(low_h, x="hour_of_day", y="low_events")
        fig.update_traces(marker=dict(color=low_h["low_events"], colorscale=BLUE_SCALE),
                          hovertemplate="%{x}:00<br>%{y:,.0f} ครั้ง<extra></extra>")
        fig.update_xaxes(title_text="ชั่วโมง", dtick=2)
        fig.update_yaxes(title_text="จำนวนครั้ง")
        st.plotly_chart(style(fig, 360, legend_top=False), width="stretch")

    st.divider()
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("#### Q11 · การรับเข้า–จ่ายออก และส่วนต่างสะสม")
        panel("ปริมาณรับเข้า vs จ่ายออกรายวัน",
              "mart_11_inventory_imbalance — เส้น = ส่วนต่างสะสม (รับเข้า − จ่ายออก)")
        imb = q("""
            select date_day, sum(quantity_in) as qty_in, sum(quantity_out) as qty_out
            from mart_11_inventory_imbalance
            where gasstation_id = any(?) and product_id = any(?)
              and date_day between ? and ?
            group by 1 order by 1
        """, (list(S), list(P), start_d, end_d))
        imb["cum"] = (imb["qty_in"] - imb["qty_out"]).cumsum()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=imb["date_day"], y=imb["qty_in"], name="รับเข้า",
                             marker_color=BLUE,
                             hovertemplate="%{y:,.0f} ลิตร<extra>รับเข้า</extra>"))
        fig.add_trace(go.Bar(x=imb["date_day"], y=-imb["qty_out"], name="จ่ายออก",
                             marker_color=CYAN,
                             hovertemplate="%{y:,.0f} ลิตร<extra>จ่ายออก</extra>"))
        fig.add_trace(go.Scatter(x=imb["date_day"], y=imb["cum"], name="ส่วนต่างสะสม",
                                 mode="lines", yaxis="y2",
                                 line=dict(color=GOLD, width=2.2),
                                 hovertemplate="%{y:,.0f} ลิตร<extra>สะสม</extra>"))
        fig.update_layout(barmode="relative",
                          yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                      tickfont=dict(color=GOLD), title=None))
        fig.update_yaxes(title_text="ลิตร")
        fig.update_xaxes(title_text="")
        st.plotly_chart(style(fig, 370), width="stretch")

    with c2:
        st.markdown("#### Q13 · ขนาดการเติมเทียบความจุถัง")
        panel("ปริมาณเติมเฉลี่ยต่อครั้ง (% ของความจุ)", "mart_13_refill_pattern × dim_tank")
        rf = q("""
            select product_name,
                   avg(pct_refill_of_capacity) as pct_cap,
                   avg(avg_qty_per_refill) as avg_qty,
                   sum(refill_count) as refills
            from mart_13_refill_pattern
            where gasstation_id = any(?) and product_id = any(?)
              and date_day between ? and ? and refill_count > 0
            group by 1 order by 2
        """, (list(S), list(P), start_d, end_d))
        fig = px.bar(rf, x="pct_cap", y="product_name", orientation="h",
                     custom_data=["avg_qty", "refills"],
                     text=rf["pct_cap"].map(lambda v: f"{v:.0%}"))
        fig.update_traces(marker=dict(color=rf["pct_cap"], colorscale=BLUE_SCALE),
                          textposition="outside", textfont=dict(color=INK, size=10),
                          hovertemplate="%{y}<br>%{x:.1%} ของความจุ<br>"
                                        "เฉลี่ย %{customdata[0]:,.0f} ลิตร/ครั้ง<br>"
                                        "เติมทั้งหมด %{customdata[1]:,.0f} ครั้ง<extra></extra>")
        fig.update_xaxes(tickformat=".0%", title_text="% ของความจุถัง")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 370, legend_top=False), width="stretch")

    st.divider()
    st.markdown("#### Q14 · ยอดขายตามใบเสร็จ vs ปริมาณจ่ายออกจากถัง")
    st.caption("ส่วนต่างเป็น “จุดให้ตรวจสอบ” ไม่ใช่ข้อสรุปว่ามีน้ำมันสูญหาย")
    c1, c2 = st.columns([1.45, 1])
    with c1:
        panel("ส่วนต่างรายวัน (ขาย − จ่ายออก)", "mart_14_sales_vs_dispense")
        dif = q("""
            select date_day, sum(quantity_sold) as sold, sum(quantity_out) as out,
                   sum(diff) as diff
            from mart_14_sales_vs_dispense
            where gasstation_id = any(?) and product_id = any(?)
              and date_day between ? and ?
            group by 1 order by 1
        """, (list(S), list(P), start_d, end_d))
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dif["date_day"], y=dif["diff"], name="ส่วนต่าง",
            marker_color=[GREEN if abs(v) < dif["sold"].mean() * .01 else GOLD
                          for v in dif["diff"]],
            customdata=dif[["sold", "out"]].values,
            hovertemplate="%{x|%d %b}<br>ขาย %{customdata[0]:,.0f} ล. · "
                          "จ่ายออก %{customdata[1]:,.0f} ล.<br><b>ส่วนต่าง %{y:+,.0f} ล.</b>"
                          "<extra></extra>",
        ))
        fig.add_hline(y=0, line_color=MUTED, line_width=1)
        fig.update_yaxes(title_text="ลิตร")
        fig.update_xaxes(title_text="")
        st.plotly_chart(style(fig, 350, legend_top=False), width="stretch")

    with c2:
        panel("ส่วนต่างเฉลี่ย (%) ตามสถานี × ชนิดน้ำมัน", "mart_14 — ค่าบวก = ขายมากกว่าที่จ่ายออก")
        dp2 = q("""
            select gasstation_name, product_name, avg(pct_diff) as pct_diff
            from mart_14_sales_vs_dispense
            where gasstation_id = any(?) and product_id = any(?)
              and date_day between ? and ? and pct_diff is not null
            group by 1, 2
        """, (list(S), list(P), start_d, end_d))
        piv = dp2.pivot(index="gasstation_name", columns="product_name", values="pct_diff")
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=piv.columns, y=piv.index,
            colorscale=[[0, RED], [.5, NAVY_800], [1, GREEN]], zmid=0, xgap=3, ygap=3,
            text=[[f"{v:+.1f}%" if pd.notna(v) else "" for v in row] for row in piv.values],
            texttemplate="%{text}", textfont=dict(color="#fff", size=10),
            colorbar=dict(title="%", outlinewidth=0, tickfont=dict(color=MUTED)),
            hovertemplate="%{y}<br>%{x}<br>%{z:+.2f}%<extra></extra>",
        ))
        fig.update_xaxes(title_text="", tickangle=-20)
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 350, legend_top=False), width="stretch")

# ===========================================================================
# TAB 6 — คุณภาพข้อมูล
# ===========================================================================
with TAB6:
    st.markdown("#### ธรรมาภิบาลข้อมูล (Data Quality & Governance)")
    st.caption("แถวที่มีปัญหาไม่ถูกลบทิ้ง แต่ถูกติดธง `is_data_quality_flagged` "
               "และมิติมี Unknown member (-1 / 'unknown') รองรับการเชื่อมที่หาคู่ไม่ได้")

    dq = q("""
        select 'fact_sales' as table_name, count(*) as total_rows,
               count(*) filter (where is_data_quality_flagged) as flagged_rows
        from fact_sales
        union all
        select 'fact_invoice', count(*), count(*) filter (where is_data_quality_flagged)
        from fact_invoice
        union all
        select 'fact_inventory_transaction', count(*),
               count(*) filter (where is_data_quality_flagged)
        from fact_inventory_transaction
    """)
    dq["flag_pct"] = dq["flagged_rows"] / dq["total_rows"]

    cols = st.columns(3)
    for col, r in zip(cols, dq.itertuples()):
        kpi(col, r.table_name, f"{r.flagged_rows:,}", f" / {r.total_rows:,} แถว")
        col.caption(f"สัดส่วนแถวที่ติดธง {r.flag_pct:.2%}")

    st.write("")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        panel("สัดส่วนแถวที่ติดธงคุณภาพข้อมูลในแต่ละ Fact table", "fact_* · is_data_quality_flagged")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dq["table_name"], y=dq["flag_pct"],
                             marker_color=[RED if v > .02 else GOLD for v in dq["flag_pct"]],
                             text=[f"{v:.2%}" for v in dq["flag_pct"]],
                             textposition="outside", textfont=dict(color=INK),
                             hovertemplate="%{x}<br>%{y:.2%}<extra></extra>"))
        fig.update_yaxes(tickformat=".1%", title_text="สัดส่วนที่ติดธง")
        fig.update_xaxes(title_text="")
        st.plotly_chart(style(fig, 320, legend_top=False), width="stretch")

    with c2:
        panel("ความครบถ้วนของวัน (data coverage)", "dim_date.is_complete_day")
        cov = q("""
            select is_complete_day, count(*) as days
            from dim_date where date_key <> -1 group by 1
        """)
        cov["label"] = cov["is_complete_day"].map({True: "ยืนยันครบถ้วน", False: "ยังไม่ยืนยัน"})
        fig = go.Figure(go.Pie(
            labels=cov["label"], values=cov["days"], hole=.6,
            marker=dict(colors=[BLUE, GOLD], line=dict(color=NAVY_950, width=2)),
            textinfo="percent", textfont=dict(color="#fff"),
            hovertemplate="%{label}<br>%{value} วัน<extra></extra>",
        ))
        st.plotly_chart(style(fig, 320), width="stretch")

    st.markdown("##### โครงสร้างตารางในคลังข้อมูล")
    tables = q("""
        select table_name,
               case
                   when table_name like 'dim_%' then '1 · Dimension'
                   when table_name like 'bridge_%' then '2 · Bridge'
                   when table_name like 'fact_%' then '3 · Fact'
                   when table_name like 'int_%'  then '4 · Intermediate'
                   when table_name like 'mart_%' then '5 · Mart'
                   else '0 · Source/Staging'
               end as layer,
               estimated_size as approx_rows,
               column_count
        from duckdb_tables()
        order by layer, table_name
    """)
    st.dataframe(
        tables[tables["layer"] != "0 · Source/Staging"],
        width="stretch", hide_index=True,
        column_config={
            "table_name": "ตาราง",
            "layer": "เลเยอร์",
            "approx_rows": st.column_config.NumberColumn("จำนวนแถว (โดยประมาณ)", format="%d"),
            "column_count": st.column_config.NumberColumn("จำนวนคอลัมน์"),
        },
    )

st.markdown(
    f'<div style="text-align:center;color:{MUTED};font-size:.78rem;padding-top:18px;'
    f'border-top:1px solid {LINE};margin-top:22px">'
    f'Fuel Station Analytics · Star Schema (dbt + DuckDB) · ข้อมูลจาก Dimension / Fact / Mart เท่านั้น'
    f'</div>',
    unsafe_allow_html=True,
)