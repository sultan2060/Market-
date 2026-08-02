
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="لوحة التحليل الفني والخيارات", layout="wide")

st.title("📈 لوحة المتابعة المتقدمة - إشارات وتحديد الموجات")
st.write(f"آخر تحديث للبيانات: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 1. شريط الأسهم الرئيسي
st.subheader("🎯 الأسهم والمؤشرات الرئيسية")
main_cols = st.columns(4)

main_tickers = {
    "SPX": "^GSPC",
    "Tesla": "TSLA",
    "QQQ": "QQQ",
    "Apple": "AAPL"
}

# قائمة أسهم إضافية في القائمة المنسدلة
extra_tickers = {
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Microsoft": "MSFT",
    "Meta": "META",
    "AMD": "AMD"
}

# اختيار السهم المراد تحليله
selected_ticker = None

# أزرار سريعة للأسهم الرئيسية
col_idx = 0
for name, symbol in main_tickers.items():
    with main_cols[col_idx]:
        if st.button(f"📊 {name} ({symbol})", key=symbol, use_container_width=True):
            st.session_state['selected_symbol'] = symbol
    col_idx += 1

# القائمة المنسدلة لبقية الأسهم
st.sidebar.title("⚙️ إعدادات التحليل")
dropdown_choice = st.sidebar.selectbox(
    "أو اختر سهم إضافي من القائمة:",
    ["-- اختر سهم --"] + list(extra_tickers.keys())
)

if dropdown_choice != "-- اختر سهم --":
    st.session_state['selected_symbol'] = extra_tickers[dropdown_choice]

# التعيين الافتراضي إذا لم يتم الاختيار
if 'selected_symbol' not in st.session_state:
    st.session_state['selected_symbol'] = "^GSPC"

active_symbol = st.session_state['selected_symbol']

# 2. إعدادات الفريمات الزمنية
timeframe = st.sidebar.selectbox(
    "اختر الفريم الزمني:",
    [
        "1 دقيقة (لحظي)", 
        "5 دقائق", 
        "15 دقيقة", 
        "1 ساعة", 
        "يومي", 
        "أسبوعي", 
        "شهري"
    ]
)

# تعيين معلمات البيانات بحسب الفريم
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

# 3. جلب البيانات
@st.cache_data(ttl=15)
def get_stock_data(symbol, period, interval):
    data = yf.Ticker(symbol).history(period=period, interval=interval)
    return data

df = get_stock_data(active_symbol, period_val, interval_val)

if not df.empty and len(df) > 20:
    # 4. حساب المؤشرات الفنية وإشارات Call / Put والتقاط الموجة
    # المتوسطات المتحركة EMA 9 & 21
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # تحديد مناطق التقاط الموجة (Pivot Points)
    df['Pivot_Low'] = df['Low'][(df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))]
    df['Pivot_High'] = df['High'][(df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))]

    last_close = df['Close'].iloc[-1]
    last_ema9 = df['EMA9'].iloc[-1]
    last_ema21 = df['EMA21'].iloc[-1]
    prev_ema9 = df['EMA9'].iloc[-2]
    prev_ema21 = df['EMA21'].iloc[-2]

    # إشارة الدخول (Call / Put)
    signal = "محايد ⚪"
    signal_color = "gray"
    
    if prev_ema9 <= prev_ema21 and last_ema9 > last_ema21:
        signal = "إشارة شراء / CALL 🟢"
        signal_color = "green"
    elif prev_ema9 >= prev_ema21 and last_ema9 < last_ema21:
        signal = "إشارة بيع / PUT 🔴"
        signal_color = "red"
    elif last_ema9 > last_ema21:
        signal = "مسار صاعد (اتجاه CALL) 🟢"
        signal_color = "green"
    else:
        signal = "مسار هابط (اتجاه PUT) 🔴"
        signal_color = "red"

    # عرض معلومات السهم والتوصية اللحظية
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"السعر الحالي ({active_symbol})", f"${last_close:.2f}")
    c2.markdown(f"### الإشارة الحالية:\n **:{signal_color}[{signal}]**")
    
    # تحديد أقرب منطقة التقاط موجة
    recent_pivots_low = df['Pivot_Low'].dropna()
    recent_pivots_high = df['Pivot_High'].dropna()
    
    support_wave = recent_pivots_low.iloc[-1] if not recent_pivots_low.empty else df['Low'].min()
    resistance_wave = recent_pivots_high.iloc[-1] if not recent_pivots_high.empty else df['High'].max()
    
    c3.metric("منطقة التقاط الموجة (دعم)", f"${support_wave:.2f}")

    # 5. الرسم البياني الشامل
    fig = go.Figure()

    # الشموع اليابانية
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="السعر"
    ))

    # متوسطات EMA
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], line=dict(color='cyan', width=1.5), name="EMA 9"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], line=dict(color='orange', width=1.5), name="EMA 21"))

    # نقاط التقاط الموجات على الرسم
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Pivot_Low'], mode='markers',
        marker=dict(symbol='triangle-up', size=12, color='lime'), name='قاع موجة (التقاط CALL)'
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Pivot_High'], mode='markers',
        marker=dict(symbol='triangle-down', size=12, color='magenta'), name='قمة موجة (التقاط PUT)'
    ))

    fig.update_layout(
        title=f"رسم بياني تفاعلي - {active_symbol} | فريم {timeframe}",
        template="plotly_dark",
        height=600,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ جاري تحميل البيانات أو أن السوق مغلق في الوقت الحالي لهذا الفريم.")



                                                                                                    

                                                                                                    .
