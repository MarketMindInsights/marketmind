import streamlit as st
import yfinance as yf
from textblob import TextBlob
import feedparser
import re
import pandas as pd
import datetime

st.set_page_config(page_title="📊 MarketMind", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #111;
        color: #fefefe;
        font-size: 16px;
    }

    .stApp {
        background-color: #000;
        padding: 3rem 4rem;
        border-radius: 12px;
    }

    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
    }

    .stTextInput > div > div > input {
        background-color: #181818;
        color: #fff;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 16px;
        font-size: 16px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #0f0f0f, #444);
        border: none;
        color: white;
        padding: 14px 30px;
        font-size: 16px;
        border-radius: 10px;
        transition: 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #222, #666);
    }

    .stCheckbox > label {
        color: #ccc;
        font-size: 15px;
    }

    .stExpanderHeader {
        background-color: #181818;
        color: #eee;
        font-size: 18px;
        font-weight: 600;
        border-bottom: 1px solid #444;
        padding: 10px;
    }

    .stCaption {
        color: #888;
        font-size: 13px;
        margin-top: 20px;
    }

    hr {
        border: none;
        border-top: 1px solid #333;
        margin: 2rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ----- Copy your helper functions from marketmind_v5_final.py -----
# Include: extract_number, determine_sector, sector_benchmarks, get_news_sentiment, get_market_psychology, ai_summary_from_metrics

# For demo: we'll simulate with a minimal version.
from marketmind_v5_final import (
    extract_number,
    determine_sector,
    sector_benchmarks,
    get_news_sentiment,
    get_market_psychology,
    ai_summary_from_metrics
)

# Sector Outlook Multiplier
sector_outlook_map = {
    "Renewable": 15,
    "EV": 10,
    "IT": 5,
    "Banking": 0,
    "FMCG": 0,
    "Oil": -15,
    "Coal": -15,
    "Industrial": -10,
    "Default": 0
}

st.title("📊 MarketMind: Is Your Stock Pick Rational?")
st.caption("Understand fundamentals, sentiment, and psychology in one click.")

with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    stock_options = ["INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK", "ONGC", "SBIN", "WIPRO", "HINDUNILVR", "BAJFINANCE"]
    with col2:
        symbol = st.text_input("🔍 Enter Stock Symbol (e.g., INFY):", "").strip().upper()
        if symbol:
            st.session_state["last_symbol"] = symbol if symbol.endswith(".NS") or symbol.endswith(".BSE") else symbol + ".NS"
        analyze = st.button("🚀 Analyze")

if analyze:
    with st.spinner("Fetching data..."):
        try:
            ticker = yf.Ticker(st.session_state.get("last_symbol", symbol))
            info = ticker.info
            sector = determine_sector(info)

            # Prepare report
            report = {
                "PE Ratio": str(info.get("trailingPE", "N/A")),
                "ROE": str(info.get("returnOnEquity", 0) * 100) + "%" if info.get("returnOnEquity") else "N/A",
                "EPS Growth": "N/A",
                "Free Cash Flow": "N/A",
                "Profit Margin": str(info.get("profitMargins", 0) * 100) + "%" if info.get("profitMargins") else "N/A",
                "PB Ratio": str(info.get("priceToBook", "N/A")),
            }

            score = sum(
                1 for v in report.values()
                if v != "N/A" and extract_number(v) is not None and extract_number(v) > 0
            )

            eps = info.get("trailingEps")
            current_price = info.get("currentPrice")

            growth_rate = 0.15
            discount_rate = 0.10

            custom_sector_pe = {
                "Power": 35,
                "Infrastructure": 30,
                "Renewable": 40,
                "Default": 15
            }
            sector_pe = custom_sector_pe.get(sector, 15)

            projected_eps = eps * ((1 + growth_rate) ** 5)
            intrinsic = (projected_eps * sector_pe) / ((1 + discount_rate) ** 5)

            verdict = "✅ Undervalued" if intrinsic > current_price else "❌ Overvalued"

            tabs = st.tabs(["Overview", "Valuation", "Sentiment", "Recommendation"])

            with tabs[0]:  # Overview
                st.header("📊 Fundamental Report")
                for k, v in report.items():
                    if v == "N/A":
                        continue
                    icon = "✅" if ("%" in v and "-" not in v) or ("Cr" in v and "-" not in v) or extract_number(v) > 0 else "❌"
                    st.markdown(f"<span style='font-size:16px'><strong>{k}:</strong> {v} {icon}</span>", unsafe_allow_html=True)
                st.markdown(f"**Final Score:** {score}/6")
                if score >= 5:
                    st.markdown("🏅 <strong>Top Fundamental Pick</strong>", unsafe_allow_html=True)
                elif score == 4:
                    st.markdown("👀 <strong>Watchlist Potential</strong>", unsafe_allow_html=True)
                else:
                    st.markdown("⚠️ <strong>High Risk Zone</strong>", unsafe_allow_html=True)

                sector_icon_map = {
                    "Power": "🔌", "Oil": "🛢️", "IT": "💻", "Banking": "🏦", "FMCG": "🛍️", 
                    "Renewable": "🌿", "Coal": "⛏️", "Infrastructure": "🏗️", "Default": "📦"
                }
                st.markdown(f"**Sector:** {sector_icon_map.get(sector, '📦')} {sector}")

                if report["PE Ratio"] != "N/A" and report["PB Ratio"] != "N/A":
                    sector_avg = sector_benchmarks.get(sector, sector_benchmarks["Default"])
                    pe_df = pd.DataFrame({
                        "P/E": [extract_number(report["PE Ratio"]), sector_avg["PE"]],
                    }, index=["This Stock", "Sector Avg"])
                    pb_df = pd.DataFrame({
                        "P/B": [extract_number(report["PB Ratio"]), sector_avg["PB"]],
                    }, index=["This Stock", "Sector Avg"])

                    st.markdown("**P/E Comparison**")
                    st.bar_chart(pe_df)

                    st.markdown("**P/B Comparison**")
                    st.bar_chart(pb_df)

                st.header("🧠 AI Summary")
                st.write(ai_summary_from_metrics(report, score, sector))

                sector_outlook = sector_outlook_map.get(sector, 0)
                base_score = score * 15 + (25 if '✅ Undervalued' in (locals().get('verdict', '') or '') else 10)
                adjusted_score = min(100, max(0, base_score + sector_outlook))

                st.markdown("### 📈 MarketMind Score", unsafe_allow_html=True)
                st.markdown(f"<h4 style='color:#00ffcc'>🔢 Base Score: <strong>{base_score}/100</strong></h4>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='color:#33ff99'>🌍 Sector Outlook Applied: <strong>{adjusted_score}/100</strong></h4>", unsafe_allow_html=True)
                st.progress(int(adjusted_score))

            with tabs[1]:  # Valuation
                st.header("💰 Valuation Analysis")

                st.markdown(f"- EPS Used: ₹{eps}")
                st.markdown(f"- Sector PE Used: {sector_pe}")
                st.markdown(f"- Growth Rate Assumption: {growth_rate * 100}%")
                st.markdown(f"- Discount Rate Assumption: {discount_rate * 100}%")

                if intrinsic > current_price * 5:
                    st.warning("⚠️ Intrinsic value is unusually high — check EPS or growth assumptions.")
                if intrinsic < current_price * 0.3:
                    st.warning("⚠️ Intrinsic value is far below market price. This may be a high-growth stock or valuation assumptions may need review.")

                st.markdown(f"- Projected EPS (5yr): ₹{projected_eps:.2f}")
                st.markdown(f"- Intrinsic Value: ₹{intrinsic:.2f}")
                st.markdown(f"- Current Price: ₹{current_price}")
                st.markdown(f"- **{verdict}**")

                st.markdown("### 🔍 Raw Valuation Inputs")
                st.json({
                    "EPS": eps,
                    "Sector PE": sector_pe,
                    "Growth Rate": growth_rate,
                    "Discount Rate": discount_rate,
                    "Projected EPS (5yr)": projected_eps,
                    "Intrinsic Value": intrinsic,
                    "Current Price": current_price
                })

            with tabs[2]:  # Sentiment
                st.header("🧠 Market Psychology")
                st.write(get_market_psychology(st.session_state.get("last_symbol", symbol)))

                # ----- Behavioral Alert -----
                history = ticker.history(period="7d")
                price_change = None
                if not history.empty:
                    closing_prices = history["Close"]
                    volume = history["Volume"]
                    price_change = (closing_prices.iloc[-1] - closing_prices.iloc[0]) / closing_prices.iloc[0] * 100
                    latest_volume = volume.iloc[-1]
                    avg_volume = volume.mean()

                    st.markdown("### 📉 Behavioral Alert")
                    if price_change and abs(price_change) > 7:
                        if price_change > 0:
                            st.warning(f"🚨 FOMO Alert: Stock rose {price_change:.2f}% in the last week.")
                        else:
                            st.warning(f"😨 Panic Risk: Stock dropped {price_change:.2f}% in the last week.")
                    elif latest_volume > 1.5 * avg_volume:
                        st.info("⚠️ Sudden spike in trading volume — watch for sentiment shift.")
                    else:
                        st.info("🧘 Calm Market: No significant emotional signals detected.")

                st.header("📰 News Sentiment")
                sentiment, headlines = get_news_sentiment(st.session_state.get("last_symbol", symbol))
                st.markdown(f"**Sentiment:** {sentiment}")
                for h in headlines:
                    st.markdown(f"🔹 <span style='font-size:16px'>{h}</span>", unsafe_allow_html=True)

            with tabs[3]:  # Recommendation
                st.header("🎯 MarketMind Verdict (Smart Summary Mode)")
                if score >= 5 and '✅ Undervalued' in verdict and "🟢 Positive sentiment" in sentiment:
                    st.success("✅ Strong Buy: Undervalued with solid fundamentals and positive sentiment.")
                elif score >= 4 and '✅ Undervalued' in verdict:
                    st.success("✅ Likely Buy: Good fundamentals, undervaluation detected.")
                elif score >= 4 and '❌ Overvalued' in verdict:
                    st.info("💡 Consider for Growth Portfolio: Strong fundamentals but currently expensive.")
                elif score >= 3:
                    st.warning("⚠️ Watch: Fundamentals are average. Further confirmation needed.")
                else:
                    st.error("❌ Avoid: Weak fundamentals or high valuation.")

                if adjusted_score >= 80:
                    st.success("✅ **Final Verdict: BUY** — Strong fundamentals and undervaluation. 🟢")
                elif adjusted_score >= 60:
                    st.info("⏳ **Final Verdict: WATCH** — Decent fundamentals, needs confirmation. 🟡")
                else:
                    st.error("❌ **Final Verdict: AVOID** — Weak fundamentals or poor outlook. 🔴")

        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.caption("Made by MarketMind Insights • Smart Investing for Everyone")