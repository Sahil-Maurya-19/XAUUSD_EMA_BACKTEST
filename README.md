# XAUUSD_EMA_BACKTEST
An automated quantitative backtesting engine built in Python to evaluate algorithmic day-trading strategies using dynamic support/resistance zones and moving average crossovers.


# 📈 Algorithmic Trading Performance Analyzer

**An automated quantitative backtesting engine built in Python to evaluate high risk-to-reward intraday trading strategies.**

## 📝 Project Overview
This project is an end-to-end data analysis pipeline designed to test the viability of mean-reversion and momentum trading strategies on historical Forex/Commodity data. Using 5-minute tick data for XAUUSD (Spot Gold), the engine cleans the time-series data, programmatically engineers technical indicators, executes simulated trades based on strict risk management rules, and outputs a professional financial tear sheet.

This project demonstrates core competencies in **time-series data manipulation, algorithm design, feature engineering, and data visualization.**

## 🛠️ Tech Stack
* **Language:** Python
* **Data Manipulation:** `pandas`, `numpy`
* **Data Visualization:** `matplotlib`
* **Domain Context:** Quantitative Finance, Algorithmic Trading, Risk Management

---

## 🚀 Key Features

* **Time-Series Data Engineering:** Cleans and indexes large datasets (70,000+ rows) of OHLCV market data, handling missing values and structural formatting.
* **Dynamic Feature Generation:** Calculates Fast/Slow Exponential Moving Averages (EMAs) and maps dynamic Support (Demand) and Resistance (Supply) zones using rolling lookback windows.
* **Algorithmic Signal Detection:** Generates automated Buy/Sell signals by identifying specific crossover conditions occurring within 0.1% proximity to structural zones, effectively filtering out "false" entries.
* **Rigorous Trade Simulation:** Features a custom backtesting loop that executes trades with a dynamic Stop-Loss (placed slightly outside structural zones) and enforces a strict 1:2 Risk-to-Reward ratio.
* **Automated KPI Reporting:** Calculates industry-standard metrics including Win Rate, Gross PnL, and Profit Factor, outputting a visual equity curve and drawdown chart.

---

## 🏗️ System Architecture 

1. **Data Ingestion:** Loads raw CSV data and converts it into a structured Pandas DatetimeIndex DataFrame.
2. **Indicator Mapping:** Calculates the 9-EMA and 21-EMA, and establishes 20-period rolling maximums/minimums for supply and demand zones.
3. **Signal Generation:** Flags potential entries mathematically without look-ahead bias.
4. **Execution Engine:** Iterates through the data chronologically, triggering active trades, monitoring dynamic stop-loss levels, and logging exits.
5. **Evaluation:** Compiles the trade ledger and utilizes Matplotlib to render the final performance dashboard.

---

## 📊 Results & Visualization

*The algorithm successfully processed 71,000+ data points, executing over 400 simulated trades while maintaining a disciplined risk profile.*

### Performance Tear Sheet
<img width="1529" height="789" alt="image" src="https://github.com/user-attachments/assets/47429c7e-d4eb-4a31-9769-285687d5a7b2" />


**Key Performance Indicators (Sample Output):**
* **Total Trades Executed:** 430
* **Risk/Reward Profile:** 1:2
* **Profit Factor:** 1
* **Net PnL:** 0.13 points
