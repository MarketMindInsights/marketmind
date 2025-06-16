import streamlit as st
import yfinance as yf
from textblob import TextBlob
import feedparser
import re

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

st.set_page_config(page_title="MarketMind", layout="centered")
st.title("📊 MarketMind: Smart Stock Analyzer")

symbol = st.text_input("Enter Indian stock symbol (e.g., INFY.NS):", "INFY.NS")

if st.button("Analyze"):
    with st.spinner("Fetching data..."):
        try:
            ticker = yf.Ticker(symbol)
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

            st.subheader("📊 Fundamental Report")
            for k, v in report.items():
                if v == "N/A":
                    continue
                icon = "✅" if ("%" in v and "-" not in v) or ("Cr" in v and "-" not in v) or extract_number(v) > 0 else "❌"
                st.markdown(f"**{k}:** {v} {icon}")
            st.markdown(f"**Final Score:** {score}/6")

            st.subheader("🧠 AI Summary")
            st.write(ai_summary_from_metrics(report, score, sector))

            st.subheader("💰 Valuation Analysis")
            eps = info.get("trailingEps")
            current_price = info.get("currentPrice")
            verdict = "Valuation Verdict: N/A"
            if eps and current_price:
                projected_eps = eps * ((1 + 0.15) ** 5)
                intrinsic = (projected_eps * sector_benchmarks[sector]["PE"]) / ((1 + 0.10) ** 5)
                verdict = "✅ Undervalued" if intrinsic > current_price else "❌ Overvalued"
                st.markdown(f"- Projected EPS (5yr @15%): ₹{projected_eps:.2f}")
                st.markdown(f"- Intrinsic Value: ₹{intrinsic:.2f}")
                st.markdown(f"- Current Price: ₹{current_price}")
                st.markdown(f"- **{verdict}**")
            else:
                st.warning("Missing EPS or current price.")

            st.subheader("🧠 Market Psychology")
            st.write(get_market_psychology(symbol))

            st.subheader("📰 News Sentiment")
            sentiment, headlines = get_news_sentiment(symbol)
            st.markdown(f"**Sentiment:** {sentiment}")
            for h in headlines:
                st.markdown(f"- {h}")

            st.subheader("📊 Buy Recommendation")
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

        except Exception as e:
            st.error(f"Error: {e}")