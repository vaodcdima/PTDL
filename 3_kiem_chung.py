"""BƯỚC 3 (tùy chọn) — Kiểm chứng: mở lại ngẫu nhiên 15 tin từ link gốc,
đối chiếu tên việc + tên công ty với dữ liệu đã lưu.

    python 3_kiem_chung.py

Tin hết hạn thường bị trang gốc gỡ nội dung -> tính riêng là "ĐÃ GỠ", không tính là dữ liệu sai.
"""
import importlib
import sys

import pandas as pd
from bs4 import BeautifulSoup

crawl = importlib.import_module("1_crawl")
lam_sach = importlib.import_module("2_lam_sach")


def main(n: int = 15) -> None:
    newest = max(lam_sach.CLEAN_DIR.glob("jobs_clean_*.csv"))   # file sạch của ngày gần nhất
    print(f"Kiểm chứng từ file {newest.name}")
    df = pd.read_csv(newest, dtype=str)
    sample = df.sample(min(n, len(df)))
    khop = da_go = 0
    for _, r in sample.iterrows():
        html = crawl.get(r["url"])
        jp = crawl.jobposting(BeautifulSoup(html, "html.parser")) if html else {}
        if not jp:
            da_go += 1
            print("  ĐÃ GỠ  " + r["title"][:60])
            continue
        org = jp.get("hiringOrganization") or {}
        cong_ty = org.get("name") if isinstance(org, dict) else org
        match = (lam_sach.bo_dau(jp.get("title")) == lam_sach.bo_dau(r["title"])
                 and lam_sach.bo_dau(cong_ty) == lam_sach.bo_dau(r["company"]))
        khop += match
        print(("  KHỚP   " if match else "  LỆCH   ") + r["title"][:60])
    con_mo = len(sample) - da_go
    print(f"\nKiểm chứng {len(sample)} tin: {khop}/{con_mo} tin còn mở khớp với trang gốc, {da_go} tin đã bị gỡ.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
