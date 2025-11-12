from pathlib import Path
import pandas as pd

FIXEDCOL = ["Week", "Day", "Date", "Events"]

Y11 = ["11 - Class", "11 - Task Name", "11 - Weighting", "11 - Task Type", "11 - Other Notes"]
Y12 = ["12 - Class", "12 - Task Name", "12 - Weighting", "12 - Task Type", "12 - Other Notes"]

def _find_header_row(raw: pd.DataFrame, max_scan: int = 20) -> int:
    target = [c.lower() for c in FIXEDCOL]
    nrows = min(max_scan, len(raw))
    for i in range(nrows):
        row = raw.iloc[i].fillna("")
        probe = [str(row.get(j, "")).strip().lower() for j in range(4)]
        if probe == target:
            return i
    return 0

def fillOutFixedColdata(df: pd.DataFrame):

    for col in FIXEDCOL:
        for row in col:
            if row != None:
                lastVal = row

            else:
                row = lastVal
                

    print(df)
    return df

def _require_columns(df: pd.DataFrame, cols: list[str], label: str ):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing {label} columns: {missing}")
    
def _checkForTempValue(df: pd.DataFrame, cols: list[str] ) -> pd.DataFrame:

    className = cols[0]

    keep_rows = df[df[className] != "Select Class"]
    
    return pd.DataFrame(keep_rows)


def extract_sheet1_json(xlsx_path: str, outdir: str = "."):
    raw = pd.read_excel(xlsx_path, sheet_name="Sheet1", header=None, dtype=str)
    hdr = _find_header_row(raw)
    df = pd.read_excel(xlsx_path, sheet_name="Sheet1", header=hdr, dtype=str)

    _require_columns(df, FIXEDCOL, "fixed")
    _require_columns(df, Y11, "Year 11")
    _require_columns(df, Y12, "Year 12")

    df = fillOutFixedColdata(df)

    #data = _stop_at_blank_week(df)
    data11 = _checkForTempValue(df,Y11)
    data12 = _checkForTempValue(df,Y12)

    def nonempty_block(frame: pd.DataFrame, subcols: list[str]) -> pd.DataFrame:
        out = frame[FIXEDCOL + subcols].copy()
        mask_all_empty = out[subcols].apply(lambda s: s.fillna("").astype(str).str.strip()).eq("").all(axis=1)
        return out.loc[~mask_all_empty]
    
    data11 = nonempty_block(data11, Y11)
    data12 = nonempty_block(data12, Y12)

    out_dir = Path(outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data11.to_json(out_dir / "year11.json", orient="records", indent=2)
    data12.to_json(out_dir / "year12.json", orient="records", indent=2 )

    print("Json saved to:", out_dir.resolve())


