import streamlit as st
import requests
import json
import urllib3
import pandas as pd
from datetime import datetime
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API 配置
API_KEY = "CWA-118F0D40-7F13-4BA2-B316-CC5767CA0CC6"
API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

# SQLite DB 路徑
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def init_db():
    """初始化 SQLite 資料庫與表格"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                county TEXT,
                normalized_name TEXT,
                fetched_at TEXT,
                data_json TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_weather_to_db(county_name, details):
    """將抓到的天氣資料存入 SQLite"""
    if not details:
        return
    normalized = county_name.replace("台", "臺")
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO weather (county, normalized_name, fetched_at, data_json) VALUES (?, ?, ?, ?)",
            (county_name, normalized, datetime.now().isoformat(), json.dumps(details, ensure_ascii=False))
        )
        conn.commit()
    finally:
        """
        此檔案已移動到 `weather_streamlit.py`。

        為了保持相容性，請改用 `weather_streamlit.py` 來啟動 Streamlit 應用。
        舊檔案保留為跳轉說明，以免破壞既有腳本引用。
        """

        import sys

        print("此檔案已移至 'weather_streamlit.py'。請改用該檔案啟動 Streamlit 應用。")
        sys.exit(0)
        else:
