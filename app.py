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

DATA_FILE = "live_signals.json"
PROFILES_FILE = "trader_profiles.json"

# 2. دوال إدارة البيانات والأرشيف
def load_json(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_val
    return default_val

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_signals():
    return load_json(DATA_FILE, [])

def save_signal(signal_data):
    signals = load_signals()
    signals.insert(0, signal_data)
    save_json(DATA_FILE, signals)

def load_profiles():
    return load_json(PROFILES_FILE, {})

def save_profile(handle, bio, strategy, secret_key):
    profiles = load_profiles()
    profiles[handle] = {
        "bio": bio,
        "strategy": strategy,
        "secret_key": secret_key
    }
    save_json(PROFILES_FILE, profiles)

# دالة جلب السعر المباشر من السوق
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

# 3. واجهة العرض الرئيسية
st.title("🛡️ ProofOfEdge — خلاصة الرصد الكمي الموثق")
st.caption("منصة مستقلة لتوثيق الأداء الكمي، القضاء على العشوائية، وبناء السجل التاريخي الحقيقي للمحللين.")

# عرض شريط الأسعار الحية
c1, c2, c3 = st.columns(3)
spx_price = get_live_market_price("SPX")
c1.metric("مؤشر SPX المباشر", f"${spx_price}")
c2.metric("سهم TSLA المباشر", f"${get_live_market_price('TSLA')}")
c3.metric("سهم NVDA المباشر", f"${get_live_market_price('NVDA')}")

st.markdown("---")

# 4. الشريط الجانبي - إدارة الحسابات وإرسال الإشارات
with st.sidebar:
    st.header("⚙️ لوحة تحكم المحلل")
    
    tab_type = st.radio("اختر العملية:", ["إرسال إشارة للتوثيق", "تسجيل / تحديث بروفايل محلل"])
    
    profiles = load_profiles()
    
    if tab_type == "تسجيل / تحديث بروفايل محلل":
        st.subheader("👤 التسجيل الشخصي للمحلل")
        new_handle = st.text_input("معرفك الفريد (مثال: AbuSaeed_Quant)").strip()
        bio_text = st.text_area("نبذة تعريفية عنك أو موقعك")
        strategy_desc = st.text_area("شرح الاستراتيجية (مثل: رصد الـ Call Walls والـ GEX)")
        custom_secret = st.text_input("مفتاحك السري الخاص (Secret Key)", type="password")
        
        if st.button("💾 حفظ البروفايل وإنشاء الهوية"):
            if new_handle and custom_secret:
                save_profile(new_handle, bio_text, strategy_desc, custom_secret)
                st.success(f"تم حفظ بروفايل المحلل @{new_handle} بنجاح!")
                st.rerun()
            else:
                st.error("الرجاء إدخال المعرف والمفتاح السري على الأقل.")
    
    else:
        st.header("⚡ إرسال إشارة للتوثيق")
        st.warning("⚠️ يتم توثيق الإشارات لحظياً بناءً على سعر النظام وساعة السيرفر لمنع أي تلاعب.")
        
        # اختيار المعرف المسجل أو كتابته مباشرة
        registered_handles = list(profiles.keys()) if profiles else ["QuantBot_v1"]
        trader_handle = st.selectbox("معرف المتداول المسجل", registered_handles)
        
        verification_code = st.text_input("رمز توثيق الخوارزمية (Secret Key)", type="password")
        
        symbol = st.selectbox("الأصل", ["SPX", "TSLA", "NVDA"])
        signal_type = st.selectbox("نوع الإشارة", ["GEX Zero Gamma Rejection", "Call Wall Resistance", "Put Wall Support"])
        direction = st.selectbox("الاتجاه", ["Call / Bullish 🟢", "Put / Bearish 🔴"])
        
        live_p = get_live_market_price(symbol)
        st.info(f"سعر التنفيذ اللحظي الموثق: **${live_p}**")
        
        if st.button("🚀 معالجة ونشر الإشارة"):
            # التحقق من مفتاح المحلل المخزن في البروفايل أو المفتاح العام الافتراضي
            stored_profile = profiles.get(trader_handle, {})
            expected_secret = stored_profile.get("secret_key", "2222")
            
            is_verified = (verification_code == expected_secret) and (verification_code != "")
            
            new_signal = {
                "trader": f"@{trader_handle}",
                "symbol": symbol,
                "entry_price": live_p,
                "signal_type": signal_type,
                "direction": direction,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "verified": is_verified,
                "status_text": "إشارة آلية/موثقة عبر النظام ✅" if is_verified else "توقع يدوي (مفتاح غير مطابق) ⚠️"
            }
            
            save_signal(new_signal)
            if is_verified:
                st.success("تم توثيق ونشر الصفقة بنجاح في السجل التاريخي!")
            else:
                st.error("تم النشر، ولكن برمز غير مطابق للبروفايل المسجل.")
            st.rerun()

# 5. عرض البطاقات والبروفايلات في الواجهة الرئيسية
st.subheader("📡 الخلاصة الحية وسجل الأداء الموثق (Live Feed)")

signals = load_signals()

if not signals:
    st.info("لا توجد إشارات مسجلة حتى الآن. كن أول من يوثق أدائه بالأرقام!")
else:
    for sig in signals:
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2, 2, 2])
            
            trader_name = sig.get('trader')
            col_a.markdown(f"**المتداول:** `{trader_name}`")
            col_b.markdown(f"**الأصل:** `{sig.get('symbol')}` @ **${sig.get('entry_price')}**")
            col_c.markdown(f"**الاتجاه:** {sig.get('direction')}")
            
            st.markdown(f"🎯 **نوع الإشارة:** `{sig.get('signal_type')}`")
            
            # عرض نبذة المحلل إذا كان مسجلاً
            profile_data = profiles.get(trader_name.replace("@", ""), {})
            if profile_data.get("strategy"):
                st.caption(f"💡 **استراتيجية المحلل:** {profile_data.get('strategy')}")
            
            # الشارة الفاصلة بين التوثيق والتوقع
            if sig.get("verified"):
                st.success(f"🛡️ حالة التوثيق: {sig.get('status_text')} | {sig.get('time')}")
            else:
                st.error(f"❌ حالة التوثيق: {sig.get('status_text')} | {sig.get('time')}")
