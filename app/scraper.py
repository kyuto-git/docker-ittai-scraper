from bs4 import BeautifulSoup
from typing import Dict, Tuple, Optional

def parse_ittai_result(html: str) -> Dict[str, Tuple[str, float]]:
    """
    成績テーブルから 馬番→(馬名, 指数) を抽出
    return: { "01": ("ラージギャラリー", 66.0), ... }  # 馬番は2桁ゼロ埋め
    """
    soup = BeautifulSoup(html, "lxml")

    # 指数列のある成績テーブルを特定（ヘッダに「指数」を含むもの）
    target_table = None
    for tbl in soup.find_all("table"):
        ths = [th.get_text(strip=True) for th in tbl.find_all("th")]
        if ths and "指数" in ths:
            target_table = tbl
            break
    if target_table is None:
        return {}

    rows = target_table.find_all("tr")
    result = {}
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue

        # 馬番：第2列（<span class="badge ...">X</span>）の内部テキスト
        try:
            num_cell = tds[1]
            num_text = num_cell.get_text(strip=True)
            if not num_text:
                continue
            uma_num = f"{int(num_text):02d}"
        except Exception:
            continue

        # 馬名：第4列の<a>テキスト
        name_cell = tds[3]
        a = name_cell.find("a")
        uma_name = a.get_text(strip=True) if a else name_cell.get_text(strip=True)

        # 指数：最終列の<strong>数値</strong>
        idx_cell = tds[-1]
        strong = idx_cell.find("strong")
        if strong is None:
            continue
        idx_text = strong.get_text(strip=True).replace(",", "")
        try:
            idx_val = float(idx_text)
        except ValueError:
            continue

        result[uma_num] = (uma_name, idx_val)

    return result