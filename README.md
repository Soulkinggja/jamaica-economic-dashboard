# Jamaica Economic Dashboard

An interactive dashboard that shows how Jamaica's economy has changed since 2000, built with Python, pandas, Plotly and Streamlit.

**Live app:** https://jamaica-economy.streamlit.app

## What it shows

* Headline numbers for the latest year: growth, inflation, unemployment, public debt, the exchange rate and GDP per person
* Key takeaways written from the data, so they update when the data does
* Charts for growth, prices and the exchange rate, jobs, debt and the current account
* IMF projections to 2031, shown as dashed lines and striped bars, which you can switch off
* Key events marked on every chart: the 2008 financial crisis, the 2013 IMF programme, COVID 19, Hurricane Beryl (2024) and Hurricane Melissa (2025)
* A data table with a CSV download

## Data sources

| Indicator | Source |
| --- | --- |
| Real GDP growth, unemployment, public debt, current account | IMF World Economic Outlook (DataMapper API) |
| Inflation, GDP, GDP per person, population | World Bank World Development Indicators, via FRED |
| Exchange rate (JMD per USD) | Penn World Table via FRED to 2023; 2024 and 2025 are averages of daily market rates |

All data sits in `data/jamaica_indicators.csv` in long format (indicator, year, value, is_projection, source).

## Run it on your computer

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Refresh the data

```bash
python update_data.py
```

This pulls the latest figures from the IMF and FRED and merges them into the CSV. Each year, move `first_projection_year` forward by one at the bottom of the script.

## Project structure

```
app.py                     the dashboard
update_data.py             data refresh script (IMF + FRED)
data/jamaica_indicators.csv
requirements.txt
.streamlit/config.toml     theme
```

Built by [Devin McIntosh](https://www.linkedin.com/in/devinlerandezmcintosh).
