import argparse
from pathlib import Path
import pandas as pd

FIXEDCOL = ["Week", "Day", "Date", "Events"]

Y11 = ["11 - Class", "11 - Task Name", "11 - Weighting", "11 - Task Type", "11 - Other Notes"]
Y12 = ["12 - Class", "12 - Task Name", "12 - Weighting", "12 - Task Type", "12 - Other Notes"]

def _find_header_row(raw: pd.DataFrame, max_scan: int = 20) -> int:
    # Locates the Header row incase the excel users change the row
    for i in range(min(max_scan, len(raw))):
        row = raw.iloc[i].fillna("")
        first4 = [str(row.get(j, "")).strip().lower() for j in range(4)]
        if first4 == ["week", "day", "date", "events"]:
            return i
        return 0
    
def _stop_at_blank_week(df_in: pd.DataFrame) -> pd.DataFrame:
    # Don't export rows after the first week = ""
    keep_rows = []
    
    for _, r in df_in.iterrows():
        week_val = str(r.get("Week", "")).strip().lower()
        if week_val == "" or week_val == "nan":
            break
        keep_rows.append(r)

    if not keep_rows:
        return df_in.iloc[0:0].copy()
    
    return pd.DataFrame(keep_rows, columns=df_in.columns)

def _require_columns(df: pd.DataFrame, cols: list[str], label: str ):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing {label} columns: {missing}")

def extract_sheet1_json(xlsx_path: str, outdir: str = "."):
    raw = pd.read_excel(xlsx_path, sheet_name="Sheet1", header=None, dtype=str)
    hdr = _find_header_row(raw)
    df = pd.read_excel(xlsx_path, sheet_name="Sheet1", header=hdr, dtype=str)

    _require_columns(df, FIXEDCOL, "fixed")
    _require_columns(df, Y11, "Year 11")
    _require_columns(df, Y12, "Year 12")

    data = _stop_at_blank_week(df)

    def nonempty_block(frame: pd.DataFrame, subcols: list[str]) -> pd.DataFrame:
        out = frame[FIXEDCOL + subcols].copy()
        mask_all_empty = out[subcols].apply(lambda s: s.fillna("").astype(str).str.strip()).eq("").all(axis=1)
        return out.loc[~mask_all_empty]
    
    year11 = nonempty_block(data, Y11)
    year12 = nonempty_block(data, Y12)

    out_dir = Path(outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    year11.to_json(out_dir / "year11.json", orient="records", indent=2)
    year12.to_json(out_dir / "year12.json", orient="records", indent=2 )

    print("Json saved to:", out_dir.resolve())



def main():
    ap = argparse.ArgumentParser(description="")
    ap.add_argument("excel", help="")
    ap.add_argument("--outdir", default=".", help="Output directory")
    args = ap.parse_args()
    extract_sheet1_json(args.excel, args.outdir)

