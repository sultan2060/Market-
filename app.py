import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# ============== PAGE CONFIG ==============
st.set_page_config(page_title="SPX — تحليل الموجة", page_icon="📈", layout="centered")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  html, body, [class*="css"] { direction: rtl; font-family: 'Tajawal', sans-serif; }
  .stApp { background-color: #0a0d0f; color: #e7ecef; }
  .block-container { padding-top: 1.2rem; max-width: 720px; }
  .mono { font-family: 'JetBrains Mono', monospace; }
  .card { background:#12161a; border:1px solid #232a30; border-radius:16px; padding:16px; margin-bottom:14px; }
  .price-box { background:#161b20; border:1px solid #232a30; border-radius:12px; padding:10px 12px; }
  .lbl { font-size:12px; color:#8b95a1; }
  .val { font-family:'JetBrains Mono', monospace; font-size:20px; font-weight:700; }
  .chip { display:inline-block; background:#161b20; border:1px solid #232a30; border-radius:8px;
          padding:6px 10px; font-family:'JetBrains Mono', monospace; font-size:12px; margin:3px; color:#22c55e; }
  .badge { font-size:12px; font-weight:700; border-radius:8px; padding:4px 10px; border:1px solid; display:inline-block; }
  .buy   { color:#22c55e; border-color:rgba(34,197,94,.4); background:rgba(34,197,94,.08); }
  .sell  { color:#ef4444; border-color:rgba(239,68,68,.4); background:rgba(239,68,68,.08); }
  .neutral { color:#8b95a1; border-color:rgba(139,149,161,.35); background:rgba(139,149,161,.06); }
  .status-live { color:#22c55e; font-weight:700; }
  .status-off  { color:#ef4444; font-weight:700; }
  .wave-call { border:1px solid rgba(34,197,94,.4); background:rgba(34,197,94,.06); }
  .wave-put  { border:1px solid rgba(239,68,68,.4); background:rgba(239,68,68,.06); }
  .target-row { display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-top:1px dashed #232a30; }
  .target-row:first-child{ border-top:none; }
  #MainMenu, footer, header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=60_000, key="auto_refresh")

# ============== DATA FETCH ==============
@st.cache_data(ttl=55, show_spinner=False)
def load_price_data():
    spx_intra = yf.download("^GSPC", period="5d", interval="15m", progress=False, auto_adjust=False)
    spy_intra = yf.download("SPY", period="5d", interval="15m", progress=False, auto_adjust=False)
    spx_daily = yf.download("^GSPC", period="6mo", interval="1d", progress=False, auto_adjust=False)
    return spx_intra, spy_intra, spx_daily

@st.cache_data(ttl=300, show_spinner=False)
def load_options_chain():
    """Uses SPY chain as a liquid proxy for SPX gamma walls (no free SPX index option chain available)."""
    tk = yf.Ticker("SPY")
    expiries = tk.options
    if not expiries:
        return None
    exp = expiries[0]
    chain = tk.option_chain(exp)
    return {"expiry": exp, "calls": chain.calls, "puts": chain.puts}

status_ok = True
try:
    spx_intra, spy_intra, spx_daily = load_price_data()
    if spx_intra.empty or spy_intra.empty:
        status_ok = False
except Exception:
    status_ok = False

# ============== INDICATORS ==============
def calc_rsi(s, period=14):
    d = s.diff()
    gain, loss = d.clip(lower=0), -d.clip(upper=0)
    ag, al = gain.rolling(period).mean(), loss.rolling(period).mean()
    rs = ag / al.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)

def calc_macd(s, fast=12, slow=26, signal=9):
    ef, es = s.ewm(span=fast, adjust=False).mean(), s.ewm(span=slow, adjust=False).mean()
    macd = ef - es
    sig = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig, macd - sig

def calc_stoch(df, period=14, smooth=3):
    lo, hi = df["Low"].rolling(period).min(), df["High"].rolling(period).max()
    k = 100 * (df["Close"] - lo) / (hi - lo)
    return k.fillna(50), k.rolling(smooth).mean().fillna(50)

def calc_roc(s, period=9):
    return ((s - s.shift(period)) / s.shift(period) * 100).fillna(0)

def calc_cmf(df, period=20):
    mfm = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / (df["High"] - df["Low"]).replace(0, np.nan)
    mfv = mfm * df["Volume"]
    cmf = mfv.rolling(period).sum() / df["Volume"].rolling(period).sum()
    return cmf.fillna(0)

def historical_vol(s, bars_per_day=26, trading_days=252):
    r = np.log(s / s.shift(1)).dropna()
    if len(r) < 10:
        return 0.18
    return float(min(1.2, max(0.05, r.std() * math.sqrt(bars_per_day * trading_days))))

def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def black_scholes(S, K, T, r, sigma, is_call=True):
    T = max(T, 0.0001)
    d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if is_call:
        return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2), norm_cdf(d1)
    return K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1), norm_cdf(d1) - 1

def fmt(n, d=2):
    try:
        return f"{n:,.{d}f}"
    except Exception:
        return "—"

# ============== HEADER ==============
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
  <div>
    <div style="font-weight:900;font-size:20px;">SPX — تحليل الموجة والاتجاه</div>
    <div style="font-size:12px;color:#8b95a1;">بيانات حية من Yahoo Finance عبر yfinance — خادم مباشر بدون API key</div>
  </div>
  <div class="{'status-live' if status_ok else 'status-off'}">{'🟢 متصل' if status_ok else '🔴 غير متصل'}</div>
</div>
""", unsafe_allow_html=True)

if not status_ok:
    st.error("تعذّر جلب البيانات حاليًا. سيعيد التطبيق المحاولة تلقائيًا كل 60 ثانية.")
    st.stop()

spx_close = spx_intra["Close"].dropna()
spy_close = spy_intra["Close"].dropna()
spx = float(spx_close.iloc[-1])
spy = float(spy_close.iloc[-1])
spx_prev = float(spx_close.iloc[-2]) if len(spx_close) > 1 else spx
spx_chg = spx - spx_prev
ratio = spx / spy  # live SPX/SPY ratio, used to translate SPY strikes into SPX-equivalent levels

st.markdown(f"""<div class="price-box">
<div class="lbl">S&amp;P 500 · SPX</div>
<div class="val">{fmt(spx)}</div>
<div class="mono" style="color:{'#22c55e' if spx_chg>=0 else '#ef4444'};font-size:12px;">
{'▲' if spx_chg>=0 else '▼'} {fmt(abs(spx_chg))} ({fmt(abs(spx_chg/spx*100))}%)</div></div>""", unsafe_allow_html=True)

st.line_chart(spx_close.tail(150), height=180)

# ============== INDICATORS ==============
rsi = calc_rsi(spx_close)
macd, macd_sig, macd_hist = calc_macd(spx_close)
k, d = calc_stoch(spx_intra)
roc = calc_roc(spx_close)
cmf = calc_cmf(spx_intra)

rsi_l, macd_l, hist_l, k_l, roc_l, cmf_l = rsi.iloc[-1], macd.iloc[-1], macd_hist.iloc[-1], k.iloc[-1], roc.iloc[-1], cmf.iloc[-1]

# last candle strength
last = spx_intra.iloc[-1]
body = abs(last["Close"] - last["Open"])
rng = max(last["High"] - last["Low"], 1e-6)
body_ratio = float(body / rng)
candle_bullish = last["Close"] > last["Open"]
candle_strength = "قوية" if body_ratio > 0.6 else ("متوسطة" if body_ratio > 0.3 else "ضعيفة")

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### المؤشرات الفنية")
st.caption("RSI · MACD · Stochastic · ROC · تدفق الأموال (CMF) — من بيانات فعلية 15 دقيقة")

c1, c2, c3 = st.columns(3)
c1.metric("RSI", fmt(rsi_l))
c2.metric("MACD Hist", fmt(hist_l))
c3.metric("Stochastic K", fmt(k_l))
c4, c5, c6 = st.columns(3)
c4.metric("ROC (9)", f"{fmt(roc_l)}%")
c5.metric("تدفق الأموال CMF", fmt(cmf_l, 3))
c6.metric("قوة الشمعة الأخيرة", f"{candle_strength} ({'صاعدة' if candle_bullish else 'هابطة'})")
st.markdown('</div>', unsafe_allow_html=True)

# ============== CALL WALL / PUT WALL ==============
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### Call Wall / Put Wall")
st.caption("من التمركز الفعلي للعقود المفتوحة (Open Interest) على SPY — أقرب انتهاء متاح، محوّلة لمستوى SPX")

call_wall_spx = put_wall_spx = None
try:
    oc = load_options_chain()
    if oc:
        calls, puts = oc["calls"], oc["puts"]
        near_calls = calls[(calls["strike"] > spy * 0.9) & (calls["strike"] < spy * 1.1)]
        near_puts = puts[(puts["strike"] > spy * 0.9) & (puts["strike"] < spy * 1.1)]
        if not near_calls.empty:
            call_wall_spy = float(near_calls.loc[near_calls["openInterest"].idxmax(), "strike"])
            call_wall_spx = call_wall_spy * ratio
        if not near_puts.empty:
            put_wall_spy = float(near_puts.loc[near_puts["openInterest"].idxmax(), "strike"])
            put_wall_spx = put_wall_spy * ratio

        w1, w2 = st.columns(2)
        w1.markdown(f"<div class='price-box'><div class='lbl'>🧱 Call Wall (مقاومة جاما)</div><div class='val' style='color:#ef4444;'>{fmt(call_wall_spx) if call_wall_spx else '—'}</div></div>", unsafe_allow_html=True)
        w2.markdown(f"<div class='price-box'><div class='lbl'>🧱 Put Wall (دعم جاما)</div><div class='val' style='color:#22c55e;'>{fmt(put_wall_spx) if put_wall_spx else '—'}</div></div>", unsafe_allow_html=True)
        st.caption(f"انتهاء العقود المستخدم: {oc['expiry']}")
    else:
        st.info("بيانات سلسلة الخيارات غير متاحة حاليًا من المصدر.")
except Exception:
    st.info("تعذّر جلب بيانات Call Wall / Put Wall حاليًا — سيعاد المحاولة تلقائيًا.")
st.markdown('</div>', unsafe_allow_html=True)

# ============== WAVE / REVERSAL TARGET ENGINE ==============
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### تحليل الموجة ونقطة الانعكاس")
st.caption("رصد آخر أرجل الحركة (Swing) وإسقاط أهداف فيبوناتشي من نقطة الانعكاس المحتملة")

LOOKBACK = 60
window = spx_intra.tail(LOOKBACK)
swing_high_idx = window["High"].idxmax()
swing_low_idx = window["Low"].idxmin()
swing_high = float(window.loc[swing_high_idx, "High"])
swing_low = float(window.loc[swing_low_idx, "Low"])
leg_len = swing_high - swing_low

if swing_low_idx > swing_high_idx:
    geo_bias = "call"
    reversal_point = swing_low
    reversal_time = swing_low_idx
    leg_start_time = swing_high_idx
else:
    geo_bias = "put"
    reversal_point = swing_high
    reversal_time = swing_high_idx
    leg_start_time = swing_low_idx

bars_in_leg = max(1, abs(window.index.get_loc(reversal_time) - window.index.get_loc(leg_start_time)))

score = 0
score += 1 if rsi_l < 45 else (-1 if rsi_l > 55 else 0)
score += 1 if hist_l >= 0 else -1
score += 1 if k_l < 40 else (-1 if k_l > 60 else 0)
score += 1 if roc_l > 0 else -1
score += 1 if cmf_l > 0 else -1
score += 1 if candle_bullish else -1

if put_wall_spx and abs(spx - put_wall_spx) / spx < 0.01:
    score += 1
if call_wall_spx and abs(spx - call_wall_spx) / spx < 0.01:
    score -= 1

confluence_bias = "call" if score > 0 else ("put" if score < 0 else "neutral")

if geo_bias == confluence_bias:
    wave_type, confidence = geo_bias, min(95, 55 + abs(score) * 8)
elif confluence_bias == "neutral":
    wave_type, confidence = geo_bias, 40
else:
    wave_type, confidence = "انتظار", 30

direction = 1 if wave_type == "call" else (-1 if wave_type == "put" else 0)

if direction != 0:
    t1 = reversal_point + direction * leg_len * 1.0
    t2 = reversal_point + direction * leg_len * 1.272
    t3 = reversal_point + direction * leg_len * 1.618
    velocity = leg_len / bars_in_leg

    def bars_needed(target):
        dist = abs(target - spx)
        return max(1, dist / max(velocity, 0.01))

    def bars_to_time(bars):
        hours = bars * 15 / 60
        if hours < 6.5:
            return f"~{fmt(hours,1)} ساعة (نفس الجلسة)"
        days = hours / 6.5
        return f"~{fmt(days,1)} يوم تداول"

    entry_low = min(spx, reversal_point) if wave_type == "call" else spx
    entry_high = spx if wave_type == "call" else max(spx, reversal_point)
    stop_level = swing_low if wave_type == "call" else swing_high

    wave_class = "wave-call" if wave_type == "call" else "wave-put"
    label = "🟢 موجة CALL — انعكاس صاعد محتمل" if wave_type == "call" else "🔴 موجة PUT — انعكاس هابط محتمل"

    st.markdown(f"""<div class="card {wave_class}" style="margin-bottom:0;">
    <div style="font-weight:700;font-size:15px;margin-bottom:6px;">{label}</div>
    <div style="font-size:12px;color:#8b95a1;">درجة الثقة (توافق المؤشرات): <b>{confidence}%</b></div>
    <div style="margin-top:10px;">منطقة الدخول المقترحة: <span class="mono" style="color:#e6b455;">{fmt(entry_low)} — {fmt(entry_high)}</span></div>
    <div>وقف الخسارة (خلف نقطة الانعكاس): <span class="mono" style="color:#ef4444;">{fmt(stop_level)}</span></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:12px;font-weight:700;'>الأهداف والمدة الزمنية المقدّرة</div>", unsafe_allow_html=True)
    for i, t in enumerate([t1, t2, t3], start=1):
        eta = bars_to_time(bars_needed(t))
        st.markdown(f"""<div class="target-row">
        <div>هدف {i}</div>
        <div style="text-align:left;"><span class="mono" style="color:#22c55e;font-weight:700;">{fmt(t)}</span>
        <div style="font-size:11px;color:#8b95a1;">{eta}</div></div>
        </div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div class="card" style="margin-bottom:0;border:1px solid rgba(139,149,161,.3);">
    <div style="font-weight:700;">⚪ انتظار — لا يوجد توافق كافٍ بين هندسة الموجة والمؤشرات حاليًا</div>
    <div style="font-size:12px;color:#8b95a1;margin-top:6px;">يُفضّل الانتظار حتى يتوافق اتجاه الموجة مع تأكيد المؤشرات قبل الدخول.</div>
    </div>""", unsafe_allow_html=True)

st.caption(f"القمة المرجعية: {fmt(swing_high)} — القاع المرجعي: {fmt(swing_low)} — طول الموجة: {fmt(leg_len)} نقطة (آخر {LOOKBACK} شمعة 15 دقيقة)")
st.markdown('</div>', unsafe_allow_html=True)

# ============== OPTIONS SIMULATOR ==============
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### محاكي صفقة الخيارات (Black-Scholes)")
st.caption("مربوط تلقائيًا باتجاه الموجة المكتشف أعلاه — يمكنك التعديل يدويًا")

opt_type = st.radio("نوع العقد", ["CALL (شراء)", "PUT (بيع)"],
                     index=0 if (wave_type != "put") else 1,
                     horizontal=True, label_visibility="collapsed")
is_call = opt_type.startswith("CALL")

dte = st.slider("عدد أيام الانتهاء", 1, 45, 7)
strike_offset = st.slider("إزاحة سعر التنفيذ عن SPY الحالي", -30, 30, 0)
hv_default = round(historical_vol(spx_close) * 100)
iv_pct = st.slider("التقلب التاريخي المقدر (%)", 5, 80, hv_default)
contracts = st.number_input("عدد العقود", min_value=1, max_value=50, value=1)

K = round(spy + strike_offset)
T, r, iv = dte / 365, 0.045, iv_pct / 100
premium, delta = black_scholes(spy, K, T, r, iv, is_call)
premium = max(0.05, premium)
move = spy * iv * math.sqrt(T)
target_spy = spy + move * 0.9 if is_call else spy - move * 0.9
stop_spy = spy - move * 0.5 if is_call else spy + move * 0.5
target_price, _ = black_scholes(target_spy, K, max(0.0005, (dte - 1) / 365), r, iv, is_call)
stop_price, _ = black_scholes(stop_spy, K, max(0.0005, (dte - 1) / 365), r, iv, is_call)
win = (target_price - premium) * 100 * contracts
lose = (stop_price - premium) * 100 * contracts

g1, g2, g3 = st.columns(3)
g1.metric("Delta", fmt(delta, 3))
g2.metric("Historical Vol", f"{iv_pct}%")
g3.metric("السعر (Premium)", f"${fmt(premium)}")
w1, w2 = st.columns(2)
w1.metric("الربح عند الهدف", f"{'+' if win>=0 else ''}${fmt(win,0)}")
w2.metric("الخسارة عند الوقف", f"{'+' if lose>=0 else ''}${fmt(lose,0)}")

st.warning("⚠️ هذا تحليل احتمالي مبني على هندسة الموجة وتوافق المؤشرات وتمركز العقود المفتوحة — وليس تنبؤًا مضمونًا. الأسواق يمكن أن تُبطل أي سيناريو في أي لحظة. هذه أداة تحليل ومحاكاة وليست توصية استثمارية أو تنفيذ تداول فعلي، وأنا لست مستشارًا ماليًا مرخّصًا.")
st.markdown('</div>', unsafe_allow_html=True)

st.caption("المصدر: Yahoo Finance عبر yfinance (اتصال خادم مباشر). يحدّث تلقائيًا كل 60 ثانية.")
