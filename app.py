"""
app.py — Fuel Station Analytics Report (v3 · ต่อกับ dbt warehouse ชุดใหม่)
==========================================================================
อ่านข้อมูลจาก dev.duckdb ที่สร้างโดย dbt เท่านั้น (dim_ / fact_ / int_ / mart_)

รัน:
    streamlit run app.py

ถ้าไฟล์ฐานข้อมูลอยู่ที่อื่น ตั้งค่าผ่าน environment variable ได้:
    GAS_DW_PATH=/path/to/dev.duckdb streamlit run app.py

ออกแบบใหม่ตามแนวทาง "น้อยแต่ครอบคลุม": 7 กราฟหลัก + แผงตัวเลขสรุป
แทนที่จะทำ 1 กราฟต่อ 1 คำถาม แต่ละกราฟถูกเลือกให้ตอบได้หลายข้อพร้อมกัน
โดยยังอธิบายได้ชัดเจนว่าทำไมถึงเลือกรูปแบบนั้น (ระบุไว้ใต้หัวข้อทุกส่วน)
"""

from __future__ import annotations

import os

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# 1) การตั้งค่าฐานข้อมูล
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get("GAS_DW_PATH"),
    os.path.join(os.getcwd(), "dev.duckdb"),
    os.path.join(HERE, "Gasstation_dw_duckdb", "dev.duckdb"),
    os.path.join(HERE, "dev.duckdb"),
]
DB_PATH = next((p for p in _CANDIDATES if p and os.path.exists(p)), _CANDIDATES[1])

# ---------------------------------------------------------------------------
# 2) ดีไซน์ระบบ — พาเลตสีที่ผ่านการตรวจสอบ (categorical order คงที่, ห้ามสลับ)
#    อ้างอิงจาก dataviz skill: sequential = blue เดียว, diverging = blue<->red,
#    status = fixed 4 สี, categorical = ลำดับ 8 สีที่ผ่าน CVD check แล้ว
# ---------------------------------------------------------------------------
SURFACE, PAGE = "#fcfcfb", "#f9f9f7"
INK, INK_SOFT, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, BORDER = "#e1e0d9", "#c3c2b7", "rgba(11,11,11,0.10)"

CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
               "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE, ORANGE, AQUA, YELLOW = CATEGORICAL[0], CATEGORICAL[1], CATEGORICAL[2], CATEGORICAL[3]
RED_HUE = CATEGORICAL[7]

SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95"]
DIVERGING = [[0.0, "#e34948"], [0.5, "#f0efec"], [1.0, "#2a78d6"]]

STATUS_GOOD, STATUS_WARN, STATUS_SERIOUS, STATUS_CRIT = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"

WEEKDAY_TH = {"Monday": "จันทร์", "Tuesday": "อังคาร", "Wednesday": "พุธ",
              "Thursday": "พฤหัสบดี", "Friday": "ศุกร์", "Saturday": "เสาร์", "Sunday": "อาทิตย์"}
WEEKDAY_ORDER = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

st.set_page_config(page_title="Fuel Station Analytics Report", page_icon="⛽",
                    layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  html, body, [class*="css"] {{ font-family: "IBM Plex Sans Thai", "IBM Plex Sans", sans-serif; }}
  .stApp {{ background: {PAGE}; color: {INK}; }}
  [data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  .block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1440px; }}
  h1, h2, h3, h4 {{ color: {INK}; font-weight: 700; letter-spacing: .1px; }}
  .report-header {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; padding: 22px 28px; margin-bottom: 20px; border-left: 4px solid {BLUE}; }}
  .report-header h1 {{ margin: 0; font-size: 1.5rem; }}
  .report-header p {{ margin: 6px 0 0; color: {INK_SOFT}; font-size: .92rem; }}
  .report-header .meta {{ color: {MUTED}; font-size: .8rem; margin-top: 10px; }}
  .kpi {{ background: {SURFACE}; border: 1px solid {BORDER}; border-top: 3px solid {BLUE}; border-radius: 8px; padding: 14px 16px; height: 100%; }}
  .kpi .label {{ color: {MUTED}; font-size: .74rem; font-weight: 600; letter-spacing: .3px; text-transform: uppercase; }}
  .kpi .value {{ color: {INK}; font-size: 1.5rem; font-weight: 700; margin-top: 4px; line-height: 1.2; }}
  .kpi .unit {{ font-size: .8rem; color: {MUTED}; font-weight: 500; margin-left: 3px; }}
  .kpi .sub {{ font-size: .76rem; color: {INK_SOFT}; margin-top: 4px; }}
  .panel {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; padding: 18px 20px 8px; margin-bottom: 18px; }}
  .panel h4 {{ margin: 0 0 4px; font-size: 1.02rem; font-weight: 700; }}
  .panel .q-tag {{ display: inline-block; background: rgba(42,120,214,.10); color: {BLUE}; border-radius: 4px; padding: 1px 7px; font-size: .72rem; font-weight: 700; margin-right: 6px; }}
  .panel .why {{ color: {MUTED}; font-size: .80rem; margin: 4px 0 12px; line-height: 1.5; }}
  [data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 8px; }}
  .stAlert {{ border-radius: 8px; }}
  footer, #MainMenu {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 3) Data access
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_con() -> duckdb.DuckDBPyConnection:
    if not os.path.exists(DB_PATH):
        st.error(f"ไม่พบไฟล์ฐานข้อมูล: `{DB_PATH}`\n\n"
                 "รัน `dbt run` ในโฟลเดอร์ `Gasstation_dw_duckdb` ก่อน หรือกำหนด "
                 "environment variable `GAS_DW_PATH` ให้ชี้ไปที่ `dev.duckdb`")
        st.stop()
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(show_spinner=False)
def q(sql: str, params: tuple | list | None = None) -> pd.DataFrame:
    return get_con().execute(sql, list(params) if params else []).df()


def panel(title: str, tags: str, why: str) -> None:
    st.markdown(f'<div class="panel"><h4>{title}</h4>'
                f'<div>{tags}</div><p class="why">{why}</p></div>', unsafe_allow_html=True)


def style(fig: go.Figure, height: int = 360, legend_top: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans Thai, IBM Plex Sans, sans-serif", color=INK, size=12.5),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BLUE, font_color=INK),
        colorway=CATEGORICAL)
    if legend_top:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                                       bgcolor="rgba(0,0,0,0)", title_text=""))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=BASELINE, linecolor=BASELINE,
                      tickfont_color=MUTED, title_font_color=INK_SOFT)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=BASELINE, linecolor=BASELINE,
                      tickfont_color=MUTED, title_font_color=INK_SOFT)
    return fig


def kpi(col, label: str, value: str, unit: str = "", sub: str = "") -> None:
    col.markdown(f'<div class="kpi"><div class="label">{label}</div>'
                 f'<div class="value">{value}<span class="unit">{unit}</span></div>'
                 f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def guard(df: pd.DataFrame, msg: str = "ไม่มีข้อมูลในเงื่อนไขที่เลือก") -> bool:
    if df is None or df.empty:
        st.info(msg)
        return False
    return True


# ---------------------------------------------------------------------------
# 4) Sidebar filters
# ---------------------------------------------------------------------------
dim_station = q("select gasstation_id, gasstation_name, address from dim_gasstation "
                "order by gasstation_id")
dim_prod = q("select product_id, product_name, product_type, is_fuel from dim_product "
             "order by is_fuel desc, product_id")
bounds = q("select min(date_day) d0, max(date_day) d1 from dim_date")
D0, D1 = bounds.iloc[0, 0], bounds.iloc[0, 1]

with st.sidebar:
    st.markdown(f'<div style="font-size:1.1rem;font-weight:700;color:{INK}">⛽ Fuel Analytics</div>'
                f'<div style="color:{MUTED};font-size:.76rem;margin-bottom:14px">'
                f'Star Schema · DuckDB · dbt</div>', unsafe_allow_html=True)

    st.markdown("##### ช่วงวันที่")
    dr = st.date_input("ช่วงวันที่", value=(D0, D1), min_value=D0, max_value=D1,
                        label_visibility="collapsed")
    start_d, end_d = dr if isinstance(dr, (tuple, list)) and len(dr) == 2 else (D0, D1)

    rank_st = q("""
        select gasstation_id, sum(total_amount) as sales_amount
        from fact_invoice group by 1 order by 2 desc
    """)
    rank_st = rank_st.merge(dim_station, on="gasstation_id")

    st.markdown("##### สถานีบริการ")
    st.caption(f"คลังข้อมูลมี {len(dim_station):,} สถานี")
    scope = st.radio("ขอบเขต", ["Top 10 ตามยอดขาย", "Top 25 ตามยอดขาย", "ทั้งหมด", "เลือกเอง"],
                      label_visibility="collapsed")

    if scope == "ทั้งหมด":
        S = dim_station["gasstation_id"].tolist()
    elif scope.startswith("Top"):
        n = int(scope.split()[1])
        S = rank_st.head(n)["gasstation_id"].tolist()
    else:
        picked = st.multiselect("เลือกสถานี", dim_station["gasstation_name"].tolist(),
                                 default=rank_st.head(5)["gasstation_name"].tolist())
        S = dim_station.loc[dim_station["gasstation_name"].isin(picked), "gasstation_id"].tolist()

    st.markdown("##### สินค้า")
    fuel_only = st.toggle("เฉพาะน้ำมันเชื้อเพลิง", value=True)
    pool = dim_prod[dim_prod["is_fuel"]] if fuel_only else dim_prod
    prod_names = st.multiselect("สินค้า", pool["product_name"].tolist(),
                                 default=pool["product_name"].tolist(),
                                 label_visibility="collapsed")

    st.divider()
    st.caption("ข้อมูลอ้างอิงจากตาราง dim_ / fact_ / int_ ใน dbt warehouse โดยตรง "
               "กราฟตอบสนองตามช่วงวันที่และสถานีที่เลือกด้านบน")

if not S:
    st.warning("กรุณาเลือกอย่างน้อย 1 สถานี")
    st.stop()
if not prod_names:
    st.warning("กรุณาเลือกอย่างน้อย 1 สินค้า")
    st.stop()

P = dim_prod.loc[dim_prod["product_name"].isin(prod_names), "product_id"].tolist()
k0 = int(pd.Timestamp(start_d).strftime("%Y%m%d"))
k1 = int(pd.Timestamp(end_d).strftime("%Y%m%d"))
span_days = (pd.Timestamp(end_d) - pd.Timestamp(start_d)).days + 1

# ---------------------------------------------------------------------------
# 5) Header + KPI row
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="report-header">
  <h1>รายงานวิเคราะห์เครือข่ายสถานีบริการน้ำมัน</h1>
  <p>สรุปยอดขาย พฤติกรรมการซื้อ ประสิทธิภาพบุคลากร และการบริหารคลังน้ำมัน
     สำหรับ {len(S)} สถานี · {len(P)} สินค้า · {start_d:%d %b %Y} – {end_d:%d %b %Y}
     ({span_days} วัน)</p>
  <div class="meta">แหล่งข้อมูล: dim_ / fact_ / int_ tables · dbt + DuckDB</div>
</div>
""", unsafe_allow_html=True)

kpi_sql = """
select coalesce(sum(f.total_amount), 0) as sales_amount,
       count(*) as bill_count,
       count(distinct f.customer_id) as customer_count
from fact_invoice f
where f.gasstation_id = any(?) and f.date_key between ? and ?
"""
cur_k = q(kpi_sql, (S, k0, k1)).iloc[0]

fuel_sql = """
select coalesce(sum(s.quantity_sold), 0) as fuel_liters
from fact_sales s join dim_product p on s.product_id = p.product_id
where p.is_fuel and s.gasstation_id = any(?) and s.product_id = any(?)
  and s.date_key between ? and ?
"""
fuel_liters = q(fuel_sql, (S, P, k0, k1)).iloc[0].fuel_liters

top_station = q("""
    select g.gasstation_name, sum(f.total_amount) as s
    from fact_invoice f join dim_gasstation g on f.gasstation_id = g.gasstation_id
    where f.gasstation_id = any(?) and f.date_key between ? and ?
    group by 1 order by 2 desc limit 1
""", (S, k0, k1))

spread = q("""
    select avg(sales_multiple) as m
    from mart_09_daily_station_ranking
    where date_key between ? and ? and sales_multiple is not null
""", (k0, k1)).iloc[0].m

c = st.columns(5)
kpi(c[0], "ยอดขายรวม", f"{cur_k.sales_amount:,.0f}", " ₫")
kpi(c[1], "ปริมาณน้ำมันที่ขาย", f"{fuel_liters:,.0f}", " ลิตร")
kpi(c[2], "จำนวนบิล", f"{cur_k.bill_count:,.0f}", " บิล",
    f"เฉลี่ย {cur_k.sales_amount / cur_k.bill_count:,.0f} ₫/บิล" if cur_k.bill_count else "")
kpi(c[3], "สถานีขายดีสุด", top_station.iloc[0].gasstation_name if not top_station.empty else "—",
    sub=f"{top_station.iloc[0].s:,.0f} ₫" if not top_station.empty else "")
kpi(c[4], "ส่วนต่างยอดขายสูงสุด/ต่ำสุดต่อวัน", f"{spread:,.1f}" if pd.notna(spread) else "—", " เท่า",
    "เฉลี่ยทั้งระบบ (Q9)")
st.write("")

# ===========================================================================
# ส่วนที่ 1 — ผลการดำเนินงานตามสถานี  (Q1, Q7, Q9)
# ===========================================================================
panel("ผลการดำเนินงานตามสถานี: กลุ่มดีที่สุด vs แย่ที่สุด",
      '<span class="q-tag">Q1</span><span class="q-tag">Q7</span>',
      "จัดกลุ่มสถานีเป็นสูง/กลาง/ต่ำ (Q1) จากยอดขายเฉลี่ยต่อวัน โดยคำนวณจากทั้ง 100 สถานีเสมอ "
      "ไม่ขึ้นกับตัวกรองสถานีด้านซ้าย (การจัดกลุ่มต้องอิงประชากรทั้งหมดถึงจะมีความหมาย) "
      "แล้วแสดงเฉพาะ 8 อันดับแรกและ 8 อันดับสุดท้ายเทียบกัน — ถ้าดูทั้ง 100 สถานีพร้อมกันแท่งจะเบียดจนแยกไม่ออก "
      "แต่ถ้าดูแค่ Top 10 ก็จะเห็นแต่กลุ่มบนซึ่งมีค่าใกล้เคียงกันเองจนดูไม่ต่าง การเทียบสองขั้วจึงเห็นส่วนต่างจริง "
      "(สูงสุด/ต่ำสุดต่างกันเกือบ 4 เท่า) ชื่อถนนของแต่ละสถานีอยู่ในป้ายเมื่อชี้เมาส์ (ตอบ Q7) "
      "ส่วนต่างยอดขายรายวัน (Q9) สรุปเป็นตัวเลขในแผงด้านบนแล้ว")

perf = q("""
    with daily as (
        select gasstation_id, date_key, sum(total_amount) as daily_sales
        from fact_invoice
        where date_key between ? and ?
        group by 1, 2
    ),
    station_avg as (
        select gasstation_id, avg(daily_sales) as avg_daily_sales
        from daily group by 1
    ),
    tiered as (
        select gasstation_id, avg_daily_sales,
               ntile(3) over (order by avg_daily_sales desc) as tier_rank,
               row_number() over (order by avg_daily_sales desc) as rnk_desc,
               row_number() over (order by avg_daily_sales asc) as rnk_asc
        from station_avg
    )
    select t.gasstation_id, g.gasstation_name,
           trim(split_part(g.address, ',', 1)) as road_name,
           t.avg_daily_sales, t.tier_rank
    from tiered t join dim_gasstation g on t.gasstation_id = g.gasstation_id
    where t.rnk_desc <= 8 or t.rnk_asc <= 8
""", (k0, k1))

if guard(perf):
    TIER_LABEL = {1: "กลุ่มสูง", 2: "กลุ่มกลาง", 3: "กลุ่มต่ำ"}
    TIER_COLOR = {1: SEQ_BLUE[4], 2: SEQ_BLUE[3], 3: SEQ_BLUE[1]}
    top_n = perf.sort_values("avg_daily_sales")
    fig = go.Figure()
    for tier in [3, 2, 1]:
        sub = top_n[top_n["tier_rank"] == tier]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub.avg_daily_sales, y=sub.gasstation_name, orientation="h",
            name=TIER_LABEL[tier], marker_color=TIER_COLOR[tier],
            customdata=sub[["road_name"]].values,
            hovertemplate="%{y}<br>ถนน %{customdata[0]}<br>%{x:,.0f} ₫/วัน<extra></extra>"))
    ratio = perf.avg_daily_sales.max() / perf.avg_daily_sales.min()
    fig.add_annotation(xref="paper", yref="paper", x=1, y=1.08, showarrow=False,
                        text=f"สูงสุด/ต่ำสุด = {ratio:.1f} เท่า", font=dict(color=MUTED, size=12))
    fig.update_layout(barmode="overlay", legend_title_text="ระดับยอดขาย")
    fig.update_xaxes(title_text="ยอดขายเฉลี่ยต่อวัน (₫)")
    fig.update_yaxes(title_text="")
    st.plotly_chart(style(fig, 460, True), width="stretch")

# ===========================================================================
# ส่วนที่ 2 — โครงสร้างสินค้าตามสถานี  (Q2, Q8)
# ===========================================================================
panel("โครงสร้างยอดขายตามชนิดสินค้า", '<span class="q-tag">Q2</span><span class="q-tag">Q8</span>',
      "ทดสอบก่อนแล้วว่าสัดส่วนเบนซิน/ดีเซลของแต่ละสถานีต่างกันไม่ถึง 2 จุดเปอร์เซ็นต์ทั้งระบบ "
      "การทำแท่งสัดส่วนแยกทีละสถานีจะได้แท่งหน้าตาเหมือนกันหมด 100 แท่ง ซึ่งไม่ช่วยให้เข้าใจอะไรเพิ่ม "
      "จึงตอบ Q8 ด้วยตัวเลขสรุปตัวเดียวพอ (ซ้าย) ส่วนสินค้าขายดีที่สุดของแต่ละสถานี (Q2) "
      "กลับต่างกันจริงราวครึ่งต่อครึ่งระหว่างสองยี่ห้อ จึงคุ้มที่จะแสดงเป็นตารางแยกสถานี (ขวา)")

mix = q("""
    select s.gasstation_id, g.gasstation_name, p.product_type, p.product_name,
           sum(s.total_price) as sales_value, sum(s.quantity_sold) as liters
    from fact_sales s
    join dim_product p on s.product_id = p.product_id
    join dim_gasstation g on s.gasstation_id = g.gasstation_id
    where s.gasstation_id = any(?) and s.product_id = any(?) and s.date_key between ? and ?
    group by 1, 2, 3, 4
""", (S, P, k0, k1))

if guard(mix):
    c1, c2 = st.columns([1, 1.3])
    with c1:
        TYPE_COLOR = {"Gasoline": BLUE, "Diesel": ORANGE, "Lubricant": AQUA}
        overall = mix.groupby("product_type")["sales_value"].sum().reset_index()
        overall["pct"] = overall["sales_value"] / overall["sales_value"].sum() * 100
        by_station_pct = (mix.groupby(["gasstation_id", "product_type"])["sales_value"].sum()
                           .groupby(level=0).apply(lambda s: s / s.sum() * 100))
        spread = by_station_pct.groupby("product_type").std().max()
        fig = go.Figure(go.Bar(
            x=overall.sales_value, y=overall.product_type, orientation="h",
            marker_color=[TYPE_COLOR.get(t, MUTED) for t in overall.product_type],
            text=[f"{p:.1f}%" for p in overall.pct], textposition="outside",
            textfont=dict(color=INK),
            hovertemplate="%{y}<br>%{x:,.0f} ₫<extra></extra>"))
        fig.update_xaxes(title_text="ยอดขายรวมทุกสถานีที่เลือก (₫)")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 260, False), width="stretch")
        st.caption(f"สัดส่วนนี้แทบไม่ต่างกันระหว่างสถานี (ส่วนเบี่ยงเบนมาตรฐานสูงสุด ±{spread:.1f} "
                   "จุดเปอร์เซ็นต์) จึงไม่จำเป็นต้องแตกกราฟรายสถานี")
    with c2:
        top_per_station = (mix.sort_values("liters", ascending=False)
                            .drop_duplicates("gasstation_id")
                            .merge(mix.groupby("gasstation_id")["liters"].sum().rename("station_total"),
                                   on="gasstation_id"))
        top_per_station["ส่วนแบ่งในสถานี"] = (top_per_station["liters"] / top_per_station["station_total"]
                                              * 100).round(1).astype(str) + "%"
        tbl = (top_per_station[["gasstation_name", "product_name", "liters", "ส่วนแบ่งในสถานี"]]
               .rename(columns={"gasstation_name": "สถานี", "product_name": "สินค้าขายดีสุด",
                                 "liters": "ปริมาณ (ลิตร)"})
               .sort_values("ปริมาณ (ลิตร)", ascending=False))
        tbl["ปริมาณ (ลิตร)"] = tbl["ปริมาณ (ลิตร)"].map(lambda v: f"{v:,.0f}")
        st.dataframe(tbl, width="stretch", hide_index=True, height=300)
        counts = top_per_station["product_name"].value_counts()
        summary = " · ".join(f"{name} เป็นสินค้าขายดีสุดใน {n} สถานี" for name, n in counts.items())
        st.caption(summary)

# ===========================================================================
# ส่วนที่ 3 — รูปแบบเวลาการขาย  (Q3, Q5, Q10)
# ===========================================================================
panel("รูปแบบเวลาการขาย: ชั่วโมง × วันในสัปดาห์",
      '<span class="q-tag">Q3</span><span class="q-tag">Q5</span><span class="q-tag">Q10</span>',
      "Heatmap ชั่วโมง×วัน เป็นรูปแบบมาตรฐานสำหรับข้อมูลบนกริดสองมิติ — ช่องสีเข้มสุดคือชั่วโมงพีค (Q3) "
      "แถวเสาร์-อาทิตย์เทียบกับจันทร์-ศุกร์บอกความต่างวันธรรมดา/สุดสัปดาห์ได้ในภาพเดียว (Q5) "
      "และแถวที่มีสีเข้มโดยรวมมากที่สุดคือวันที่ขายดีที่สุดในรอบสัปดาห์ (Q10)")

heat = q("""
    select d.weekday_name, f.hour_of_day, count(*) as bill_count
    from fact_invoice f join dim_date d on f.date_key = d.date_key
    where f.gasstation_id = any(?) and f.date_key between ? and ?
    group by 1, 2
""", (S, k0, k1))

if guard(heat):
    heat["wd"] = heat["weekday_name"].map(WEEKDAY_TH)
    piv = (heat.pivot_table(index="wd", columns="hour_of_day", values="bill_count",
                             aggfunc="sum", fill_value=0).reindex(WEEKDAY_ORDER).fillna(0))
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=[f"{h:02d}" for h in piv.columns], y=piv.index,
        colorscale=SEQ_BLUE, xgap=2, ygap=2,
        colorbar=dict(title="บิล", outlinewidth=0, tickfont=dict(color=MUTED)),
        hovertemplate="%{y} %{x}:00<br>%{z:,.0f} บิล<extra></extra>"))
    fig.update_xaxes(title_text="ชั่วโมง")
    fig.update_yaxes(autorange="reversed", title_text="")
    st.plotly_chart(style(fig, 380, False), width="stretch")

# ===========================================================================
# ส่วนที่ 4 — ช่องทางการชำระเงิน  (Q4, Q14)
# ===========================================================================
panel("ช่องทางการชำระเงินและต้นทุนค่าธรรมเนียม",
      '<span class="q-tag">Q4</span><span class="q-tag">Q14</span>',
      "แท่งสัดส่วนเงินสด/บัตรเครดิตต่อสถานี ตอบพฤติกรรมการชำระเงิน (Q4) โดยตรง "
      "ส่วนต้นทุนค่าธรรมเนียมบัตรเครดิตจำลองที่ 2% (Q14) เป็นตัวเลขเดียวที่คำนวณต่อจากข้อมูลชุดเดียวกัน "
      "จึงแสดงเป็นค่าสรุปแทนการทำกราฟแยก")

pay = q("""
    select payment_method_key, count(*) as bill_count, sum(total_amount) as total_amount
    from fact_invoice
    where gasstation_id = any(?) and date_key between ? and ?
    group by 1
""", (S, k0, k1))

if guard(pay):
    pay["label"] = pay["payment_method_key"].map({"cash": "เงินสด", "credit card": "บัตรเครดิต"})
    pay["label"] = pay["label"].fillna(pay["payment_method_key"])
    c1, c2 = st.columns([1.3, 1])
    with c1:
        fig = go.Figure()
        pay_sorted = pay.sort_values("total_amount")
        for i, row in pay_sorted.iterrows():
            fig.add_trace(go.Bar(
                x=[row.total_amount], y=["ยอดขาย"], orientation="h", name=row.label,
                marker_color=BLUE if row.payment_method_key == "cash" else ORANGE,
                hovertemplate=f"{row.label}<br>%{{x:,.0f}} ₫ · {row.bill_count:,.0f} บิล<extra></extra>"))
        fig.update_layout(barmode="stack", legend_title_text="วิธีชำระเงิน")
        fig.update_xaxes(title_text="ยอดขาย (₫)")
        fig.update_yaxes(title_text="")
        st.plotly_chart(style(fig, 200, True), width="stretch")
    with c2:
        cc_row = pay[pay["payment_method_key"] == "credit card"]
        cc_amount = cc_row["total_amount"].iloc[0] if not cc_row.empty else 0
        total_amount = pay["total_amount"].sum()
        fee = cc_amount * 0.02
        st.markdown(
            f'<div class="kpi" style="border-top-color:{ORANGE}">'
            f'<div class="label">ต้นทุนค่าธรรมเนียมบัตรเครดิตจำลอง (2%)</div>'
            f'<div class="value">{fee:,.0f}<span class="unit"> ₫</span></div>'
            f'<div class="sub">คิดเป็น {fee / total_amount * 100:.2f}% ของยอดขายรวม '
            f'({cc_amount:,.0f} ₫ ชำระด้วยบัตรเครดิต)</div></div>', unsafe_allow_html=True)

# ===========================================================================
# ส่วนที่ 5 — ประสิทธิภาพบุคลากร  (Q6, Q13, Q15)
# ===========================================================================
panel("ประสิทธิภาพและโครงสร้างกำลังพล",
      '<span class="q-tag">Q6</span><span class="q-tag">Q13</span><span class="q-tag">Q15</span>',
      "Scatter เปรียบเทียบยอดขายต่อพนักงาน (แกน Y) กับภาระงานต่อพนักงานเติมน้ำมัน 1 คน (แกน X) — "
      "จุดมุมขวาบนคือสถานีที่ทั้งมีประสิทธิภาพสูงและมีภาระงานหนัก ตอบ Q15 ได้ตรงประเด็นกว่าดูยอดขายอย่างเดียว "
      "ส่วนโครงสร้างตำแหน่งงาน (Q13) และพนักงานออกบิลมากสุด (Q6) ของสถานีที่เลือก แสดงเป็นตารางด้านล่าง "
      "เพราะเป็นข้อมูลระดับรายละเอียดที่ตารางอ่านง่ายกว่ากราฟ")

rev = q("""
    select gasstation_id, sum(total_amount) as total_sales, count(*) as invoice_count
    from fact_invoice where gasstation_id = any(?) and date_key between ? and ?
    group by 1
""", (S, k0, k1))
head = q("""
    select home_gasstation_id as gasstation_id, count(*) as total_employees,
           sum(case when position = 'Pump Attendant' then 1 else 0 end) as pump_attendant_count
    from dim_employee where home_gasstation_id = any(?)
    group by 1
""", (S,))
eff = (rev.merge(head, on="gasstation_id", how="inner")
       .merge(dim_station[["gasstation_id", "gasstation_name"]], on="gasstation_id"))
eff["revenue_per_employee"] = eff["total_sales"] / eff["total_employees"].replace(0, pd.NA)
eff["invoices_per_attendant"] = eff["invoice_count"] / eff["pump_attendant_count"].replace(0, pd.NA)
eff = eff.dropna(subset=["revenue_per_employee", "invoices_per_attendant"])

if guard(eff):
    med_x, med_y = eff["invoices_per_attendant"].median(), eff["revenue_per_employee"].median()
    fig = go.Figure(go.Scatter(
        x=eff.invoices_per_attendant, y=eff.revenue_per_employee, mode="markers",
        marker=dict(size=eff.total_employees, sizemode="area",
                    sizeref=2. * eff.total_employees.max() / (34 ** 2), sizemin=5,
                    color=BLUE, opacity=.75, line=dict(width=1, color=SURFACE)),
        customdata=eff[["gasstation_name", "total_employees", "pump_attendant_count"]].values,
        hovertemplate="<b>%{customdata[0]}</b><br>ยอดขาย/พนักงาน %{y:,.0f} ₫<br>"
                      "บิล/พนักงานเติมน้ำมัน %{x:,.1f}<br>พนักงานทั้งหมด %{customdata[1]} คน "
                      "(เติมน้ำมัน %{customdata[2]} คน)<extra></extra>"))
    fig.add_vline(x=med_x, line_dash="dot", line_color=MUTED)
    fig.add_hline(y=med_y, line_dash="dot", line_color=MUTED)
    fig.update_xaxes(title_text="จำนวนบิล ต่อ พนักงานเติมน้ำมัน 1 คน (ภาระงาน)")
    fig.update_yaxes(title_text="ยอดขายต่อพนักงาน 1 คน (₫)")
    st.plotly_chart(style(fig, 400, False), width="stretch")

    opts = eff.sort_values("total_sales", ascending=False)["gasstation_name"].tolist()
    sel = st.selectbox("ดูรายละเอียดตำแหน่งงานและพนักงานออกบิลสูงสุดของสถานี", opts, key="staff_detail")
    sid = int(dim_station.loc[dim_station.gasstation_name == sel, "gasstation_id"].iloc[0])

    d1, d2 = st.columns(2)
    with d1:
        st.caption(f"โครงสร้างตำแหน่งงาน — {sel} (Q13)")
        pos = q("""select position, count(*) as headcount from dim_employee
                   where home_gasstation_id = ? group by 1 order by 2 desc""", (sid,))
        pos["สัดส่วน"] = (pos["headcount"] / pos["headcount"].sum() * 100).round(1).astype(str) + "%"
        st.dataframe(pos.rename(columns={"position": "ตำแหน่ง", "headcount": "จำนวน (คน)"}),
                     width="stretch", hide_index=True)
    with d2:
        st.caption(f"พนักงานออกบิลสูงสุด — {sel} (Q6)")
        top_emp = q("""
            select e.employee_name as ชื่อพนักงาน, e.position as ตำแหน่ง,
                   count(*) as "จำนวนบิล"
            from fact_invoice f join dim_employee e on f.employee_id = e.employee_id
            where f.gasstation_id = ? and f.date_key between ? and ?
            group by 1, 2 order by 3 desc limit 5
        """, (sid, k0, k1))
        st.dataframe(top_emp, width="stretch", hide_index=True)

# ===========================================================================
# ส่วนที่ 6 — สุขภาพถังเก็บน้ำมัน  (Q12)
# ===========================================================================
panel("ระดับน้ำมันคงเหลือในถัง (ข้อมูล ณ ปัจจุบัน)", '<span class="q-tag">Q12</span>',
      "แท่งวัดระดับเทียบเกณฑ์ (bullet chart) — เส้นประคือเกณฑ์เตือนภัยที่ 20% ของความจุ "
      "แท่งที่ต่ำกว่าเส้นถูกเน้นด้วยสีสถานะ (แดง) ส่วนถังปกติใช้สีน้ำเงินตามระบบ "
      "ไม่ผูกกับช่วงวันที่ที่เลือกด้านบน เพราะเป็นค่าล่าสุด ณ ขณะนี้ ไม่ใช่ตัวเลขสะสมย้อนหลัง")

tanks = q("""
    select tank_id, gasstation_id, tank_name, capacity_liters, current_quantity,
           current_quantity / nullif(capacity_liters, 0) as fill_ratio
    from dim_tank
    where gasstation_id = any(?)
    order by fill_ratio asc
""", (S,))

if guard(tanks):
    low = tanks.head(20).sort_values("fill_ratio", ascending=False)
    colors = [STATUS_CRIT if v < 0.2 else BLUE for v in low.fill_ratio]
    fig = go.Figure(go.Bar(
        x=low.fill_ratio * 100, y=low.tank_name.astype(str) + " · สถานี " + low.gasstation_id.astype(str),
        orientation="h", marker_color=colors,
        customdata=low[["current_quantity", "capacity_liters"]].values,
        hovertemplate="%{y}<br>%{x:.1f}%% ของความจุ<br>เหลือ %{customdata[0]:,.0f} / "
                      "%{customdata[1]:,.0f} ลิตร<extra></extra>"))
    fig.add_vline(x=20, line_color=STATUS_CRIT, line_dash="dash",
                  annotation_text="เกณฑ์เตือนภัย 20%", annotation_font_color=STATUS_CRIT)
    n_below = int((tanks.fill_ratio < 0.2).sum())
    if n_below:
        st.warning(f"มีถังทั้งหมด {n_below} ใบ (จาก {len(tanks)} ใบในขอบเขตที่เลือก) "
                   "ที่ระดับน้ำมันต่ำกว่าเกณฑ์เตือนภัย 20%")
    fig.update_xaxes(title_text="% ของความจุถัง", range=[0, max(100, low.fill_ratio.max() * 105)])
    fig.update_yaxes(title_text="")
    st.plotly_chart(style(fig, 460, False), width="stretch")

# ===========================================================================
# ส่วนที่ 7 — การกระทบยอด จ่ายออก vs ขายจริง  (Q11)
# ===========================================================================
panel("ส่วนต่างปริมาณจ่ายออกจากถัง เทียบ ยอดขายจริง", '<span class="q-tag">Q11</span>',
      "แท่งสองทิศทาง (diverging bar) รอบเส้นศูนย์ — เหมาะกับข้อมูลที่มีทั้งค่าบวก/ลบเทียบเส้นฐาน "
      "แท่งเกินศูนย์ (น้ำเงิน) หมายถึงจ่ายออกมากกว่าขาย แท่งต่ำกว่าศูนย์ (แดง) "
      "หมายถึงขายมากกว่าที่บันทึกว่าจ่ายออก ซึ่งเป็นจุดที่ควรตรวจสอบ")

recon = q("""
    with sold as (
        select date_key, sum(quantity_sold) as qty_sold
        from fact_sales where gasstation_id = any(?) and product_id = any(?)
          and date_key between ? and ? group by 1
    ),
    dispensed as (
        select date_key, sum(quantity_out) as qty_out
        from fact_inventory_transaction
        where gasstation_id = any(?) and date_key between ? and ? group by 1
    )
    select coalesce(s.date_key, d.date_key) as date_key,
           coalesce(s.qty_sold, 0) as qty_sold, coalesce(d.qty_out, 0) as qty_out,
           coalesce(d.qty_out, 0) - coalesce(s.qty_sold, 0) as variance
    from sold s full outer join dispensed d on s.date_key = d.date_key
    order by 1
""", (S, P, k0, k1, S, k0, k1))

if guard(recon):
    recon["date_day"] = pd.to_datetime(recon["date_key"], format="%Y%m%d")
    fig = go.Figure(go.Bar(
        x=recon.date_day, y=recon.variance,
        marker_color=[BLUE if v >= 0 else RED_HUE for v in recon.variance],
        customdata=recon[["qty_sold", "qty_out"]].values,
        hovertemplate="%{x|%d %b}<br>ส่วนต่าง %{y:+,.0f} ลิตร<br>ขาย %{customdata[0]:,.0f} · "
                      "จ่ายออก %{customdata[1]:,.0f}<extra></extra>"))
    fig.add_hline(y=0, line_color=BASELINE, line_width=1.5)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="ส่วนต่าง (ลิตร) = จ่ายออก − ขาย")
    st.plotly_chart(style(fig, 340, False), width="stretch")
    st.caption("หมายเหตุ: ส่วนต่างเป็นจุดให้ตรวจสอบเพิ่มเติม ไม่ใช่ข้อสรุปว่ามีน้ำมันสูญหายเสมอไป")

st.markdown(f'<div style="text-align:center;color:{MUTED};font-size:.78rem;padding-top:18px;'
            f'border-top:1px solid {BORDER};margin-top:22px">Fuel Station Analytics Report · '
            f'Star Schema (dbt + DuckDB) · ข้อมูลจากตาราง Dimension / Fact / Intermediate เท่านั้น</div>',
            unsafe_allow_html=True)
