# ====================== الصياد | Hunter Signals ======================
# ملف واحد كامل - محدث

import streamlit as st
import finnhub
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time

# ====================== إعداد الصفحة ======================
st.set_page_config(
    page_title="الصياد | Hunter Signals",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .signal-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #0f1419 100%);
        border-radius: 16px;
        padding: 28px;
        border: 1px solid #2a3142;
        margin-bottom: 20px;
    }
    .call { border-left: 7px solid #00e676; }
    .put  { border-left: 7px solid #ff1744; }
    .big-number { font-size: 2.1rem; font-weight: 700; color: #ffffff; }
    .target { font-size: 1.25rem; margin: 8px 0; }
    .strength-strong { color: #00e676; font-weight: 700; }
    .strength-medium { color: #ffc107; font-weight: 700; }
    .strength-weak { color: #90a4ae; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ====================== تسجيل الدخول ======================
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None

    if not st.session_state.logged_in:
        st.title("🎯 الصياد - Hunter Signals")
        st.markdown("### تسجيل الدخول")
        col1, col2 = st.columns([1, 2])
        with col1:
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            if st.button("دخول", use_container_width=True):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.role = "admin"
                    st.rerun()
                elif username == "user" and password == "user123":
                    st.session_state.logged_in = True
                    st.session_state.role = "user"
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة")
        st.stop()

check_login()

# ====================== Finnhub ======================
@st.cache_resource
def get_client():
    # للتجربة المحلية ضع مفتاحك هنا
    # أو استخدم Secrets في Streamlit Cloud
    api_key = st.secrets.get("FINNHUB_API_KEY", "d9nn90pr01qvumgb2vg0d9nn90pr01qvumgb2vgg")
    return finnhub.Client(api_key=api_key)

client = get_client()

# ====================== الرموز والفريمات ======================
SYMBOLS = {
    "Tesla": "TSLA",
    "Apple": "AAPL",
    "NVIDIA": "NVDA",
    "SPAC - IPO": "IPO",
    "SPAC - SPCX": "SPCX",
}

TIMEFRAMES = {
    "1 دقيقة (لحظي)": "1",
    "5 دقائق": "5",
    "15 دقيقة": "15",
    "ساعة": "60",
    "4 ساعات": "240",
    "يومي": "D"
}

# ====================== دوال التحليل ======================
def get_quote(symbol):
    try:
        return client.quote(symbol)
    except Exception as e:
        st.error(f"خطأ في السعر: {e}")
        return None

def get_candles(symbol, resolution="5", days=5):
    try:
        end = int(time.time())
        start = end - days * 86400
        data = client.stock_candles(symbol, resolution, start, end)
        if data.get("s") != "ok":
            return None
        df = pd.DataFrame({
            "t": data["t"], "o": data["o"], "h": data["h"],
            "l": data["l"], "c": data["c"], "v": data["v"]
        })
        df["datetime"] = pd.to_datetime(df["t"], unit="s")
        return df
    except Exception as e:
        st.error(f"خطأ في الشموع: {e}")
        return None

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def generate_signal(df, quote, resolution):
    if df is None or len(df) < 30 or quote is None:
        return None

    df = df.copy()
    df["ma_fast"] = df["c"].rolling(9).mean()
    df["ma_slow"] = df["c"].rolling(21).mean()
    df["rsi"] = calc_rsi(df["c"])

    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = quote["c"]
    atr = (df["h"] - df["l"]).rolling(14).mean().iloc[-1]
    momentum = df["c"].pct_change(5).iloc[-1] * 100

    signal = None
    strength = None
    reason = []

    # CALL
    if last["rsi"] < 28 and last["ma_fast"] > last["ma_slow"] and prev["ma_fast"] <= prev["ma_slow"] and momentum > 0.3:
        signal, strength = "CALL", "قوي"
        reason.append("RSI تشبع قوي + تقاطع صاعد + زخم إيجابي")
    elif last["rsi"] < 35 and last["ma_fast"] > last["ma_slow"] and prev["ma_fast"] <= prev["ma_slow"]:
        signal, strength = "CALL", "متوسط"
        reason.append("RSI تشبع + تقاطع صاعد")
    elif last["rsi"] < 40:
        signal, strength = "CALL", "ضعيف"
        reason.append("RSI منخفض فقط")

    # PUT
    elif last["rsi"] > 72 and last["ma_fast"] < last["ma_slow"] and prev["ma_fast"] >= prev["ma_slow"] and momentum < -0.3:
        signal, strength = "PUT", "قوي"
        reason.append("RSI تشبع قوي + تقاطع هابط + زخم سلبي")
    elif last["rsi"] > 65 and last["ma_fast"] < last["ma_slow"] and prev["ma_fast"] >= prev["ma_slow"]:
        signal, strength = "PUT", "متوسط"
        reason.append("RSI تشبع + تقاطع هابط")
    elif last["rsi"] > 60:
        signal, strength = "PUT", "ضعيف"
        reason.append("RSI مرتفع فقط")

    if not signal:
        return None

    # الأهداف
    if signal == "CALL":
        tp1 = price + atr * 0.7
        tp2 = price + atr * 1.4
        tp3 = price + atr * 2.6
    else:
        tp1 = price - atr * 0.7
        tp2 = price - atr * 1.4
        tp3 = price - atr * 2.6

    # تقدير الوقت
    res_minutes = {"1": 1, "5": 5, "15": 15, "60": 60, "240": 240, "D": 1440}.get(resolution, 5)
    recent_speed = df["c"].diff().abs().tail(10).mean()
    if recent_speed == 0:
        recent_speed = atr / 10

    if strength == "قوي":
        mult = [1.0, 4.5, 18]
    elif strength == "متوسط":
        mult = [2.0, 8, 35]
    else:
        mult = [3.5, 14, 60]

    eta1 = max(5, int((abs(tp1 - price) / recent_speed) * res_minutes * mult[0] / 5))
    eta2 = max(15, int((abs(tp2 - price) / recent_speed) * res_minutes * mult[1] / 5))
    eta3 = max(60, int((abs(tp3 - price) / recent_speed) * res_minutes * mult[2] / 5))

    def format_eta(minutes):
        if minutes < 60:
            return f"{minutes} دقيقة"
        elif minutes < 1440:
            h = minutes // 60
            m = minutes % 60
            return f"{h} ساعة" + (f" و {m} د" if m else "")
        else:
            return f"{minutes // 1440} يوم"

    return {
        "signal": signal,
        "strength": strength,
        "entry": price,
        "tp1": tp1, "tp2": tp2, "tp3": tp3,
        "eta1": format_eta(eta1),
        "eta2": format_eta(eta2),
        "eta3": format_eta(eta3),
        "rsi": round(last["rsi"], 1),
        "reason": " | ".join(reason),
        "atr": round(atr, 2)
    }

# ====================== الواجهة ======================
st.sidebar.title("🎯 الصياد")
st.sidebar.markdown(f"**الدور:** `{st.session_state.role}`")

symbol_name = st.sidebar.selectbox("السهم / SPAC", list(SYMBOLS.keys()))
symbol = SYMBOLS[symbol_name]

tf_name = st.sidebar.selectbox("الفريم الزمني", list(TIMEFRAMES.keys()))
resolution = TIMEFRAMES[tf_name]

auto_refresh = st.sidebar.checkbox("تحديث تلقائي كل 30 ثانية", True)
if st.sidebar.button("تحديث الآن"):
    st.rerun()

if st.sidebar.button("تسجيل خروج"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

quote = get_quote(symbol)
days = 3 if resolution in ["1", "5", "15"] else 10
df = get_candles(symbol, resolution, days=days)
signal_data = generate_signal(df, quote, resolution)

# ====================== شاشة المستخدم ======================
if st.session_state.role == "user":
    st.title(f"🎯 {symbol_name}")
    st.caption(f"الفريم: {tf_name}")

    if signal_data is None:
        st.info("لا توجد إشارة واضحة حالياً. انتظر انعكاس أقوى.")
    else:
        direction = signal_data["signal"]
        strength = signal_data["strength"]
        color_class = "call" if direction == "CALL" else "put"
        emoji = "🟢 CALL" if direction == "CALL" else "🔴 PUT"
        strength_class = {"قوي": "strength-strong", "متوسط": "strength-medium", "ضعيف": "strength-weak"}[strength]

        st.markdown(f"""
        <div class="signal-card {color_class}">
            <h2>{emoji} <span class="{strength_class}">• {strength}</span></h2>
            <p class="big-number">الدخول عند: {signal_data['entry']:.2f}</p>
            <hr style="border-color:#2a3142">
            <p class="target">🎯 الهدف 1: <b>{signal_data['tp1']:.2f}</b> &nbsp;&nbsp; ⏱ {signal_data['eta1']}</p>
            <p class="target">🎯 الهدف 2: <b>{signal_data['tp2']:.2f}</b> &nbsp;&nbsp; ⏱ {signal_data['eta2']}</p>
            <p class="target">🎯 الهدف 3: <b>{signal_data['tp3']:.2f}</b> &nbsp;&nbsp; ⏱ {signal_data['eta3']}</p>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

# ====================== شاشة المدير ======================
else:
    st.title(f"🛠️ لوحة المدير | {symbol_name} ({symbol})")
    st.caption(f"الفريم: {tf_name}")

    if quote:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("السعر", f"{quote['c']:.2f}", f"{quote['dp']:.2f}%")
        c2.metric("أعلى", f"{quote['h']:.2f}")
        c3.metric("أدنى", f"{quote['l']:.2f}")
        c4.metric("إغلاق سابق", f"{quote['pc']:.2f}")

    if signal_data:
        st.success(f"**{signal_data['signal']} {signal_data['strength']}** | {signal_data['reason']}")
        st.write(f"RSI: {signal_data['rsi']} | ATR: {signal_data['atr']}")
        t1, t2, t3 = st.columns(3)
        t1.metric("هدف 1", f"{signal_data['tp1']:.2f}", signal_data['eta1'])
        t2.metric("هدف 2", f"{signal_data['tp2']:.2f}", signal_data['eta2'])
        t3.metric("هدف 3", f"{signal_data['tp3']:.2f}", signal_data['eta3'])
    else:
        st.warning("لا توجد إشارة حالياً")

    if df is not None and len(df) > 20:
        df["ma9"] = df["c"].rolling(9).mean()
        df["ma21"] = df["c"].rolling(21).mean()
        df["rsi"] = calc_rsi(df["c"])

        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df["datetime"], open=df["o"], high=df["h"], low=df["l"], close=df["c"], name="السعر"))
        fig.add_trace(go.Scatter(x=df["datetime"], y=df["ma9"], name="MA9", line=dict(color="orange", width=1.5)))
        fig.add_trace(go.Scatter(x=df["datetime"], y=df["ma21"], name="MA21", line=dict(color="#42a5f5", width=1.5)))
        fig.update_layout(title="الشموع + المتوسطات", xaxis_rangeslider_visible=False, height=480, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df["datetime"], y=df["rsi"], name="RSI", line=dict(color="#ab47bc")))
        fig2.add_hline(y=70, line_dash="dash", line_color="#ff1744")
        fig2.add_hline(y=30, line_dash="dash", line_color="#00e676")
        fig2.update_layout(title="RSI", height=240, template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

# تحديث تلقائي
if auto_refresh:
    time.sleep(30)
    st.rerun()
