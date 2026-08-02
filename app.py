import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="WaveSniper - قناص الفرص اللحظية", layout="wide")

st.title("🎯 WaveSniper | قناص الفرص والموجات اللحظية")
st.write(f"آخر تحديث للبيانات: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# قائمة الأسهم
main_tickers = {
    "SPX": "^GSPC",
    "Tesla": "TSLA",
    "QQQ": "QQQ",
    "Apple": "AAPL"
}

extra_tickers = {
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Microsoft": "MSFT",
    "Meta": "META",
    "AMD": "AMD"
}

st.sidebar.title("⚙️ الإعدادات والتحليل")

# اختيار السهم
st.subheader("📌 الأسهم والمؤشرات الرئيسية")
cols = st.columns(4)

if 'selected_symbol' not in st.session_state:
    st.session_state['selected_symbol'] = "^GSPC"

idx = 0
for name, sym in main_tickers.items():
    with cols[idx]:
        if st.button(f"📊 {name}", key=sym, use_container_width=True):
            st.session_state['selected_symbol'] = sym
    idx += 1

dropdown_choice = st.sidebar.selectbox(
    "أو اختر سهم آخر من القائمة:",
    ["-- اختر سهم --"] + list(extra_tickers.keys())
)

if dropdown_choice != "-- اختر سهم --":
    st.session_state['selected_symbol'] = extra_tickers[dropdown_choice]

active_symbol = st.session_state['selected_symbol']

# اختيار الفريم
timeframe = st.sidebar.selectbox(
    "اختر الفريم الزمني:",
    ["1 دقيقة (لحظي)", "5 دقائق", "15 دقيقة", "1 ساعة", "يومي", "أسبوعي", "شهري"]
)

tf_map = {
    "1 دقيقة (لحظي)": ("1d", "1m"),
    "5 دقائق": ("5d", "5m"),
    "15 دقيقة": ("5d", "15m"),
    "1 ساعة": ("1mo", "60m"),
    "يومي": ("1y", "1d"),
    "أسبوعي": ("2y", "1wk"),
    "شهري": ("5y", "1mo")
}

period_val, interval_val = tf_map[timeframe]

# جلب البيانات
@st.cache_data(ttl=15)
def load_data(symbol, period, interval):
    return yf.Ticker(symbol).history(period=period, interval=interval)

df = load_data(active_symbol, period_val, interval_val)

if not df.empty and len(df) > 10:
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

    # نقاط الارتداد والموجات
    df['Pivot_Low'] = df['Low'][(df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))]
    df['Pivot_High'] = df['High'][(df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))]

    last_close = df['Close'].iloc[-1]
    last_ema9 = df['EMA9'].iloc[-1]
    last_ema21 = df['EMA21'].iloc[-1]

    if last_ema9 > last_ema21:
        signal_text = "إشارة صعود / CALL 🟢"
    else:
        signal_text = "إشارة هبوط / PUT 🔴"

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("السعر الحالي", f"${last_close:.2f}")
    m2.metric("السهم النشط", active_symbol)
    m3.metric("إشارة الاتجاه اللحظية", signal_text)

    # الرسم البياني
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="السعر"
    ))

    fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], line=dict(color='cyan', width=1.5), name="EMA 9"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], line=dict(color='orange', width=1.5), name="EMA 21"))

    fig.add_trace(go.Scatter(
        x=df.index, y=df['Pivot_Low'], mode='markers',
        marker=dict(symbol='triangle-up', size=12, color='lime'), name='التقاط قاع (CALL)'
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Pivot_High'], mode='markers',
        marker=dict(symbol='triangle-down', size=12, color='magenta'), name='التقاط قمة (PUT)'
    ))

    fig.update_layout(
        title=f"تحليل {active_symbol} | فريم {timeframe}",
        template="plotly_dark",
        height=600,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⚠️ جاري جلب البيانات أو أن السوق مغلق حالياً لهذا الفريم.")

