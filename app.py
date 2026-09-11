import streamlit as st
import pandas as pd
import json
import os
import yfinance as yf
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="ProofOfEdge | Quant Strategy & Numeric Targets",
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
st.title("🛡️ ProofOfEdge — منصة التوثيق الكمي بالأهداف السعرية الرقمية")
st.caption("نظام احترافي يعتمد على الأرقام، المستويات، وأسعار التنفيذ اللحظية بعيداً عن التسميات العشوائية.")

# شريط الأسعار الحية في الأعلى
c1, c2, c3 = st.columns(3)
spx_price = get_live_market_price("SPX")
c1.metric("مؤشر SPX المباشر", f"${spx_price}")
c2.metric("سهم TSLA المباشر", f"${get_live_market_price('TSLA')}")
c3.metric("سهم NVDA المباشر", f"${get_live_market_price('NVDA')}")

st.markdown("---")

# تحميل البروفايلات المسجلة
profiles = load_profiles()

# 4. الشريط الجانبي (لوحة التحكم التنفيذية)
with st.sidebar:
    st.header("⚙️ لوحة التحكم التنفيذية")
    
    action_mode = st.radio("اختر القسم:", ["إرسال استراتيجية / هدف رقمي جديد", "تسجيل أو تحديث بروفايل محلل"])
    
    if action_mode == "تسجيل أو تحديث بروفايل محلل":
        st.subheader("👤 ملف المحلل والاستراتيجية")
        
        new_handle = st.text_input("معرفك الفريد (مثال: AbuSaeed)").strip()
        bio_text = st.text_area("نبذة تعريفية عنك أو عن نشاطك")
        strategy_desc = st.text_area("تفاصيل الاستراتيجية الكمية (مثل: GEX & Call Walls مع شروط الرصد)")
        custom_secret = st.text_input("مفتاحك السري الخاص (Secret Key)", type="password")
        
        if st.button("💾 حفظ البروفايل واعتماد الهوية"):
            if new_handle and custom_secret:
                save_profile(new_handle, bio_text, strategy_desc, custom_secret)
                st.success(f"✅ تم حفظ بروفايل المحلل @{new_handle} بنجاح!")
            else:
                st.error("❌ الرجاء إدخال المعرف والمفتاح السري على الأقل.")
    
    else:
        st.subheader("⚡ توثيق هدف رقمي واستراتيجية")
        st.warning("⚠️ يتم توثيق السعر ووقت النظام لحظياً، ويتم استنتاج اتجاه الصفقة تلقائياً من الهدف الرقمي.")
        
        registered_handles = list(profiles.keys()) if profiles else ["محلل_عام"]
        trader_handle = st.selectbox("اختر اسم المحلل المسجل", registered_handles)
        
        verification_code = st.text_input("رمز توثيق المحلل (Secret Key)", type="password")
        
        symbol = st.selectbox("الأصل المالي", ["SPX", "TSLA", "NVDA"])
        signal_type = st.text_input("اسم النموذج أو الأداة (مثال: GEX Zero Gamma Rejection)")
        
        live_p = get_live_market_price(symbol)
        st.info(f"سعر التنفيذ اللحظي الموثق: **${live_p}**")
        
        # إدخال الهدف السعري الرقمي الصريح بدلاً من اختيار كول أو بوت
        target_price = st.number_input(
            "الهدف السعري الرقمي المستهدف (Target Price)", 
            value=float(live_p + 10.0) if live_p > 0 else 0.0,
            step=0.25,
            format="%.2f"
        )
        
        confirmation_notes = st.text_area("توقيت التأكيد وشروط الاستراتيجية", placeholder="مثال: تم إعطاء التأكيد فور ثبات السعر فوق مستوى السيولة مع حجم تداول عالٍ")
        
        if st.button("🚀 اعتماد ونشر الهدف بالسجل العام"):
            stored_profile = profiles.get(trader_handle, {})
            expected_secret = stored_profile.get("secret_key", "2222")
            
            is_verified = (verification_code == expected_secret) and (verification_code != "")
            
            # استنتاج الاتجاه برمجيًا بناءً على مقارنة الهدف بسعر الدخول
            if target_price > live_p:
                inferred_direction = "صاعد (Bullish Target) 🟢"
            elif target_price < live_p:
                inferred_direction = "هابط (Bearish Target) 🔴"
            else:
                inferred_direction = "حيادي (Neutral) ⚪"
            
            new_signal = {
                "trader": f"@{trader_handle}",
                "symbol": symbol,
                "entry_price": live_p,
                "signal_type": signal_type if signal_type else "هدف كمي معتمد",
                "target_price": target_price,
                "direction": inferred_direction,
                "confirmation_notes": confirmation_notes,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "verified": is_verified,
                "status_text": "هدف خوارزمي موثق ✅" if is_verified else "اختبار رقمي مؤمن ⚠️"
            }
            
            save_signal(new_signal)
            if is_verified:
                st.success("✅ تم توثيق الهدف الرقمي ونشره في السجل التاريخي بنجاح!")
            else:
                st.error("⚠️ تم النشر كـ (اختبار رقمي) لعدم مطابقة مفتاح الخوارزمية.")
            st.rerun()

# 5. الواجهة الرئيسية - قسم عرض البروفايلات وسجل الأداء الموثق
st.subheader("👥 دليل المحللين واستراتيجياتهم المسجلة")
if profiles:
    profile_cols = st.columns(min(len(profiles), 3))
    for idx, (hname, hdata) in enumerate(profiles.items()):
        col_idx = idx % 3
        with profile_cols[col_idx]:
            with st.container(border=True):
                st.markdown(f"### 👤 @{hname}")
                st.markdown(f"**نبذة:** {hdata.get('bio', 'لا توجد نبذة')}")
                st.markdown(f"**الاستراتيجية:** {hdata.get('strategy', 'غير محددة')}")
else:
    st.info("لا توجد بروفايلات مسجلة حتى الآن. قم بإنشاء هويتك من القائمة الجانبية.")

st.markdown("---")
st.subheader("📡 السجل التاريخي الحقيقي لاختبارات الأداء والأهداف الرقمية (Verified Track Record)")

signals = load_signals()

if not signals:
    st.info("لا توجد إشارات مسجلة حتى الآن. ابدأ بتوثيق أول هدف رقمي لك بالأرقام!")
else:
    for sig in signals:
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2, 2, 2])
            
            trader_name = sig.get('trader')
            symbol = sig.get('symbol')
            entry_price = sig.get('entry_price')
            target_price = sig.get('target_price', 0.0)
            direction = sig.get('direction')
            
            col_a.markdown(f"**المتداول:** `{trader_name}`")
            col_b.markdown(f"**الأصل:** `{symbol}` @ الدخول: **${entry_price}**")
            col_c.markdown(f"**الهدف الرقمي:** **${target_price}** ({direction})")
            
            st.markdown(f"🎯 **النموذج / الأداة:** `{sig.get('signal_type')}`")
            
            if sig.get('confirmation_notes'):
                st.markdown(f"📝 **توقيت التأكيد والشروط:** {sig.get('confirmation_notes')}")
            
            # تقييم حركة السعر اللحظي مقارنة بسعر الدخول والهدف المحدد رقمياً
            current_market_price = get_live_market_price(symbol)
            if entry_price > 0 and current_market_price > 0 and target_price > 0:
                price_diff = round(current_market_price - entry_price, 2)
                is_target_higher = target_price > entry_price
                
                # تقييم مدى الاقتراب من الهدف أو تحقيقه
                if is_target_higher:
                    if current_market_price >= target_price:
                        target_status = "🎯 تم تحقيق الهدف الرقمي بنجاح! ✅"
                    elif current_market_price > entry_price:
                        target_status = "📈 في مسار إيجابي نحو الهدف"
                    else:
                        target_status = "📉 تحت سعر الدخول (في مسار سلبي)"
                else:
                    if current_market_price <= target_price:
                        target_status = "🎯 تم تحقيق الهدف الرقمي بنجاح! ✅"
                    elif current_market_price < entry_price:
                        target_status = "📈 في مسار إيجابي نحو الهدف"
                    else:
                        target_status = "📉 فوق سعر الدخول (في مسار سلبي)"
                
                st.markdown(f"📊 **السعر اللحظي الآن:** `${current_market_price}` | **الفارق عن الدخول:** `{price_diff:+.2f}$` | **حالة الهدف:** **{target_status}**")
            
            # عرض بروفايل المحلل أسفل البطاقة بدقة
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
