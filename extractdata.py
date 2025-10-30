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

def _request_columns(df: pd.DataFrame, cols: list[str], label[str] ):
    pass

def extract_sheet1_json(xlsx_path: str, outdir: str = "."):
    pass

def main():
    ap = argparse.ArgumentParser(description="")
    ap.add_argument("excel", help="")
    ap.add_argument("--outdir", default=".", help="Output directory")
    args = ap.parse_args()
    extract_sheet1_json(args.excel, args.outdir)

