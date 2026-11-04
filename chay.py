"""Chạy toàn bộ: crawl dữ liệu mới -> làm sạch 7 bước -> phân tích (Chương 2–5).

    python chay.py

Chạy lại mỗi ngày để tăng mẫu (chỉ tải tin mới, không trùng tin cũ).
Xem kết quả trên web: bấm ▶ Run file web/app.py trong VS Code, hoặc  python web/app.py
"""
import importlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
importlib.import_module("1_crawl").main()
importlib.import_module("2_lam_sach").main()
importlib.import_module("4_phan_tich").main()
