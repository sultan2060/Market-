import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import yfinance as yf
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="ProofOfEdge | Live Quant Feed",
    page_icon="🛡️",
    layout="wide"
)

# 2. دالة جلب السعر المباشر من السوق
@st.cache_data(ttl=15)
def get_live_market_price(ticker_symbol):
    try:
        ticker_map = {"SPX": "^GSPC", "SPY": "SPY", "TSLA": "TSLA", "NVDA": "NVDA"}
        symbol = ticker_map.get(ticker_symbol, ticker_symbol)
        data = yf.Ticker(symbol).history(period="1d", interval="1m")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
    except Exception:
        pass
    return 0.0

DATA_FILE = "live_signals.json"

def load_signals():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_signal(signal_data):
    signals = load_signals()
    signals.insert(0, signal_data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(signals, f, ensure_ascii=False, indent=4)

# 3. واجهة العرض الرئيسية
st.title("🛡️ ProofOfEdge — خلاصة الرصد الكمي الموثق")
st.caption("نظام توثيق الإشارات الحية المربوط بمحركات التداول والـ Webhook")

# عرض شريط الأسعار الحية
c1, c2, c3 = st.columns(3)
spx_price = get_live_market_price("SPX")
c1.metric("مؤشر SPX المباشر", f"${spx_price}")
c2.metric("سهم TSLA المباشر", f"${get_live_market_price('TSLA')}")
c3.metric("سهم NVDA المباشر", f"${get_live_market_price('NVDA')}")

st.markdown("---")

# 4. الشريط الجانبي - نظام التوثيق المشروط
with st.sidebar:
    st.header("⚡ إرسال إشارة للتوثيق")
    st.warning("⚠️ الإشارات المقبولة هي الصادرة آلياً عبر Webhook من TradingView أو المزودة بكود توثيق المؤشر.")
    
    trader_handle = st.text_input("معرف المتداول", "QuantBot_v1")
    
    # كود التحقق الخاص بالمؤشر (إثبات أن التنبيه صادر من خوارزمية)
    verification_code = st.text_input("رمز توثيق الخوارزمية (Webhook Secret Key)", type="password")
    
    symbol = st.selectbox("الأصل", ["SPX", "TSLA", "NVDA"])
    signal_type = st.selectbox("نوع الإشارة", ["GEX Zero Gamma Rejection", "Call Wall Resistance", "Put Wall Support"])
    direction = st.selectbox("الاتجاه", ["Call / Bullish 🟢", "Put / Bearish 🔴"])
    
    live_p = get_live_market_price(symbol)
    st.info(f"سعر التنفيذ اللحظي: **${live_p}**")
    
    if st.button("🚀 معالجة ونشر الإشارة"):
        # التحقق هل التنبيه صادر من مصدر موثق أم إدخال يدوي
        is_verified = (verification_code == "QUANT_SECRET_2026") # استبدل المفتاح بمفتاك الخاص
        
        new_signal = {
            "trader": f"@{trader_handle}",
            "symbol": symbol,
            "entry_price": live_p,
            "signal_type": signal_type,
            "direction": direction,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "verified": is_verified,
            "status_text": "إشارة آلية موثقة عبر Webhook ✅" if is_verified else "توقع يدوي (غير موثق من مؤشر) ⚠️"
        }
        
        save_signal(new_signal)
        if is_verified:
            st.success("تم التوثيق بالنظام الآلي بنجاح!")
        else:
            st.error("تم النشر كـ (توقع غير موثق) لعدم توفر مفتاح الخوارزمية.")
        st.rerun()

# 5. عرض البطاقات مع تمييز الإشارة الموثقة عن التوقع
st.subheader("📡 الخلاصة الحية (Live Feed)")

signals = load_signals()

if not signals:
    st.info("لا توجد إشارات مسجلة حالياً.")
else:
    for sig in signals:
        # تغيير لون وشكل البطاقة بناءً على التوثيق البرمجي
        card_border = "green" if sig.get("verified") else "red"
        
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2, 2, 2])
            
            col_a.markdown(f"**المتداول:** `{sig.get('trader')}`")
            col_b.markdown(f"**الأصل:** `{sig.get('symbol')}` @ **${sig.get('entry_price')}**")
            col_c.markdown(f"**الاتجاه:** {sig.get('direction')}")
            
            st.markdown(f"🎯 **نوع الإشارة:** `{sig.get('signal_type')}`")
            
            # الشارة الفاصلة بين التوثيق والتوقع
            if sig.get("verified"):
                st.success(f"🛡️ حالة التوثيق: {sig.get('status_text')} | {sig.get('time')}")
            else:
                st.error(f"❌ حالة التوثيق: {sig.get('status_text')} | {sig.get('time')}")
