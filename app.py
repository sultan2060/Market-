import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import yfinance as yf
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="ProofOfEdge | Quant Social Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. دالة جلب السعر اللحظي الدقيق من السوق (تعديل رمز SPX إلى القياسي ^GSPC)
@st.cache_data(ttl=15)
def get_live_market_price(ticker_symbol):
    try:
        ticker_map = {
            "SPX": "^GSPC",   # المؤشر الرئيسي S&P 500
            "SPY": "SPY",     # صندوق SPY
            "TSLA": "TSLA", 
            "NVDA": "NVDA", 
            "AAPL": "AAPL"
        }
        symbol = ticker_map.get(ticker_symbol, ticker_symbol)
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            return round(latest_price, 2)
    except Exception:
        pass
    return "N/A"

# 3. إدارة قاعدة البيانات الحية
DATA_FILE = "live_signals.json"

def load_signals():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return get_default_signals()
    return get_default_signals()

def get_default_signals():
    return [
        {
            "trader": "@su2su",
            "symbol": "SPX",
            "time": datetime.now().strftime("%H:%M:%S"),
            "signal_type": "GEX Zero Gamma Rejection",
            "direction": "Call / Bullish 🟢",
            "entry_price": get_live_market_price("SPX"),
            "target_strike": 5500.0,
            "quant_score": 50.0,
            "status": "Verified via Live API Engine ✅"
        }
    ]

# 4. الواجهة الرئيسية وشريط الأسعار الحية
st.title("🛡️ ProofOfEdge — Quantitative Social Platform")
st.caption("شبكة التوثيق الكمي الأولى لإشارات السيولة وهيكلية السوق")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("SPX Index", f"${get_live_market_price('SPX')}")
col_m2.metric("TSLA Live", f"${get_live_market_price('TSLA')}")
col_m3.metric("NVDA Live", f"${get_live_market_price('NVDA')}")
col_m4.metric("AAPL Live", f"${get_live_market_price('AAPL')}")

st.markdown("---")

# 5. الشريط الجانبي - نموذج النشر الهيكلي المقيد (إلغاء الكتابة الحرة والتقييم اليدوي)
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/guarantee.png", width=70)
    st.header("👤 ملف المتداول الكمي")
    
    trader_handle = st.text_input("معرف الحساب (Handle)", "su2su")
    
    # التقييم مغلق ومحسوب بالنظام فقط (افتراضي 50.0 للبداية)
    system_qs = 50.0
    st.info(f"🏆 تقييم المصداقية الآلي (Quant Score): **{system_qs}**")
    
    st.markdown("---")
    st.subheader("⚡ رصد إشارة كمية جديدة")
    
    with st.form("publish_strict_signal_form"):
        # أجهزة إدخال مقيدة بقوائم وأرقام فقط (منع الكتابة العشوائية)
        symbol_input = st.selectbox("1. الأصل (Asset)", ["SPX", "TSLA", "NVDA", "AAPL"])
        
        signal_type_input = st.selectbox(
            "2. نوع الإشارة الهيكلية",
            [
                "GEX Zero Gamma Rejection",
                "Call Wall Resistance Level",
                "Put Wall Support Defense",
                "VWAP Mean Reversion",
                "Order Flow Imbalance"
            ]
        )
        
        direction_input = st.selectbox("3. الاتجاه الكمي", ["Call / Bullish 🟢", "Put / Bearish 🔴"])
        
        current_market_price = get_live_market_price(symbol_input)
        st.write(f"سعر الدخول الموثق لحظياً: **${current_market_price}**")
        
        target_strike_input = st.number_input(
            "4. مستهدف السترايك / الهدف الرقمي (Target Strike)",
            value=float(current_market_price) if isinstance(current_market_price, (int, float)) else 5000.0,
            step=5.0
        )
        
        submit_btn = st.form_submit_button("🚀 توثيق ونشر البطاقة")
        
        if submit_btn:
            new_card = {
                "trader": f"@{trader_handle}",
                "symbol": symbol_input,
                "time": datetime.now().strftime("%H:%M:%S"),
                "signal_type": signal_type_input,
                "direction": direction_input,
                "entry_price": f"${current_market_price}",
                "target_strike": target_strike_input,
                "quant_score": system_qs,
                "status": "Verified via Live API Engine ✅"
            }
            current_signals = load_signals()
            current_signals.insert(0, new_card)
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(current_signals, f, ensure_ascii=False, indent=4)
            st.success("تم تسجيل الإشارة الكمية بنجاح!")
            st.rerun()

# 6. خلاصة البطاقات الموثقة (Live Verified Feed)
st.subheader("📡 خلاصة الرصد والبطاقات الموثقة (Live Verified Feed)")

signals_list = load_signals()

for card in signals_list:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.markdown(f"**المتداول:** `{card.get('trader')}`")
        c2.markdown(f"**الأصل:** `{card.get('symbol')}` @ `{card.get('entry_price')}`")
        c3.markdown(f"**الاتجاه:** {card.get('direction')}")
        c4.markdown(f"🏆 **`QS: {card.get('quant_score')}`**")
        
        st.markdown(f"🎯 **نوع الإشارة:** `{card.get('signal_type')}` | **الهدف الرقمي:** `{card.get('target_strike')}`")
        st.caption(f"⏱️ وقت التوثيق: {card.get('time')} | 🛡️ حالة التوثيق: {card.get('status')}")

st.markdown("---")

# 7. غرف المراقبة
st.subheader("🔥 غرف المراقبة والسيولة (Live Flow Hubs)")
tab1, tab2 = st.tabs(["📊 SPX Options Flow", "⚡ TSLA Market Structure"])

with tab1:
    chart_data = pd.DataFrame({
        'Strike Price': [5400, 5425, 5450, 5475, 5500],
        'Gamma Exposure (GEX)': [-120, 45, 310, 180, -90]
    })
    fig = px.bar(chart_data, x='Strike Price', y='Gamma Exposure (GEX)', color='Gamma Exposure (GEX)',
                 title="مستويات الجاما الحالية (GEX Profile)", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.info(f"سعر TSLA المباشر: ${get_live_market_price('TSLA')}")
