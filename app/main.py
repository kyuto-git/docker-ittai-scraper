import pandas as pd
from app.utils import get_logger, sleep_delay, get_html
from app.scraper import parse_ittai_result
from app.merger import read_all_inputs, apply_indices, write_outputs

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"
BASE_URL = "https://ittai.net/RK/race_index.php?type=result&id={}&mode=1"

def build_fetch_plan(df_all: pd.DataFrame):
    """レースID(新)の先頭16桁からURLを生成"""
    s = df_all["レースID(新)"].astype(str)
    base16 = s.str.slice(0, 16)
    uniq = sorted(set(base16))
    return {bid: BASE_URL.format(bid) for bid in uniq if len(bid) == 16 and bid.isdigit()}

def main():
    logger = get_logger()
    logger.info("=== Ittai scraper started ===")

    df_all = read_all_inputs(INPUT_DIR)
    if df_all.empty:
        logger.error("No input data. Exiting.")
        return

    plan = build_fetch_plan(df_all)
    logger.info(f"Unique race pages to fetch: {len(plan)}")

    mapping = {}

    for bid16, url in plan.items():
        html = get_html(url, logger)
        if not html:
            logger.warning(f"Skip (no HTML): {url}")
            sleep_delay()
            continue

        pairs = parse_ittai_result(html)
        if not pairs:
            logger.warning(f"No rows parsed: {url}")
            sleep_delay()
            continue

        # ✅ 1〜16桁 + 馬番(2桁ゼロ埋め) = 18桁キー
        for uma_num, (_name, idx) in pairs.items():
            match_key = bid16 + uma_num.zfill(2)
            mapping[match_key] = idx

        logger.info(f"Parsed {len(pairs)} horses from {bid16}")
        sleep_delay()

    df_all = apply_indices(df_all, mapping)
    write_outputs(df_all, OUTPUT_DIR)

    total_rows = len(df_all)
    filled = df_all["ワーク1"].notna().sum() if "ワーク1" in df_all.columns else 0
    logger.info(f"Summary: rows={total_rows}, filled ワーク1={filled}")
    logger.info("=== Ittai scraper finished ===")

if __name__ == "__main__":
    main()