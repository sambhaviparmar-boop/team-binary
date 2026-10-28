
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

DAILY_FILES = {
    "BDI": ROOT / "data" / "indices" / "bdiy_historical.csv",
    "BCI": ROOT / "data" / "indices" / "cape_historical.csv",
    "BPI": ROOT / "data" / "indices" / "panama_historical.csv",
}
WEEKLY_FILE = ROOT / "03_Processed_Data" / "weekly_indices_2021_2025.csv"

START = pd.Timestamp("2021-01-01")
END = pd.Timestamp("2025-12-31")

available_daily_files = {
    code: path for code, path in DAILY_FILES.items() if path.is_file()
}

if set(available_daily_files) != set(DAILY_FILES) and WEEKLY_FILE.is_file():
    print(f"Validating available weekly index file: {WEEKLY_FILE}")
    df = pd.read_csv(WEEKLY_FILE)
    required = {"date", "index_code", "value"}
    if not required.issubset(df.columns):
        raise SystemExit(
            f"Weekly index CSV is missing required columns: {sorted(required - set(df.columns))}"
        )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["index_code"].isin(DAILY_FILES)]
    for code in DAILY_FILES:
        checked = df[df["index_code"] == code]
        print(f"\n{'=' * 12} {code} {'=' * 12}")
        if checked.empty:
            print("ERROR: No weekly records found.")
            continue
        print("Weekly observations:", len(checked))
        print("Invalid dates:", int(checked["date"].isna().sum()))
        print("Missing/non-numeric values:", int(checked["value"].isna().sum()))
        print("Duplicate dates:", int(checked["date"].duplicated().sum()))
        print("Non-positive values:", int((checked["value"] <= 0).sum()))
        print("Date coverage:", checked["date"].min(), "to", checked["date"].max())
else:
    for code in DAILY_FILES:
        if code not in available_daily_files:
            print(f"ERROR: Daily source file missing: {DAILY_FILES[code]}")

for code, path in available_daily_files.items():
    print(f"\n{'=' * 12} {code} {'=' * 12}")

    if not path.exists() or path.stat().st_size == 0:
        print("ERROR: File missing or empty:", path)
        continue

    df = pd.read_csv(path)
    print("Columns:", list(df.columns))
    print("Total source rows:", len(df))

    if not {"Date", "Index"}.issubset(df.columns):
        print("ERROR: Expected Date and Index columns.")
        continue

    dates = pd.to_datetime(df["Date"], errors="coerce")
    values = pd.to_numeric(
        df["Index"].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )

    valid_dates = dates.notna()
    valid_values = values.notna()
    in_range = valid_dates & dates.between(START, END)

    checked = pd.DataFrame({
        "date": dates[in_range],
        "value": values[in_range],
    })

    print("Invalid dates in source:", int((~valid_dates).sum()))
    print("Missing/non-numeric index values:", int((~valid_values).sum()))
    print("Rows in 2021–2025:", len(checked))

    if checked.empty:
        print("ERROR: No valid records in requested date range.")
        continue

    print("Date coverage:", checked["date"].min(), "to", checked["date"].max())
    print("Duplicate dates:", int(checked["date"].duplicated().sum()))
    print("Non-positive values:", int((checked["value"] <= 0).sum()))

    daily = (
        checked.sort_values("date")
        .drop_duplicates("date", keep="last")
        .set_index("date")["value"]
    )

    weekly = daily.resample("W-FRI").last().dropna()

    print("Weekly observations:", len(weekly))
    print("Weekly date coverage:", weekly.index.min(), "to", weekly.index.max())
    print("First 3 weekly values:")
    print(weekly.head(3).to_string())
