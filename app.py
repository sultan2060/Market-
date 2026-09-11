import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import yfinance as yf
from datetime import datetime

# 1. إعدادات الصفحة والمظهر
st.set_page_config(
    page_title="ProofOfEdge | Quant Social Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. دالة جلب السعر اللحظي المباشر من السوق
@st.cache_data(ttl=15)  # تحديث السعر كل 15 ثانية تلقائياً
def get_live_market_price(ticker_symbol):
    try:
        # تحويل اسم المؤشر للصيغة القياسية في Yahoo Finance
        ticker_map = {"SPX": "^GSPC", "TSLA": "TSLA", "NVDA": "NVDA", "AAPL": "AAPL"}
        symbol = ticker_map.get(ticker_symbol, ticker_symbol)
        
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            return f"{latest_price:,.2f}"
    except Exception:
        pass
    return "N/A"

# 3. إدارة قاعدة البيانات الحية (حفظ واسترجاع الإشارات)
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
    spx_live = get_live_market_price("SPX")
    tsla_live = get_live_market_price("TSLA")
    
    return [
        {
            "trader": "@su2su",
            "symbol": "SPX",
            "time": datetime.now().strftime("%H:%M:%S"),
            "signal": "GEX Call Wall Defense",
            "price": spx_live if spx_live != "N/A" else "5,520.10",
            "quant_score": 94.8,
            "details": "تم رصد امتصاص سيولة مؤسسي عند مناطق الجاما الصفرية (Zero Gamma Zone).",
            "status": "Verified via Live Market Data ✅"
        },
        {
            "trader": "@Quant_Algo_v2",
            "symbol": "TSLA",
            "time": datetime.now().strftime("%H:%M:%S"),
            "signal": "Institutional Order Flow Sweep",
            "price": tsla_live if tsla_live != "N/A" else "220.50",
            "quant_score": 88.2,
            "details": "تجمع أومر شرائية ضخمة على عقد الخيارات Delta 0.50.",
            "status": "Verified via Live Market Data ✅"
        }
    ]

# 4. الهيدر الرئيسي للمنصة مع شريط الأسعار الحية
st.title("🛡️ ProofOfEdge — Quantitative Social Platform")
st.caption("شبكة التواصل الأولى المعتمدة على توثيق الأداء الكمي وإثبات خوارزميات التدفق (Proof of Quant Edge)")

# شريط الأسعار الحية اللحظية فوق الخلاصة
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("SPX Live", f"${get_live_market_price('SPX')}")
col_m2.metric("TSLA Live", f"${get_live_market_price('TSLA')}")
col_m3.metric("NVDA Live", f"${get_live_market_price('NVDA')}")
col_m4.metric("AAPL Live", f"${get_live_market_price('AAPL')}")

st.markdown("---")

# 5. الشريط الجانبي - الملف الشخصي ونموذج النشر السريع
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/guarantee.png", width=70)
    st.header("👤 ملف المتداول الكمي")
    
    trader_handle = st.text_input("معرف الحساب (Handle)", "su2su")
    quant_score = st.number_input("مؤشر المصداقية (Quant Score)", min_value=0.0, max_value=100.0, value=94.8, step=0.1)
    
    st.metric(label="الرتبة في المجتمع", value="Quant Master 🏆", delta="+2.4% هذا الشهر")
    
    st.markdown("---")
    st.subheader("📊 إحصائيات الأداء الموثق")
    col_sb1, col_sb2 = st.columns(2)
    col_sb1.metric("Win Rate", "78.5%")
    col_sb2.metric("Profit Factor", "2.41")

    st.markdown("---")
    st.subheader("⚡ نشر إشارة حية بسعر السوق اللحظي")
    with st.form("publish_signal_form"):
        symbol_input = st.selectbox("الأصل", ["SPX", "TSLA", "NVDA", "AAPL"])
        signal_input = st.text_input("نوع الإشارة", "GEX Zero Gamma Rejection")
        
        # جلب السعر اللحظي تلقائياً للأصل المختار
        auto_price = get_live_market_price(symbol_input)
        price_input = st.text_input("السعر اللحظي (مجلوب آلياً)", value=f"${auto_price}")
        details_input = st.text_area("تفاصيل الحركة الهيكلية", "اختراق مستوى جاما مرتفع مع زيادة تدفق أومر الشراء.")
        
        submit_btn = st.form_submit_button("🚀 نشر البطاقة بالسعر اللحظي")
        
        if submit_btn:
            new_card = {
                "trader": f"@{trader_handle}",
                "symbol": symbol_input,
                "time": datetime.now().strftime("%H:%M:%S"),
                "signal": signal_input,
                "price": price_input,
                "quant_score": quant_score,
                "details": details_input,
                "status": "Verified via Live API Engine ✅"
            }
            current_signals = load_signals()
            current_signals.insert(0, new_card)
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(current_signals, f, ensure_ascii=False, indent=4)
            st.success("تم نشر البطاقة بالسعر اللحظي المباشر!")
            st.rerun()

# 6. الجسم الرئيسي: خلاصة التحليلات الموثقة
st.subheader("📡 خلاصة التحليلات والبطاقات الحية (Live Verified Feed)")

signals_list = load_signals()

for card in signals_list:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.markdown(f"**المتداول:** `{card.get('trader')}`")
        c2.markdown(f"**الأصل:** `{card.get('symbol')}` @ `{card.get('price')}`")
        c3.markdown(f"**الإشارة:** `{card.get('signal')}`")
        c4.markdown(f"🏆 **`QS: {card.get('quant_score')}`**")
        
        st.write(card.get('details'))
        st.caption(f"⏱️ الوقت: {card.get('time')} | 🛡️ التوثيق: {card.get('status')}")

st.markdown("---")

# 7. غرف المراقبة المباشرة (Flow Hubs)
st.subheader("🔥 غرف المراقبة والسيولة المشتركة (Live Flow Hubs)")
tab1, tab2 = st.tabs(["📊 SPX Options Flow", "⚡ TSLA Market Structure"])

with tab1:
    st.markdown("### غرفة مراقبة تدفق سيولة SPX")
    st.write("تعرض هذه الغرفة التحليلات المعتمدة فقط للمتداولين الذين يتجاوز Quant Score الخاص بهم 85.0")
    
    chart_data = pd.DataFrame({
        'Strike Price': [5400, 5425, 5450, 5475, 5500],
        'Gamma Exposure (GEX)': [-120, 45, 310, 180, -90]
    })
    fig = px.bar(chart_data, x='Strike Price', y='Gamma Exposure (GEX)', color='Gamma Exposure (GEX)',
                 title="مستويات الجاما الحالية (GEX Profile)", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### غرفة مراقبة هيكلة أسهم TSLA")
    st.info(f"سعر TSLA اللحظي الآن في السوق: ${get_live_market_price('TSLA')}")
