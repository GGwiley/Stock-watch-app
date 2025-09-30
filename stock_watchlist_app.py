# stock_watchlist_app_csv.py

import yfinance as yf
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# --- Streamlit App Configuration ---
st.set_page_config(page_title="Stock Watchlist Generator", layout="wide")
st.title("📈 Stock Watchlist Generator")

# --- Input Section ---
tickers_input = st.text_input(
    "Enter stock tickers (comma-separated):",
    value="AAPL, MSFT, GOOGL, AMZN, TSLA"
)

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# --- Caching Function for Download ---
@st.cache_data
def fetch_price_data(ticker, period="6mo", interval="1d"):
    return yf.download(ticker, period=period, interval=interval)

# --- Main Button ---
if st.button("Generate Watchlist"):
    data = []
    hist_data = {}

    with st.spinner("Fetching stock data..."):
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                data.append({
                    "Ticker": ticker,
                    "Name": info.get("shortName", pd.NA),
                    "Price": info.get("currentPrice", pd.NA),
                    "Market Cap": info.get("marketCap", pd.NA),
                    "52w High": info.get("fiftyTwoWeekHigh", pd.NA),
                    "52w Low": info.get("fiftyTwoWeekLow", pd.NA),
                    "PE Ratio": info.get("trailingPE", pd.NA),
                })

                hist_data[ticker] = fetch_price_data(ticker)["Close"]

            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {e}")

    # --- Display Metrics Table ---
    if data:
        df = pd.DataFrame(data)
        st.subheader("📊 Stock Metrics")
        st.dataframe(df, use_container_width=True)

        # --- Market Summary ---
        st.subheader("📌 Market Sentiment Summary")
        avg_pe = df["PE Ratio"].dropna().astype(float).mean()
        avg_price = df["Price"].dropna().astype(float).mean()
        avg_mcap = df["Market Cap"].dropna().astype(float).mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("📉 Avg Price", f"${avg_price:,.2f}" if pd.notna(avg_price) else "N/A")
        col2.metric("🏦 Avg Market Cap", f"${avg_mcap:,.0f}" if pd.notna(avg_mcap) else "N/A")
        col3.metric("📊 Avg P/E Ratio", f"{avg_pe:.2f}" if pd.notna(avg_pe) else "N/A")

        # --- CSV Download Instead of Excel ---
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="stock_watchlist.csv",
            mime="text/csv"
        )

        # --- Heatmap of Returns ---
        if hist_data:
            st.subheader("🔥 Performance Heatmap (6M Daily Returns)")
            hist_df = pd.DataFrame(hist_data)
            returns = hist_df.pct_change().dropna() * 100

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(
                returns.T,
                cmap="RdYlGn",
                center=0,
                cbar_kws={'label': '% Daily Return'},
                ax=ax
            )
            ax.set_title("Stock Daily Returns Heatmap")
            ax.set_xlabel("Date")
            ax.set_ylabel("Ticker")
            st.pyplot(fig)

        # --- Price History Charts ---
        st.subheader("📉 Price History with Indicators")
        for ticker in tickers:
            try:
                hist = fetch_price_data(ticker)
                hist["SMA20"] = hist["Close"].rolling(window=20).mean()
                hist["SMA50"] = hist["Close"].rolling(window=50).mean()

                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(hist.index, hist["Close"], label="Close Price", linewidth=1)
                ax.plot(hist.index, hist["SMA20"], label="SMA 20", linestyle="--")
                ax.plot(hist.index, hist["SMA50"], label="SMA 50", linestyle="--")
                ax.set_title(f"{ticker} Price Chart with SMA20 & SMA50")
                ax.set_xlabel("Date")
                ax.set_ylabel("Price")
                ax.legend()
                st.pyplot(fig)

            except Exception as e:
                st.warning(f"Could not fetch chart for {ticker}: {e}")
