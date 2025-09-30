import yfinance as yf
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# --- STREAMLIT APP ---
st.set_page_config(page_title="Stock Watchlist Generator", layout="wide")

st.title("📈 Stock Watchlist Generator")

# Input for tickers
tickers_input = st.text_input(
    "Enter stock tickers (comma-separated):",
    value="AAPL, MSFT, GOOGL, AMZN, TSLA"
)

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# Button to fetch data
if st.button("Generate Watchlist"):
    data = []
    hist_data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            data.append({
                "Ticker": ticker,
                "Name": info.get("shortName", "N/A"),
                "Price": info.get("currentPrice", "N/A"),
                "Market Cap": info.get("marketCap", "N/A"),
                "52w High": info.get("fiftyTwoWeekHigh", "N/A"),
                "52w Low": info.get("fiftyTwoWeekLow", "N/A"),
                "PE Ratio": info.get("trailingPE", "N/A"),
            })
            hist_data[ticker] = yf.download(ticker, period="6mo", interval="1d")["Close"]
        except Exception as e:
            st.error(f"Error fetching {ticker}: {e}")

    if data:
        df = pd.DataFrame(data)
        st.subheader("📊 Stock Metrics")
        st.dataframe(df, use_container_width=True)

        # --- Dashboard Summary ---
        st.subheader("📌 Market Sentiment Summary")
        avg_pe = df["PE Ratio"].replace("N/A", pd.NA).dropna().astype(float).mean()
        avg_price = df["Price"].replace("N/A", pd.NA).dropna().astype(float).mean()
        avg_mcap = df["Market Cap"].replace("N/A", pd.NA).dropna().astype(float).mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("📉 Avg Price", f"${avg_price:,.2f}" if pd.notna(avg_price) else "N/A")
        col2.metric("🏦 Avg Market Cap", f"${avg_mcap:,.0f}" if pd.notna(avg_mcap) else "N/A")
        col3.metric("📊 Avg P/E Ratio", f"{avg_pe:.2f}" if pd.notna(avg_pe) else "N/A")

        # --- Download button (fixed) ---
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        st.download_button(
            label="Download as Excel",
            data=output,
            file_name="stock_watchlist.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # --- Heatmap Visualization ---
        if hist_data:
            st.subheader("🔥 Performance Heatmap (6M Daily Returns)")
            hist_df = pd.DataFrame(hist_data)
            returns = hist_df.pct_change().dropna() * 100
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(returns.T, cmap="RdYlGn", center=0, cbar_kws={'label': '% Daily Return'}, ax=ax)
            ax.set_title("Stock Daily Returns Heatmap")
            ax.set_xlabel("Date")
            ax.set_ylabel("Ticker")
            st.pyplot(fig)

        st.subheader("📉 Price History with Indicators")
        for ticker in tickers:
            try:
                hist = yf.download(ticker, period="6mo", interval="1d")

                # Calculate indicators
                hist["SMA20"] = hist["Close"].rolling(window=20).mean()
                hist["SMA50"] = hist["Close"].rolling(window=50).mean()

                delta = hist["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                hist["RSI"] = 100 - (100 / (1 + rs))

                # MACD
                exp1 = hist["Close"].ewm(span=12, adjust=False).mean()
                exp2 = hist["Close"].ewm(span=26, adjust=False).mean()
                hist["MACD"] = exp1 - exp2
                hist["Signal"] = hist["MACD"].ewm(span=9, adjust=False).mean()

                # Plot Price + SMAs + Indicators
                fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1, 1]})

                ax1.plot(hist.index, hist["Close"], label="Close", color="blue")
                ax1.plot(hist.index, hist["SMA20"], label="SMA20", color="orange")
                ax1.plot(hist.index, hist["SMA50"], label="SMA50", color="green")
                ax1.set_title(f"{ticker} - Price & Moving Averages (6M)")
                ax1.set_ylabel("Price ($)")
                ax1.legend()

                # Plot RSI
                ax2.plot(hist.index, hist["RSI"], label="RSI", color="purple")
                ax2.axhline(70, linestyle="--", color="red")
                ax2.axhline(30, linestyle="--", color="green")
                ax2.set_title("Relative Strength Index (RSI)")
                ax2.set_ylabel("RSI")

                # Plot MACD
                ax3.plot(hist.index, hist["MACD"], label="MACD", color="blue")
                ax3.plot(hist.index, hist["Signal"], label="Signal", color="red")
                ax3.bar(hist.index, hist["MACD"] - hist["Signal"], label="Histogram", color="gray", alpha=0.5)
                ax3.set_title("MACD")
                ax3.set_ylabel("MACD")
                ax3.legend()

                plt.tight_layout()
                st.pyplot(fig)

            except Exception as e:
                st.warning(f"Could not fetch chart for {ticker}: {e}")
