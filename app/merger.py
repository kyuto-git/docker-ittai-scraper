import os
import glob
import pandas as pd
from typing import Dict, Tuple
from .utils import get_logger

ENC = "cp932"  # Shift-JIS

def read_all_inputs(input_dir: str) -> pd.DataFrame:
    """
    input/*.csv を全部読み込み、縦結合。重複行は残す（どの元ファイル出身かを残すため）。
    各行に _source_file 列を付与。
    """
    logger = get_logger()
    paths = sorted(glob.glob(os.path.join(input_dir, "*.csv")))
    if not paths:
        logger.warning("No input CSVs found.")
        return pd.DataFrame()

    dfs = []
    for p in paths:
        try:
            df = pd.read_csv(p, encoding=ENC)
            df["_source_file"] = os.path.basename(p)
            dfs.append(df)
            logger.info(f"Loaded: {p} ({len(df)} rows)")
        except Exception as e:
            logger.exception(f"Failed to read {p}: {e}")

    if not dfs:
        return pd.DataFrame()
    merged = pd.concat(dfs, ignore_index=True)
    return merged

def apply_indices(df_all: pd.DataFrame, mapping: Dict[str, float]) -> pd.DataFrame:
    """
    mapping: { match_key(14桁+2桁馬番) : 指数 }
    df_allのワーク1列を更新して返す（新規作成可）
    """
    if "ワーク1" not in df_all.columns:
        df_all["ワーク1"] = pd.NA

    cnt_match = 0
    updated = []
    for key, idx in mapping.items():
        mask = df_all["レースID(新)"].astype(str) == key
        n = mask.sum()
        if n:
            df_all.loc[mask, "ワーク1"] = idx
            cnt_match += int(n)
    get_logger().info(f"Applied indices: matched rows={cnt_match}")
    return df_all

def write_outputs(df_all: pd.DataFrame, output_dir: str):
    """
    (a) _merged.csv：元ファイル単位で出す
    (b) 日付S単位で レースID(新),ワーク1 のファイル：YYYYMMDD_ittai.csv
    """
    logger = get_logger()
    os.makedirs(output_dir, exist_ok=True)

    # (a) sourceごと
    for src, g in df_all.groupby("_source_file"):
        out = os.path.join(output_dir, os.path.splitext(src)[0] + "_merged.csv")
        try:
            g.to_csv(out, index=False, encoding=ENC)
            logger.info(f"Wrote merged: {out} ({len(g)} rows)")
        except Exception as e:
            logger.exception(f"Write failed: {out}: {e}")

    # (b) 日付ごと（軽量）
    if "日付S" in df_all.columns:
        small = df_all[["日付S", "レースID(新)", "ワーク1"]].copy()
        small = small.dropna(subset=["レースID(新)"])  # 必須
        small["日付S"] = small["日付S"].astype(str)
        for dt, g in small.groupby("日付S"):
            day = dt.replace("/", "").replace("-", "")
            fname = f"{day}_ittai.csv"
            out = os.path.join(output_dir, fname)
            try:
                g[["レースID(新)", "ワーク1"]].to_csv(out, index=False, encoding=ENC)
                logger.info(f"Wrote daily: {out} ({len(g)} rows)")
            except Exception as e:
                logger.exception(f"Write failed: {out}: {e}")
    else:
        logger.warning("Column 日付S not found – daily light files not written.")