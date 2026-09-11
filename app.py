import streamlit as st
import pandas as pd
import json
import os
import yfinance as yf
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="ProofOfEdge | Quant Strategy Testing & Proof",
    page_icon="🛡️",
    layout="wide"
)

DATA_FILE = "live_signals.json"
PROFILES_FILE = "trader_profiles.json"

# 2. دوال إدارة الملفات والبيانات بأمان
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

# دالة جلب السعر المباشر للأصول
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

# 3. واجهة المنصة الرئيسية
st.title("🛡️ ProofOfEdge — خلاصة الرصد الكمي واختبار الاستراتيجيات")
st.caption("منصة موثقة رقمياً لقياس أداء الاستراتيجيات، القضاء على العشوائية، وبناء السجل التاريخي الحقيقي للمحلل.")

# شريط الأسعار الحية في الأعلى
c1, c2, c3 = st.columns(3)
spx_price = get_live_market_price("SPX")
c1.metric("مؤشر SPX المباشر", f"${spx_price}")
c2.metric("سهم TSLA المباشر", f"${get_live_market_price('TSLA')}")
c3.metric("سهم NVDA المباشر", f"${get_live_market_price('NVDA')}")

st.markdown("---")

# تحميل البروفايلات المسجلة
profiles = load_profiles()

# 4. الشريط الجانبي (لوحة التحكم والإدارة)
with st.sidebar:
    st.header("⚙️ لوحة التحكم")
    
    action_mode = st.radio("اختر العملية:", ["توثيق واختبار إشارة", "تسجيل / تحديث بروفايل محلل"])
    
    if action_mode == "تسجيل / تحديث بروفايل محلل":
        st.subheader("👤 هوية المحلل واستراتيجيته")
        
        # حقول إدخال نظيفة ومباشرة لضمان الاستقرار
        new_handle = st.text_input("معرفك الفريد (مثال: AbuSaeed_Quant)").strip()
        bio_text = st.text_area("نبذة تعريفية عنك")
        strategy_desc = st.text_area("شرح الاستراتيجية الكمية (مثل: GEX Zero Gamma & Call Walls)")
        custom_secret = st.text_input("مفتاحك السري الخاص (Secret Key)", type="password")
        
        if st.button("💾 حفظ البروفايل وإنشاء الهوية"):
            if new_handle and custom_secret:
                save_profile(new_handle, bio_text, strategy_desc, custom_secret)
                st.success(f"✅ تم حفظ البروفايل للمحلل @{new_handle} بنجاح!")
            else:
                st.error("❌ الرجاء إدخال المعرف والمفتاح السري على الأقل.")
    
    else:
        st.subheader("⚡ توثيق إشارة / اختبار استراتيجية")
        st.warning("⚠️ يتم توثيق السعر ووقت النظام لحظياً لمنع أي تلاعب أو تعديل بأثر رجعي.")
        
        registered_handles = list(profiles.keys()) if profiles else ["QuantBot_v1"]
        trader_handle = st.selectbox("معرف المتداول المسجل", registered_handles)
        
        verification_code = st.text_input("رمز توثيق الخوارزمية (Secret Key)", type="password")
        
        symbol = st.selectbox("الأصل المالي", ["SPX", "TSLA", "NVDA"])
        signal_type = st.selectbox("نوع الإشارة / النموذج الكمي", ["GEX Zero Gamma Rejection", "Call Wall Resistance", "Put Wall Support"])
        direction = st.selectbox("الاتجاه", ["Call / Bullish 🟢", "Put / Bearish 🔴"])
        
        live_p = get_live_market_price(symbol)
        st.info(f"سعر التنفيذ اللحظي الموثق: **${live_p}**")
        
        if st.button("🚀 اعتماد وتوثيق الصفقة بالسجل"):
            stored_profile = profiles.get(trader_handle, {})
            expected_secret = stored_profile.get("secret_key", "2222")
            
            # التحقق من صحة المفتاح السري للخوارزمية أو البروفايل
            is_verified = (verification_code == expected_secret) and (verification_code != "")
            
            new_signal = {
                "trader": f"@{trader_handle}",
                "symbol": symbol,
                "entry_price": live_p,
                "signal_type": signal_type,
                "direction": direction,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "verified": is_verified,
                "status_text": "إشارة خوارزمية موثقة ✅" if is_verified else "اختبار يدوي مؤمن ⚠️"
            }
            
            save_signal(new_signal)
            if is_verified:
                st.success("✅ تم توثيق الاعتماد في السجل التاريخي بنجاح!")
            else:
                st.error("⚠️ تم التوثيق كـ (اختبار يدوي) لعدم مطابقة مفتاح الخوارزمية.")
            st.rerun()

# 5. الواجهة الرئيسية - الخلاصة الحية وسجل الأداء الموثق
st.subheader("📡 السجل التاريخي الحقيقي لاختبارات الأداء (Verified Track Record)")

signals = load_signals()

if not signals:
    st.info("لا توجد إشارات مسجلة حتى الآن. ابدأ بتوثيق أول اختبار استراتيجية لك بالأرقام!")
else:
    for sig in signals:
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2, 2, 2])
            
            trader_name = sig.get('trader')
            symbol = sig.get('symbol')
            entry_price = sig.get('entry_price')
            direction = sig.get('direction')
            
            col_a.markdown(f"**المتداول:** `{trader_name}`")
            col_b.markdown(f"**الأصل:** `{symbol}` @ سعر التنفيذ: **${entry_price}**")
            col_c.markdown(f"**الاتجاه:** {direction}")
            
            st.markdown(f"🎯 **النموذج / الإشارة:** `{sig.get('signal_type')}`")
            
            # مقارنة السعر اللحظي الحالي بسعر الدخول لتقييم حركة الأداء بموضوعية
            current_market_price = get_live_market_price(symbol)
            if entry_price > 0 and current_market_price > 0:
                price_diff = round(current_market_price - entry_price, 2)
                is_bullish = "Bullish" in direction or "🟢" in direction
                
                if is_bullish:
                    perf_eval = "📈 في مسار إيجابي (صاعد لصالح الاتجاه)" if price_diff > 0 else ("⏳ نقطة الحياد الحالية" if price_diff == 0 else "📉 في مسار سلبي (هابط عكس الاتجاه)")
                else:
                    perf_eval = "📈 في مسار إيجابي (هابط لصالح الاتجاه)" if price_diff < 0 else ("⏳ نقطة الحياد الحالية" if price_diff == 0 else "📉 في مسار سلبي (صاعد عكس الاتجاه)")
                
                st.markdown(f"📊 **السعر اللحظي الآن:** `${current_market_price}` | **الفارق الكمي:** `{price_diff:+.2f}$` | **الحالة:** **{perf_eval}**")
            
            # استدعاء وعرض نبذة واستراتيجية المحلل المرتبط بالبطاقة
            clean_handle = trader_name.replace("@", "").strip()
            profile_data = profiles.get(clean_handle, {})
            
            if profile_data.get("strategy"):
                st.info(f"💡 **استراتيجية المحلل ({clean_handle}):** {profile_data.get('strategy')}")
            if profile_data.get("bio"):
                st.caption(f"👤 **نبذة المحلل:** {profile_data.get('bio')}")
            
            # حالة التوثيق الرسمية
            if sig.get("verified"):
                st.success(f"🛡️ {sig.get('status_text')} | الوقت الموثق: {sig.get('time')}")
            else:
                st.warning(f"⚠️ {sig.get('status_text')} | الوقت الموثق: {sig.get('time')}")
