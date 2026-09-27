import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pytse_client as tse

st.set_page_config(page_title="Iran Stock AI", page_icon="📈", layout="wide")

st.title("📈 تحلیل‌گر هوشمند بورس ایران")
st.caption("نسخه موبایل — تحلیل تکنیکال، حجم، حقیقی/حقوقی و اطلاعات لحظه‌ای")

symbol = st.text_input("نماد را وارد کن", value="وثوق").strip()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

if st.button("🔍 تحلیل سهم", use_container_width=True):
    if not symbol:
        st.warning("نماد را وارد کن.")
        st.stop()

    try:
        ticker = tse.Ticker(symbol)
        df = ticker.history.copy()

        if df.empty:
            st.error("برای این نماد داده‌ای پیدا نشد.")
            st.stop()

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        df["EMA20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["RSI14"] = rsi(df["close"])
        df["VolMA20"] = df["volume"].rolling(20).mean()
        df["VolRatio"] = df["volume"] / df["VolMA20"]

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("آخرین قیمت", f"{last['close']:,.0f}")
        c2.metric("تغییر روزانه", f"{((last['close']/prev['close'])-1)*100:.2f}%")
        c3.metric("RSI", f"{last['RSI14']:.1f}")
        c4.metric("نسبت حجم", f"{last['VolRatio']:.2f}x")

        st.subheader("📊 نمودار")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"],
            low=df["low"], close=df["close"], name="قیمت"
        ))
        fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], name="EMA20"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["EMA50"], name="EMA50"))
        fig.update_layout(height=520, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        recent = df.tail(60)
        support = recent["low"].min()
        resistance = recent["high"].max()

        st.subheader("🎯 جمع‌بندی هوشمند")
        signals = []

        if last["close"] > last["EMA20"]:
            signals.append("قیمت بالای EMA20 است؛ روند کوتاه‌مدت مثبت‌تر است.")
        else:
            signals.append("قیمت زیر EMA20 است؛ روند کوتاه‌مدت هنوز ضعیف است.")

        if last["EMA20"] > last["EMA50"]:
            signals.append("EMA20 بالای EMA50 قرار دارد؛ ساختار میان‌مدت صعودی‌تر است.")
        else:
            signals.append("EMA20 زیر EMA50 است؛ ساختار میان‌مدت هنوز تأیید صعودی ندارد.")

        if last["RSI14"] < 35:
            signals.append("RSI پایین است و سهم وارد ناحیه فروش سنگین شده است.")
        elif last["RSI14"] > 70:
            signals.append("RSI بالاست؛ ریسک اصلاح کوتاه‌مدت افزایش یافته است.")
        else:
            signals.append("RSI در محدوده میانی قرار دارد.")

        if last["VolRatio"] >= 1.5:
            signals.append("حجم حداقل ۱.۵ برابر میانگین ۲۰روزه است؛ افزایش حجم قابل توجه است.")
        else:
            signals.append("حجم هنوز جهش غیرعادی نسبت به میانگین ۲۰روزه ندارد.")

        for s in signals:
            st.write("• " + s)

        st.info(
            f"حمایت تقریبی ۶۰روزه: {support:,.0f} | "
            f"مقاومت تقریبی ۶۰روزه: {resistance:,.0f}"
        )

        st.subheader("👥 حقیقی / حقوقی")
        try:
            ct = ticker.client_types
            if ct is not None and not ct.empty:
                st.dataframe(ct.tail(5), use_container_width=True)
            else:
                st.write("داده حقیقی/حقوقی در دسترس نبود.")
        except Exception:
            st.write("داده حقیقی/حقوقی فعلاً قابل دریافت نیست.")

        st.caption("این برنامه ابزار تحلیل است و سفارش خرید/فروش ارسال نمی‌کند.")

    except Exception as e:
        st.error(f"خطا در دریافت اطلاعات نماد: {e}")
        st.info("نام نماد را دقیقاً مثل بورس وارد کن؛ مثلاً خودرو، فولاد، وبملت یا وثوق.")
