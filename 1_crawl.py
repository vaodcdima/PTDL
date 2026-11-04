"""BƯỚC 1 — Crawl tin tuyển dụng thực tập / part-time từ 2 trang công khai.

    Nguồn 1: CareerViet  https://careerviet.vn
    Nguồn 2: JobOKO      https://vn.joboko.com

Kết quả: data/raw/careerviet_<YYYY-MM-DD>.csv, data/raw/joboko_<YYYY-MM-DD>.csv
    - Mỗi ngày chạy ra 1 file riêng mang ngày hôm đó (không ghi dồn vào 1 file).
    - Mỗi dòng là 1 tin, có cột `url` = link tin gốc để kiểm chứng.
    - Chỉ tải tin MỚI: tin đã có ở các ngày trước được bỏ qua, không trùng.

Nguyên tắc (slide 6): chỉ lấy thông tin công khai, kiểm tra robots.txt trước mỗi URL,
nghỉ ~1,5 giây giữa 2 lượt truy cập, không vượt rào chống bot.
"""
import csv
import json
import math
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

# ============================== CẤU HÌNH ==============================
MAX_PAGES = 20            # số trang danh sách tối đa cho mỗi từ khóa / trang
MAX_NEW_DETAILS = 800     # số tin MỚI tối đa tải chi tiết mỗi nguồn / lần chạy
DELAY = 1.5               # giây nghỉ giữa 2 request
USER_AGENT = "PTDL-Nhom3-StudentResearch/1.0 (Van Lang University; academic project; respects robots.txt)"

CAREERVIET_KEYWORDS = ["thuc-tap", "thuc-tap-sinh", "intern", "part-time", "ban-thoi-gian"]
JOBOKO_URLS = [
    "https://vn.joboko.com/tim-viec-lam-thuc-tap",
    "https://vn.joboko.com/viec-lam-part-time-thuc-tap",
    "https://vn.joboko.com/viec-lam-nganh-lam-ban-thoi-gian-xni38",
    "https://vn.joboko.com/viec-lam-nganh-sinh-vien-lam-them-xni60",
]
RAW_DIR = Path(__file__).parent / "data" / "raw"
COLUMNS = ["source", "job_id", "title", "company",                      # tin
           "salary_text", "location_text", "country",                  # lương, địa điểm (nguyên văn)
           "employment_type", "hinh_thuc", "industry", "experience",   # loại hình, ngành, kinh nghiệm
           "date_posted", "deadline",                                  # thời gian (YYYY-MM-DD)
           "query", "url", "crawled_at"]                               # truy vết
# ======================================================================

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "vi-VN,vi;q=0.9"})
_robots: dict = {}
_last_request = 0.0


def clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def to_date(text) -> str:
    """'2026-09-14T11:12:49Z' hoặc '14/10/2026' -> '2026-09-14' (cùng 1 định dạng)."""
    s = clean(text)
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else ""


# ----------------------------------------------------------- robots.txt
def robots_rules(host: str) -> list:
    """Đọc robots.txt (nhóm User-agent: *), hỗ trợ ký tự * và $."""
    if host not in _robots:
        try:
            text = session.get(host + "/robots.txt", timeout=30).text
        except requests.RequestException:
            text = ""
        rules, active, prev_ua = [], False, False
        for line in text.splitlines():
            line = line.split("#")[0].strip()
            if ":" not in line:
                continue
            key, value = (x.strip() for x in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                active = (active and prev_ua) or value == "*"
                prev_ua = True
                continue
            prev_ua = False
            if active and key in ("allow", "disallow") and value:
                regex = "^" + ".*".join(map(re.escape, value.rstrip("$").split("*")))
                rules.append((len(value), key == "allow", re.compile(regex + ("$" if value.endswith("$") else ""))))
        _robots[host] = rules
        print(f"  Đã đọc {host}/robots.txt ({len(rules)} luật)")
    return _robots[host]


def allowed(url: str) -> bool:
    p = urlsplit(url)
    path = (p.path or "/") + (f"?{p.query}" if p.query else "")
    matches = [(n, allow) for n, allow, rx in robots_rules(f"{p.scheme}://{p.netloc}") if rx.match(path)]
    return max(matches)[1] if matches else True   # luật dài nhất thắng


def get(url: str) -> str | None:
    """Tải 1 trang: kiểm robots.txt, nghỉ giữa các request, thử lại tối đa 3 lần."""
    global _last_request
    if not allowed(url):
        print("  robots.txt KHÔNG cho phép, bỏ qua:", url)
        return None
    for attempt in range(3):
        wait = DELAY + random.random() * 0.5 - (time.time() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.time()
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                return r.content.decode("utf-8", errors="replace")
            if r.status_code not in (429, 500, 502, 503, 504):
                return None
        except requests.RequestException:
            pass
        time.sleep(5 * (attempt + 1))
    return None


# ----------------------------------------------------------- trang danh sách
def careerviet_listing(max_pages: int):
    for kw in CAREERVIET_KEYWORDS:
        last_page, page = max_pages, 1
        while page <= last_page:
            url = (f"https://careerviet.vn/viec-lam/{kw}-k-vi.html" if page == 1 else
                   f"https://careerviet.vn/viec-lam/{kw}-k-trang-{page}-vi.html")
            html = get(url)
            if not html:
                break
            if page == 1:
                m = re.search(r'\\?"totalJobs\\?"\s*:\s*(\d+)', html)
                if m:
                    last_page = min(max_pages, math.ceil(int(m.group(1)) / 50))
                    print(f"  CareerViet '{kw}': {m.group(1)} tin -> đọc {last_page} trang")
            items = BeautifulSoup(html, "html.parser").select("div.job-item")
            if not items:
                break
            for it in items:
                a = it.select_one("h2 a.job_link") or it.select_one("a.job_link")
                if not a or not a.get("data-id"):
                    continue
                comp, sal = it.select_one("a.company-name"), it.select_one(".salary")
                yield {
                    "job_id": a["data-id"], "url": urljoin("https://careerviet.vn", a["href"]),
                    "title": clean(a.get("title") or a.text), "company": clean(comp.text if comp else ""),
                    "salary_text": clean(sal.text if sal else ""),
                    "location_text": ", ".join(clean(li.text) for li in it.select(".location li")),
                    "tags": "", "query": kw,
                }
            page += 1


def joboko_listing(max_pages: int):
    for start in JOBOKO_URLS:
        url, page = start, 1
        while url and page <= max_pages:
            html = get(url)
            if not html:
                break
            soup = BeautifulSoup(html, "html.parser")
            found = {}
            for a in soup.find_all("a", href=True):
                href = a["href"].split("?")[0]
                m = re.search(r"-xvi(\d+)$", href)
                title = clean(a.get("title") or a.text)
                if not m or not title or m.group(1) in found:
                    continue
                box = a.find_parent(class_=["item-content", "item"]) or a.parent
                comp = box.select_one("a[href*='-xci']")
                pick = lambda sel: clean(box.select_one(sel).text) if box.select_one(sel) else ""
                found[m.group(1)] = {
                    "job_id": m.group(1), "url": urljoin("https://vn.joboko.com", href), "title": title,
                    "company": clean(comp.get("title") or comp.text) if comp else "",
                    "salary_text": pick(".item-salary"), "location_text": pick(".item-city"),
                    "tags": " | ".join(clean(t.text) for t in box.select(".item-tag")),
                    "query": start.rsplit("/", 1)[-1],
                }
            if not found:
                break
            yield from found.values()
            nxt = soup.find("a", href=re.compile(rf"[?&]p={page + 1}\b"))
            url = urljoin("https://vn.joboko.com", nxt["href"]) if nxt else None
            page += 1
        print(f"  JobOKO {start}: đọc {page - 1} trang")


# ----------------------------------------------------------- trang chi tiết
def jobposting(soup) -> dict:
    """Dữ liệu cấu trúc schema.org/JobPosting mà trang web nhúng sẵn (JSON-LD)."""
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "", strict=False)
        except ValueError:
            continue
        for obj in data if isinstance(data, list) else [data]:
            if isinstance(obj, dict) and obj.get("@type") == "JobPosting":
                return obj
    return {}


def info_boxes(soup) -> dict:
    """Các ô 'Nhãn: giá trị' trên trang chi tiết (Lương, Hình thức, Kinh nghiệm...)."""
    info = {}
    for li in soup.select(".detail-box li"):                                   # CareerViet
        parts = [clean(s) for s in li.stripped_strings if clean(s) not in ("", ",")]
        if len(parts) >= 2:
            info.setdefault(parts[0].rstrip(":"), ", ".join(parts[1:]))
    for it in soup.select(".int-job-info-box .item-content"):                  # JobOKO
        lb, val = it.select_one(".item-label"), it.select_one(".item-text")
        if lb and val:
            info.setdefault(clean(lb.text).rstrip(":"), clean(val.text))
    h1 = soup.find("h1")                                                       # JobOKO: đầu trang
    if h1 and h1.parent:
        for s in map(clean, h1.parent.stripped_strings):
            low = s.lower()
            if len(s) > 60:
                continue
            if "kinh nghiệm" in low:
                info.setdefault("Kinh nghiệm", s)
            elif re.search(r"triệu|thỏa thuận|thoả thuận|cạnh tranh|usd|vnđ", low):
                info.setdefault("Mức lương", s)
    return info


def parse_detail(source: str, row: dict, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    jp, info = jobposting(soup), info_boxes(soup)
    places = jp.get("jobLocation") or []
    places = places if isinstance(places, list) else [places]
    addrs = [p.get("address", {}) for p in places if isinstance(p, dict)]
    regions = [clean(a.get("addressRegion")) for a in addrs if isinstance(a, dict) and a.get("addressRegion")]
    country = next((a.get("addressCountry") for a in addrs if isinstance(a, dict) and a.get("addressCountry")), "")
    org = jp.get("hiringOrganization") or {}
    sal = (jp.get("baseSalary") or {}).get("value") or {}
    sal_json = sal.get("value") if isinstance(sal, dict) else sal
    if isinstance(sal, dict) and sal.get("minValue"):
        sal_json = f"{sal['minValue'] / 1e6:g} - {(sal.get('maxValue') or sal['minValue']) / 1e6:g} triệu"
    emp = jp.get("employmentType") or []
    emp = emp if isinstance(emp, list) else [emp]
    salary = info.get("Lương") or info.get("Mức lương") or row["salary_text"] or clean(sal_json)
    return {
        "source": source,
        "job_id": row["job_id"],
        "title": clean(jp.get("title")) or row["title"],
        "company": clean(org.get("name") if isinstance(org, dict) else org) or row["company"],
        "salary_text": re.sub(r"^Lương:\s*", "", clean(salary)),   # bỏ chữ "Lương:" thừa
        # Trang danh sách ghi cấp tỉnh; JSON-LD đôi khi ghi cấp huyện -> ưu tiên danh sách
        "location_text": row["location_text"] or info.get("Địa điểm làm việc") or ", ".join(regions),
        "country": clean(country).upper(),
        "employment_type": ", ".join(clean(e).strip('"').upper() for e in emp),
        "hinh_thuc": clean(info.get("Hình thức") or info.get("Hình thức làm việc", "")).replace(" ,", ","),
        "industry": clean(jp.get("industry")) or info.get("Ngành nghề", ""),
        "experience": info.get("Kinh nghiệm", ""),
        "date_posted": to_date(jp.get("datePosted")),
        "deadline": to_date(jp.get("validThrough")) or to_date(info.get("Hết hạn nộp") or info.get("Hạn nộp hồ sơ")),
        "query": row["query"],
        "url": row["url"],
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ----------------------------------------------------------- chạy
TARGET_WORDS = re.compile(r"thực tập|intern|part.?time|bán thời gian|làm thêm|sinh viên", re.I)


def crawl_source(source: str, listing, max_details: int) -> None:
    # Mỗi ngày 1 file riêng: data/raw/<nguồn>_<YYYY-MM-DD>.csv (chỉ chứa tin MỚI lấy trong ngày)
    path = RAW_DIR / f"{source}_{datetime.now():%Y-%m-%d}.csv"
    seen = set()
    for old in RAW_DIR.glob(f"{source}_*.csv"):     # tin đã có ở MỌI ngày trước -> bỏ qua
        with open(old, encoding="utf-8-sig") as f:
            seen |= {r["job_id"] for r in csv.DictReader(f)}

    jobs = {}
    for r in listing:
        jobs.setdefault(r["job_id"], r)
    new = [r for r in jobs.values() if r["job_id"] not in seen]
    # JobOKO có tag trên trang danh sách: tin có tag nhưng không liên quan thực tập/part-time -> bỏ qua
    new = [r for r in new if not r["tags"] or TARGET_WORDS.search(r["title"] + r["tags"])][:max_details]
    print(f"  {source}: {len(jobs)} tin trên trang danh sách, {len(seen)} tin đã có, tải chi tiết {len(new)} tin mới")

    is_new_file = not path.exists()
    with open(path, "a", newline="", encoding="utf-8-sig" if is_new_file else "utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if is_new_file:
            writer.writeheader()
        saved = 0
        for i, r in enumerate(new, 1):
            html = get(r["url"])
            if html:
                writer.writerow(parse_detail(source, r, html))
                f.flush()   # Ctrl+C giữa chừng vẫn giữ phần đã tải
                saved += 1
            if i % 20 == 0 or i == len(new):
                print(f"    {i}/{len(new)} tin")
    print(f"  -> Đã lưu {saved} tin mới vào {path}")


def main(max_pages: int = MAX_PAGES, max_details: int = MAX_NEW_DETAILS) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60, "\nBƯỚC 1: CRAWL DỮ LIỆU\n" + "=" * 60)
    print("[1/2] CareerViet")
    crawl_source("careerviet", careerviet_listing(max_pages), max_details)
    print("[2/2] JobOKO")
    crawl_source("joboko", joboko_listing(max_pages), max_details)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
