"""
Fetch Fama-French factor data directly from Kenneth French's Data Library.
French reports returns in percent; we divide by 100 to get decimals.
"""
from pathlib import Path
from io import BytesIO
import zipfile
import requests
import pandas as pd

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

FACTOR_COLS_FF3 = ["MKT", "SMB", "HML", "RF"]
FACTOR_COLS_FF4 = ["MKT", "SMB", "HML", "MOM", "RF"]
FACTOR_COLS_FF5 = ["MKT", "SMB", "HML", "RMW", "CMA", "RF"]

_BASE_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"
_DATASETS = {
    "ff3": "F-F_Research_Data_Factors_CSV.zip",
    "ff5": "F-F_Research_Data_5_Factors_2x3_CSV.zip",
    "mom": "F-F_Momentum_Factor_CSV.zip",
}


def _download_zip(url: str) -> bytes:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def _parse_french_csv(content: bytes) -> pd.DataFrame:
    """Parse a French Data Library CSV: skip header rows, stop at annual data."""
    text = content.decode("utf-8", errors="replace")
    lines = text.splitlines()

    data_lines = []
    in_monthly = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_monthly and data_lines:
                break
            continue
        # French monthly data rows start with a 6-digit YYYYMM date
        if stripped[:6].isdigit() and len(stripped[:6]) == 6:
            in_monthly = True
            data_lines.append(stripped)

    if not data_lines:
        raise ValueError("Could not parse French data CSV — format may have changed.")

    from io import StringIO
    parsed = pd.read_csv(StringIO("\n".join(data_lines)), header=None)
    return parsed


def _load_raw(key: str) -> pd.DataFrame:
    cache_path = CACHE_DIR / f"{key}.parquet"
    if cache_path.exists():
        return pd.read_parquet(cache_path)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{_BASE_URL}/{_DATASETS[key]}"
    zip_bytes = _download_zip(url)

    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        csv_name = next(n for n in zf.namelist() if n.endswith(".CSV") or n.endswith(".csv"))
        raw_bytes = zf.read(csv_name)

    raw = _parse_french_csv(raw_bytes)
    raw.to_parquet(cache_path)
    return raw


def _to_date_index(raw: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(raw.iloc[:, 0].astype(int).astype(str), format="%Y%m")
    dates = dates + pd.offsets.MonthEnd(0)
    df = raw.iloc[:, 1:].copy()
    df.index = dates
    df.index.name = "date"
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    return df


def parse_ff3(raw: pd.DataFrame) -> pd.DataFrame:
    df = _to_date_index(raw)
    df.columns = ["MKT", "SMB", "HML", "RF"]
    df[["MKT", "SMB", "HML", "RF"]] /= 100
    return df[FACTOR_COLS_FF3]


def parse_ff4(raw_ff3: pd.DataFrame, raw_mom: pd.DataFrame) -> pd.DataFrame:
    ff3 = parse_ff3(raw_ff3)
    mom_df = _to_date_index(raw_mom)
    mom_df.columns = ["MOM"]
    mom_df["MOM"] /= 100
    combined = ff3.join(mom_df, how="inner")
    return combined[FACTOR_COLS_FF4]


def parse_ff5(raw: pd.DataFrame) -> pd.DataFrame:
    df = _to_date_index(raw)
    df.columns = ["MKT", "SMB", "HML", "RMW", "CMA", "RF"]
    df[["MKT", "SMB", "HML", "RMW", "CMA", "RF"]] /= 100
    return df[FACTOR_COLS_FF5]


def fetch_ff3() -> pd.DataFrame:
    return parse_ff3(_load_raw("ff3"))


def fetch_ff4() -> pd.DataFrame:
    return parse_ff4(_load_raw("ff3"), _load_raw("mom"))


def fetch_ff5() -> pd.DataFrame:
    return parse_ff5(_load_raw("ff5"))


def fetch_factors(model: str) -> pd.DataFrame:
    if model == "ff3":
        return fetch_ff3()
    if model == "ff4":
        return fetch_ff4()
    if model == "ff5":
        return fetch_ff5()
    raise ValueError(f"Unknown model: {model!r}. Must be 'ff3', 'ff4', or 'ff5'.")
