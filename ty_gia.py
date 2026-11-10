"""Tỷ giá CHUYỂN KHOẢN của Vietcombank theo TỪNG NGÀY, lưu ở data/ty_gia.csv.

Nguyên tắc: tin lương ngoại tệ được đổi theo tỷ giá của NGÀY TIN ĐÓ ĐƯỢC THU THẬP (crawl_date),
không phải tỷ giá lúc chạy làm sạch. Dùng ngày thu thập vì CareerViet không ghi ngày đăng.

- 1_crawl.py ghi tỷ giá của hôm thu thập vào file (mỗi ngày 1 lần, ngày đã có thì bỏ qua).
- 2_lam_sach.py đọc file; ngày nào còn thiếu thì thử tải tỷ giá lịch sử của đúng ngày đó
  (Vietcombank cho tra theo ngày). Không có mạng thì dùng ngày gần nhất và đánh dấu là ước lượng.

Chạy riêng `python ty_gia.py` để bổ sung tỷ giá cho mọi ngày đã thu thập trong data/raw.
"""
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

FILE = Path(__file__).parent / "data" / "ty_gia.csv"
API = "https://www.vietcombank.com.vn/api/exchangerates?date={ngay}"     # tỷ giá cuối ngày, tra theo ngày
USER_AGENT = "PTDL-Nhom3-StudentResearch/1.0 (Van Lang University; academic project)"
COT = ["ngay", "ma", "ty_gia", "lay_luc"]


def tai_ngay(ngay: str) -> dict[str, float]:
    """Tỷ giá chuyển khoản của 1 ngày 'YYYY-MM-DD' -> {'USD': 25720.0, 'EUR': ...}."""
    r = requests.get(API.format(ngay=ngay), timeout=30, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    j = r.json()
    if not str(j.get("Date", "")).startswith(ngay):
        raise ValueError(f"Vietcombank trả tỷ giá của ngày khác ({j.get('Date')})")
    out = {}
    for x in j.get("Data") or []:
        try:
            v = float(x["transfer"])
        except (KeyError, TypeError, ValueError):
            continue
        if v > 0:
            out[x["currencyCode"]] = v
    if "USD" not in out:
        raise ValueError("không có tỷ giá USD")
    return out


def doc() -> dict[str, dict[str, float]]:
    """data/ty_gia.csv -> {'2026-10-13': {'USD': 25720.0, ...}, ...}"""
    bang: dict[str, dict[str, float]] = {}
    if FILE.exists():
        with open(FILE, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                bang.setdefault(r["ngay"], {})[r["ma"]] = float(r["ty_gia"])
    return bang


def bo_sung(cac_ngay) -> list[str]:
    """Tải và ghi thêm tỷ giá cho các ngày CHƯA có trong file. Ngày đã có thì không tải lại.
    Lỗi mạng ở ngày nào thì báo rồi bỏ qua ngày đó. Trả về danh sách ngày vừa thêm."""
    hom_nay = f"{datetime.now():%Y-%m-%d}"
    thieu = sorted(d for d in set(map(str, cac_ngay)) - set(doc()) if d <= hom_nay)
    them = []
    for i, ngay in enumerate(thieu):
        if i:
            time.sleep(1)                       # hỏi lần lượt, không dồn dập
        try:
            tg = tai_ngay(ngay)
        except requests.RequestException as e:
            print(f"  Chưa lấy được tỷ giá ngày {ngay}: không kết nối được Vietcombank ({type(e).__name__})")
            continue
        except ValueError as e:
            print(f"  Chưa lấy được tỷ giá ngày {ngay}: {e}")
            continue
        moi = not FILE.exists()
        FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FILE, "a", newline="", encoding="utf-8-sig" if moi else "utf-8") as f:
            w = csv.writer(f)
            if moi:
                w.writerow(COT)
            luc = f"{datetime.now():%Y-%m-%d %H:%M}"
            w.writerows([ngay, ma, f"{v:g}", luc] for ma, v in sorted(tg.items()))
        them.append(ngay)
    return them


def chon(bang: dict, ngay: str, ma: str) -> tuple[str | None, bool]:
    """Ngày tỷ giá dùng cho tin thu thập ngày `ngay`, loại tiền `ma` -> (ngày dùng, có phải ước lượng).
    Đúng ngày nếu có; thiếu thì ngày gần nhất TRƯỚC đó, không có nữa thì ngày gần nhất SAU đó."""
    co = sorted(d for d, tg in bang.items() if ma in tg)
    if ngay in co:
        return ngay, False
    truoc = [d for d in co if d < ngay]
    if truoc:
        return truoc[-1], True
    return (co[0], True) if co else (None, True)


# Tự kiểm tra cách chọn ngày (chạy mỗi lần import)
_B = {"2026-10-13": {"USD": 25720.0}, "2026-11-10": {"USD": 25410.0}}
assert chon(_B, "2026-10-13", "USD") == ("2026-10-13", False)
assert chon(_B, "2026-11-03", "USD") == ("2026-10-13", True)
assert chon(_B, "2026-10-01", "USD") == ("2026-10-13", True)
assert chon(_B, "2026-11-03", "EUR") == (None, True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raw = Path(__file__).parent / "data" / "raw"
    ngay = {f.stem[-10:] for f in raw.glob("*_????-??-??.csv")} | {f"{datetime.now():%Y-%m-%d}"}
    print("Đã thêm tỷ giá các ngày:", bo_sung(ngay) or "không có ngày nào thiếu")
    for d, tg in sorted(doc().items()):
        print(f"  {d}: 1 USD = {tg['USD']:,.0f} đ")
