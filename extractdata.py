from pathlib import Path
import pandas as pd

FIXED = ["Week", "Day", "Date", "Events"]
Y11 = ["11 - Class", "11 - Task Name", "11 - Weighting", "11 - Task Type", "11 - Other Notes"]
Y12 = ["12 - Class", "12 - Task Name", "12 - Weighting", "12 - Task Type", "12 - Other Notes"]

def find_header_row(raw: pd.DataFrame, max_scan: int = 20) -> int:
    target = [c.lower() for c in FIXED]
    for i in range(min(max_scan, len(raw))):
        row = raw.iloc[i].fillna("")
        probe = [str(row.get(j, "")).strip().lower() for j in range(4)]
        if probe == target:
            return i
    return 0

def fill_down(df, col):
    if col not in df.columns:
        return
    cur = None
    for i, v in df[col].items():
        if pd.isna(v) or str(v).strip() in ("", "nan", "nat"):
            if cur:
                df.at[i, col] = cur
        else:
            cur = v

def require_columns(df: pd.DataFrame, cols: list[str], label: str):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing {label} columns: {missing}")

def remove_temp_rows(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    name = cols[0]
    return df[df[name] != "Select Class"].copy()

def extract_to_json(xlsx_path: str, outdir: str = "data"):
    path = Path(xlsx_path)
    raw = pd.read_excel(path, sheet_name="Sheet1", header=None, dtype=str)
    hdr = find_header_row(raw)
    df = pd.read_excel(path, sheet_name="Sheet1", header=hdr, dtype=str)

    require_columns(df, FIXED, "fixed")
    require_columns(df, Y11, "Year 11")
    require_columns(df, Y12, "Year 12")

    for c in FIXED:
        fill_down(df, c)

    df11 = remove_temp_rows(df, Y11)
    df12 = remove_temp_rows(df, Y12)

    def block(frame, cols):
        out = frame[FIXED + cols].copy()
        mask = out[cols].apply(lambda s: s.fillna("").astype(str).str.strip()).eq("").all(axis=1)
        return out.loc[~mask]

    df11 = block(df11, Y11)
    df12 = block(df12, Y12)

    out_dir = Path(outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in (df11, df12):
        if "Date" in f.columns:
            f["Date"] = pd.to_datetime(f["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

    df11.to_json(out_dir / "year11.json", orient="records", indent=2)
    df12.to_json(out_dir / "year12.json", orient="records", indent=2)

    print(df11)
    print(df12)

if __name__ == "__main__":
    extract_to_json("Test Senior Assessment Calendar.xlsx")
