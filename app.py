import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime

# 1. إعدادات الصفحة والمظهر
st.set_page_config(
    page_title="ProofOfEdge | Quant Social Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. إدارة قاعدة البيانات الحية (حفظ واسترجاع الإشارات)
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
            "time": "15:45:10",
            "signal": "GEX Call Wall Defense",
            "price": "5,450.25",
            "quant_score": 94.8,
            "details": "تم رصد امتصاص سيولة مؤسسي عند مناطق الجاما الصفرية (Zero Gamma Zone).",
            "status": "Verified via Python Engine ✅"
        },
        {
            "trader": "@Quant_Algo_v2",
            "symbol": "TSLA",
            "time": "15:30:00",
            "signal": "Institutional Order Flow Sweep",
            "price": "214.80",
            "quant_score": 88.2,
            "details": "تجمع أومر شرائية ضخمة على عقد الخيارات Delta 0.50.",
            "status": "Verified via PineScript Webhook ✅"
        }
    ]

# 3. الهيدر الرئيسي للمنصة
st.title("🛡️ ProofOfEdge — Quantitative Social Platform")
st.caption("شبكة التواصل الأولى المعتمدة على توثيق الأداء الكمي وإثبات خوارزميات التدفق (Proof of Quant Edge)")
st.markdown("---")

# 4. الشريط الجانبي - الملف الشخصي للمتداول su2su
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
    
    st.info("💡 يتم تحديث الـ Quant Score تلقائياً عبر نتائج التحليلات المربوطة بالـ API.")

# 5. الجسم الرئيسي: خلاصة التحليلات الموثقة بالتحديث الآلي
st.subheader("📡 خلاصة التحليلات والبطاقات الحية (Live Verified Feed)")

# تحديث آلي للواجهة لتنعكس الإشارات القادمة فوراً
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

# 6. غرف المراقبة المباشرة (Flow Hubs)
st.subheader("🔥 غرف المراقبة والسيولة المشتركة (Live Flow Hubs)")
tab1, tab2 = st.tabs(["📊 SPX Options Flow", "⚡ TSLA Market Structure"])

with tab1:
    st.markdown("### غرفة مراقبة تدفق سيولة SPX")
    st.write("تعرض هذه الغرفة التحليلات المعتمدة فقط للمتداولين الذين يتجاوز Quant Score الخاص بهم 85.0")
    
    # رسم بياني توضيحي لمستويات السيولة والجاما
    chart_data = pd.DataFrame({
        'Strike Price': [5400, 5425, 5450, 5475, 5500],
        'Gamma Exposure (GEX)': [-120, 45, 310, 180, -90]
    })
    fig = px.bar(chart_data, x='Strike Price', y='Gamma Exposure (GEX)', color='Gamma Exposure (GEX)',
                 title="مستويات الجاما الحالية (GEX Profile)", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### غرفة مراقبة هيكلة أسهم TSLA")
    st.info("غرفة المراقبة نشطة. يتم تحديث التنبيهات تلقائياً للمستخدم `@su2su` عبر السيرفر الرئيسي.")
