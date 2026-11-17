"""Refresh data/jamaica_indicators.csv from the IMF and FRED.

Run:  python update_data.py

New values replace old ones for the same indicator and year. Rows the
sources don't cover (for example recent exchange rate years) are kept.
"""

from pathlib import Path

import io

import pandas as pd
import requests

DATA_FILE = Path(__file__).parent / "data" / "jamaica_indicators.csv"
START_YEAR = 2000

IMF = "IMF World Economic Outlook (DataMapper)"
WB = "World Bank WDI (via FRED)"
PWT = "Penn World Table exchange rate (via FRED)"

# indicator -> IMF DataMapper code
IMF_SERIES = {
    "gdp_growth": "NGDP_RPCH",
    "unemployment": "LUR",
    "debt_gdp": "GGXWDG_NGDP",
    "current_account": "BCA_NGDPD",
}

# indicator -> (FRED series id, scale, source label)
FRED_SERIES = {
    "inflation": ("FPCPITOTLZGJAM", 1, WB),
    "gdp_per_capita": ("PCAGDPJMA646NWDB", 1, WB),
    "gdp_usd_bn": ("MKTGDPJMA646NWDB", 1e-9, WB),
    "population": ("POPTOTJMA647NWDB", 1, WB),
    "fx_rate": ("XRNCUSJMA618NRUG", 1, PWT),
}


def fetch_imf(code: str) -> pd.DataFrame:
    url = f"https://www.imf.org/external/datamapper/api/v1/{code}/JAM"
    payload = requests.get(url, timeout=30).json()
    values = payload["values"][code]["JAM"]
    df = pd.DataFrame({"year": [int(y) for y in values], "value": list(values.values())})
    return df[df["year"] >= START_YEAR]


def fetch_fred(series_id: str) -> pd.DataFrame:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    raw = pd.read_csv(io.StringIO(requests.get(url, timeout=30).text))
    raw.columns = ["date", "value"]
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    raw = raw.dropna()
    raw["year"] = pd.to_datetime(raw["date"]).dt.year
    return raw.loc[raw["year"] >= START_YEAR, ["year", "value"]]


def main(first_projection_year: int) -> None:
    frames = []
    for key, code in IMF_SERIES.items():
        try:
            d = fetch_imf(code)
        except Exception as err:  # keep going if one source is down
            print(f"Skipped {key}: {err}")
            continue
        d["indicator"], d["source"] = key, IMF
        d["is_projection"] = (d["year"] >= first_projection_year).astype(int)
        frames.append(d)
        print(f"{key}: {len(d)} years from IMF")

    for key, (sid, scale, source) in FRED_SERIES.items():
        try:
            d = fetch_fred(sid)
        except Exception as err:
            print(f"Skipped {key}: {err}")
            continue
        d["value"] = d["value"] * scale
        d["indicator"], d["source"], d["is_projection"] = key, source, 0
        frames.append(d)
        print(f"{key}: {len(d)} years from FRED ({sid})")

    if not frames:
        print("Nothing downloaded, data file left unchanged.")
        return

    new = pd.concat(frames)
    old = pd.read_csv(DATA_FILE)
    merged = pd.concat([old, new]).drop_duplicates(["indicator", "year"], keep="last")
    merged = merged[["indicator", "year", "value", "is_projection", "source"]]
    merged.sort_values(["indicator", "year"]).to_csv(DATA_FILE, index=False)
    print(f"Saved {len(merged)} rows to {DATA_FILE}")


if __name__ == "__main__":
    # The IMF marks years after its latest actual data as projections.
    # Move this forward by one each year (for example 2027 once 2026 data is final).
    main(first_projection_year=2026)
