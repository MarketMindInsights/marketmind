import re
import yfinance as yf
# ---------------- Market Psychology ----------------
def get_market_psychology(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1mo")
        if data.empty:
            return "⚠️ No price data available"

        closing_prices = data["Close"]
        volume = data["Volume"]

        price_change = (closing_prices.iloc[-1] - closing_prices.iloc[0]) / closing_prices.iloc[0] * 100
        avg_volume = volume.mean()
        latest_volume = volume.iloc[-1]
        volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1

        if price_change > 10 and volume_ratio > 1.5:
            return "🧠 Market Psychology: 🚀 FOMO building (high volume & price surge)"
        elif price_change < -10:
            return "🧠 Market Psychology: 😨 Panic selling detected"
        elif volume_ratio > 2:
            return "🧠 Market Psychology: 🔥 High activity, watch closely"
        else:
            return "🧠 Market Psychology: 🟡 Sideways/neutral sentiment"
    except Exception as e:
        return f"🧠 Market Psychology: ⚠️ Unable to analyze ({e})"

# --- News Sentiment Analysis ---
import feedparser
from textblob import TextBlob

# ---------------- News Sentiment Function ----------------
def get_news_sentiment(symbol):
    try:
        query = symbol.replace(".NS", "")
        url = f"https://news.google.com/rss/search?q={query}+stock&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)
        entries = feed.entries[:5]
        headlines = [entry.title for entry in entries]

        if not headlines:
            return "🟡 Neutral (no major news found)", []

        negative_keywords = ["decline", "drop", "loss", "down", "plunge", "cut", "fall", "dip", "decrease"]
        positive_keywords = ["profit", "gain", "growth", "rise", "jump", "beat", "increase", "record high"]

        total_polarity = 0
        count = 0

        for title in headlines:
            weight = 1.0
            lowered = title.lower()

            if "?" in title:
                weight *= 0.5  # reduce impact of question headlines

            if any(word in lowered for word in negative_keywords):
                weight *= 1.2
                polarity = -0.4
            elif any(word in lowered for word in positive_keywords):
                weight *= 1.2
                polarity = 0.4
            else:
                polarity = TextBlob(title).sentiment.polarity

            total_polarity += polarity * weight
            count += 1

        avg = total_polarity / count if count else 0

        if avg > 0.1:
            sentiment = "🟢 Positive sentiment"
        elif avg < -0.1:
            sentiment = "🔴 Negative sentiment"
        else:
            sentiment = "🟡 Neutral sentiment"

        return sentiment, headlines
    except Exception as e:
        return f"⚠️ Unable to fetch sentiment: {e}", []

# ---------------- Sector Benchmarks ----------------
sector_benchmarks = {
    "IT": {"PE": 28, "PB": 6},
    "Utilities": {"PE": 12, "PB": 2},
    "Banking": {"PE": 15, "PB": 2.5},
    "FMCG": {"PE": 40, "PB": 10},
    "Auto": {"PE": 20, "PB": 3},
    "Default": {"PE": 25, "PB": 3}
}

# ---------------- Sector Mapping ----------------
def determine_sector(info):
    sector_map = {
        "Information Technology": "IT",
        "Utilities": "Utilities",
        "Banking": "Banking",
        "Financial Services": "Banking",
        "Consumer Defensive": "FMCG",
        "Consumer Cyclical": "Auto",
        "Auto": "Auto",
        "Industrial": "Auto"
    }
    raw_sector = info.get("sector", "Default")
    return sector_map.get(raw_sector, "Default")

# ---------------- Helper ----------------
def extract_number(value):
    try:
        value = str(value)
        cleaned = re.sub(r"[^\d.\-]", "", value)
        return float(cleaned) if cleaned not in ["", ".", "-", "-."] else None
    except:
        return None

# ---------------- AI Summary ----------------
def ai_summary_from_metrics(report, score, sector="Default"):
    strengths, weaknesses = [], []
    risk_level = "Moderate"

    pe = extract_number(report.get("PE Ratio", "0"))
    roe = extract_number(report.get("ROE", "0%"))
    eps_growth = extract_number(report.get("EPS Growth", "0%"))
    fcf = extract_number(report.get("Free Cash Flow", "0"))
    margin = extract_number(report.get("Profit Margin", "0%"))
    pb = extract_number(report.get("PB Ratio", "0"))

    if pe is not None and pe > 0:
        avg = sector_benchmarks.get(sector, sector_benchmarks["Default"])["PE"]
        if pe < avg:
            strengths.append(f"valuation is low vs sector avg P/E ({pe} < {avg})")
        elif pe > avg:
            weaknesses.append(f"valuation is high vs sector avg P/E ({pe} > {avg})")
    elif pe is not None and pe <= 0:
        weaknesses.append(f"P/E ratio is invalid or negative (PE = {pe})")

    if roe is not None and roe > 0:
        if roe > 15:
            strengths.append("strong return on equity (ROE > 15%)")
        elif roe < 5:
            weaknesses.append("poor return on equity (ROE < 5%)")
    elif roe is not None and roe <= 0:
        weaknesses.append(f"ROE is negative or zero (ROE = {roe}%)")

    if eps_growth is not None and eps_growth > 0:
        if eps_growth > 10:
            strengths.append("strong earnings growth")
        elif eps_growth < 5:
            weaknesses.append("low earnings growth")
    elif eps_growth is not None and eps_growth <= 0:
        weaknesses.append(f"EPS growth is negative or zero ({eps_growth}%)")

    if fcf is not None and fcf > 0:
        strengths.append("positive free cash flow")
    elif fcf is not None and fcf <= 0:
        weaknesses.append(f"free cash flow is zero or negative (₹{fcf} Cr)")

    if margin is not None:
        if margin >= 15:
            strengths.append("healthy profit margin")
        elif margin < 5:
            weaknesses.append("thin profit margins")
        elif margin <= 0:
            weaknesses.append(f"profit margin is zero or negative ({margin}%)")

    if pb is not None:
        avg = sector_benchmarks.get(sector, sector_benchmarks["Default"])["PB"]
        if pb > 0 and pb < avg:
            strengths.append(f"book value is attractive (PB < sector avg {avg})")
        elif pb < 0 or pb > avg * 1.2:
            weaknesses.append(f"PB ratio is unusually high or negative (PB = {pb})")

    risk_level = "Low" if score >= 5 else "Moderate" if score >= 3 else "High"

    summary_parts = []
    if strengths:
        summary_parts.append("good fundamentals including " + ", ".join(strengths) + ".")
    if weaknesses:
        summary_parts.append("However, there are concerns such as " + ", ".join(weaknesses) + ".")
    
    if not strengths and weaknesses:
        summary = "This stock has weak fundamentals. " + " ".join(summary_parts)
    elif not strengths and not weaknesses:
        summary = "This stock has limited data for evaluation."
    else:
        summary = "This stock has " + " ".join(summary_parts)

    summary += f" Overall risk profile appears **{risk_level}** based on current fundamentals."
    return summary

# ---------------- Advice & Scoring Function ----------------
def print_advice_section(score, verdict, risk, horizon):
    score_components = []

    score_components.append(score * 5)  # Fundamentals (max 30)
    valuation_score = 25 if '✅ Undervalued' in verdict else 10 if '❌ Overvalued' in verdict else 0
    score_components.append(valuation_score)

    # Risk logic
    if risk == "Low" and score >= 5:
        score_components.append(20)
    elif risk == "Medium" and score >= 3:
        score_components.append(15)
    else:
        score_components.append(10)

    # Horizon logic
    if horizon == "3+ Years" and score >= 5:
        score_components.append(20)
    elif horizon == "1 Year":
        score_components.append(15)
    else:
        score_components.append(10)

    buy_score = min(100, sum(score_components))

    print(f"\n🎯 Investor Profile: {risk} Risk | {horizon}")
    print(f"\n✅ Buy Score: {buy_score}/100")
    print("\n🧭 Advice:")

    if '❌ Overvalued' in verdict or buy_score < 60:
        print("• Short-term: ⚠️ Risky due to overvaluation or weak momentum")
    else:
        print("• Short-term: ✅ Solid opportunity")

    if score >= 4 and '✅ Undervalued' in verdict:
        print("• Long-term: ✅ Strong pick with solid fundamentals")
    else:
        print("• Long-term: ⚠️ Only consider if buying for long horizon")

# ---------------- Main Execution ----------------
if __name__ == "__main__":
    symbol = input("Enter Indian stock symbol (e.g., INFY.NS): ").strip().upper()

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

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
        sector = determine_sector(info)

        print("\n📊 Fundamental Report")
        print("---------------------")
        for k, v in report.items():
            if v == "N/A":
                continue
            icon = "✅" if ("%" in v and "-" not in v) or ("Cr" in v and "-" not in v) or extract_number(v) > 0 else "❌"
            print(f"{k}: {v} {icon}")

        print(f"\nFinal Score: {score}/6")

        print("\n🧠 AI Summary:")
        print(ai_summary_from_metrics(report, score, sector))

        # -------- Valuation --------
        print("\n💰 Valuation Analysis")
        verdict = "Valuation Verdict: N/A"
        try:
            eps = info.get("trailingEps")
            current_price = info.get("currentPrice")
            est_growth_rate = 0.15
            years = 5
            discount_rate = 0.10

            if eps and current_price:
                sector_pe = sector_benchmarks.get(sector, sector_benchmarks["Default"])["PE"]
                projected_eps = eps * ((1 + est_growth_rate) ** years)
                intrinsic = (projected_eps * sector_pe) / ((1 + discount_rate) ** years)

                verdict = "✅ Undervalued" if intrinsic > current_price else "❌ Overvalued"
                print(f"Projected EPS (5yr @ 15%): ₹{projected_eps:.2f}")
                print(f"Intrinsic Value (discounted): ₹{intrinsic:.2f}")
                print(f"Current Price: ₹{current_price}")
                print(f"Valuation Verdict: {verdict}")
            else:
                print("Valuation Verdict: N/A (missing EPS or price)")

        except Exception as ve:
            print(f"[ERROR] Valuation failed: {ve}")


        # ---- Market Psychology ----
        print("\n" + get_market_psychology(symbol))

        # -------- News Sentiment --------
        print("\n📰 News Sentiment Analysis")
        sentiment, headlines = get_news_sentiment(symbol)
        print(f"Sentiment: {sentiment}")
        if headlines:
            print("Recent headlines:")
            for h in headlines:
                print(f"- {h}")

    except Exception as e:
        print(f"[ERROR] Failed to fetch or process data: {e}")


    # -------- Final Recommendation --------
    print("\n📊 Buy Recommendation")
    if score >= 5 and '✅ Undervalued' in verdict and "🟢 Positive sentiment" in sentiment:
        print("✅ Strong Buy: Undervalued with solid fundamentals and positive sentiment.")
    elif score >= 4 and '✅ Undervalued' in verdict:
        print("✅ Likely Buy: Good fundamentals, undervaluation detected.")
    elif score >= 3 and '🟡 Neutral sentiment' in sentiment:
        print("⚠️ Watch: Fundamentals are average. Wait for better signal.")
    elif score < 3 or '❌ Overvalued' in verdict:
        print("❌ Avoid: Weak fundamentals or overvaluation.")
    else:
        print("⚠️ Neutral: Mixed signals. More analysis needed.")