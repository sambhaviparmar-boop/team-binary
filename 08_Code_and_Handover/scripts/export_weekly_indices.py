
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "03_Processed_Data" / "weekly_indices_2021_2025.csv"

FILES = {
    "BDI": ROOT / "data" / "indices" / "bdiy_historical.csv",
    "BCI": ROOT / "data" / "indices" / "cape_historical.csv",
    "BPI": ROOT / "data" / "indices" / "panama_historical.csv",
}

SOURCE_URL = (
    "https://github.com/yieldchaser/Shipping/tree/main/data/indices"
)

START = pd.Timestamp("2021-01-01")
END = pd.Timestamp("2025-12-31")

frames = []

available_files = {code: path for code, path in FILES.items() if path.is_file()}

if set(available_files) != set(FILES) and OUT.is_file():
    existing = pd.read_csv(OUT)
    required = {
        "date", "index_code", "value", "unit", "source", "source_url",
        "source_type", "verification_status", "aggregation_method",
    }
    if not required.issubset(existing.columns):
        raise SystemExit(
            f"Existing weekly index file is missing required columns: "
            f"{sorted(required - set(existing.columns))}"
        )
    existing["date"] = pd.to_datetime(existing["date"], errors="coerce")
    existing["value"] = pd.to_numeric(existing["value"], errors="coerce")
    existing = existing[existing["index_code"].isin(FILES)]
    if existing[["date", "value"]].isna().any().any():
        raise ValueError(f"Existing weekly index file contains invalid dates or values: {OUT}")
    if existing.duplicated(["date", "index_code"]).any():
        raise ValueError(f"Existing weekly index file contains duplicate dates: {OUT}")
    if (existing["value"] <= 0).any():
        raise ValueError(f"Existing weekly index file contains non-positive values: {OUT}")
    print("Daily source files are incomplete; validated the existing weekly file:")
    print("Weekly file:", OUT)
    print("Total rows:", len(existing))
    print("\nRows per index:")
    print(existing.groupby("index_code").size().to_string())
    print("\nDate coverage:")
    print(existing.groupby("index_code")["date"].agg(["min", "max"]).to_string())
    raise SystemExit(0)
elif set(available_files) != set(FILES):
    missing = sorted(set(FILES) - set(available_files))
    raise SystemExit(
        "Cannot rebuild weekly indices; missing daily source files for "
        f"{', '.join(missing)}. Existing weekly file: {OUT}"
    )

for code, path in available_files.items():
    df = pd.read_csv(path)

    dates = pd.to_datetime(df["Date"], errors="coerce")
    values = pd.to_numeric(
        df["Index"].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )

    data = pd.DataFrame({"date": dates, "value": values})
    data = data.dropna()
    data = data[data["date"].between(START, END)]
    data = data.sort_values("date")

    if data["date"].duplicated().any():
        raise ValueError(f"{code}: duplicate dates found; export stopped")

    if (data["value"] <= 0).any():
        raise ValueError(f"{code}: non-positive index values; export stopped")

    # Last available source observation in each Friday-ending week.
    weekly = (
        data.set_index("date")["value"]
        .resample("W-FRI")
        .last()
        .dropna()
        .rename("value")
        .reset_index()
    )

    weekly["index_code"] = code
    weekly["unit"] = "index_points"
    weekly["source"] = "yieldchaser/Shipping GitHub"
    weekly["source_url"] = SOURCE_URL
    weekly["source_type"] = "community_maintained"
    weekly["verification_status"] = "unverified"
    weekly["aggregation_method"] = "last_available_observation_W-FRI"

    frames.append(weekly)

result = pd.concat(frames, ignore_index=True)

result = result[
    [
        "date",
        "index_code",
        "value",
        "unit",
        "source",
        "source_url",
        "source_type",
        "verification_status",
        "aggregation_method",
    ]
].sort_values(["date", "index_code"])

OUT.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUT, index=False, date_format="%Y-%m-%d")

print("Export complete:", OUT)
print("Total rows:", len(result))
print("\nRows per index:")
print(result.groupby("index_code").size().to_string())
print("\nDate coverage:")
print(result.groupby("index_code")["date"].agg(["min", "max"]).to_string())
print("\nFirst 5 rows:")
print(result.head().to_string(index=False))
