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
        conn.close()


def get_recent_weather(county_name=None, limit=20):
    """取得最近儲存的天氣紀錄（可選縣市過濾）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        if county_name:
            cur.execute("SELECT * FROM weather WHERE county=? ORDER BY id DESC LIMIT ?", (county_name, limit))
        else:
            cur.execute("SELECT * FROM weather ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_weather_details(county_name):
    """取得縣市詳細天氣資訊"""
    normalized_name = county_name.replace("台", "臺")
    
    params = {
        "Authorization": API_KEY,
        "LocationName": normalized_name
    }
    
    try:
        response = requests.get(API_URL, params=params, verify=False, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("success"):
            return None
        
        all_locations = data.get("records", {}).get("location", [])
        matching_locations = [loc for loc in all_locations if loc.get("locationName") == normalized_name]
        
        if not matching_locations:
            return None
        
        details = {
            "county": county_name,
            "locations": []
        }
        
        element_map = {
            "Wx": "天氣狀況",
            "PoP": "降水機率",
            "MaxT": "最高溫度",
            "MinT": "最低溫度",
            "CI": "舒適度",
            "Wind": "風力",
            "RH": "相對濕度"
        }
        
        for location in matching_locations:
            location_info = {
                "name": location.get("locationName"),
                "elements": {}
            }
            
            for element in location.get("weatherElement", []):
                element_code = element.get("elementName", "")
                element_name = element_map.get(element_code, element_code)
                times = element.get("time", [])
                
                location_info["elements"][element_name] = {
                    "code": element_code,
                    "data": []
                }
                
                for time_info in times:
                    start_time = time_info.get("startTime", "")
                    value = time_info.get("parameter", {}).get("parameterName", "N/A")
                    unit = time_info.get("parameter", {}).get("parameterUnit", "")
                    
                    if start_time:
                        location_info["elements"][element_name]["data"].append({
                            "time": start_time,
                            "value": value,
                            "unit": unit
                        })
            
            details["locations"].append(location_info)
        
        return details
    
    except Exception:
        return None


def parse_numeric_value(value_str):
    """嘗試將字符串轉換為數字"""
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return None


def create_temperature_chart(weather_data):
    """創建溫度圖表"""
    if not weather_data or not weather_data.get("locations"):
        return None
    
    location = weather_data["locations"][0]
    max_temps = location["elements"].get("最高溫度", {}).get("data", [])
    min_temps = location["elements"].get("最低溫度", {}).get("data", [])
    
    if not max_temps or not min_temps:
        return None
    
    dates = []
    max_values = []
    min_values = []
    
    for i in range(min(len(max_temps), len(min_temps), 10)):
        date = max_temps[i]["time"].split(" ")[0]
        max_val = parse_numeric_value(max_temps[i]["value"])
        min_val = parse_numeric_value(min_temps[i]["value"])
        
        if max_val is not None and min_val is not None:
            dates.append(date)
            max_values.append(max_val)
            min_values.append(min_val)
    
    if not dates:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=max_values,
        mode='lines+markers',
        name='最高溫度 (°C)',
        line=dict(color='red', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=min_values,
        mode='lines+markers',
        name='最低溫度 (°C)',
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        title="溫度預報趨勢",
        xaxis_title="日期",
        yaxis_title="溫度 (°C)",
        hovermode='x unified',
        height=400
    )
    
    return fig


def create_pop_chart(weather_data):
    """創建降水機率圖表"""
    if not weather_data or not weather_data.get("locations"):
        return None
    
    location = weather_data["locations"][0]
    pop_data = location["elements"].get("降水機率", {}).get("data", [])
    
    if not pop_data:
        return None
    
    dates = []
    values = []
    
    for i in range(min(len(pop_data), 10)):
        date = pop_data[i]["time"].split(" ")[0]
        val = parse_numeric_value(pop_data[i]["value"])
        
        if val is not None:
            dates.append(date)
            values.append(val)
    
    if not dates:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates, y=values,
        name='降水機率 (%)',
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title="降水機率預報",
        xaxis_title="日期",
        yaxis_title="降水機率 (%)",
        height=400
    )
    
    return fig


def create_weather_table(weather_data):
    """創建天氣預報表格"""
    if not weather_data or not weather_data.get("locations"):
        return None
    
    location = weather_data["locations"][0]
    elements = location.get("elements", {})
    
    data_list = []
    
    for i in range(10):
        row = {"日期": ""}
        
        if "天氣狀況" in elements:
            wx_data = elements["天氣狀況"].get("data", [])
            if i < len(wx_data):
                row["日期"] = wx_data[i]["time"].split(" ")[0]
                row["天氣"] = wx_data[i]["value"]
        
        if "最高溫度" in elements:
            max_t = elements["最高溫度"].get("data", [])
            if i < len(max_t):
                row["最高溫度"] = max_t[i]["value"] + " °C"
        
        if "最低溫度" in elements:
            min_t = elements["最低溫度"].get("data", [])
            if i < len(min_t):
                row["最低溫度"] = min_t[i]["value"] + " °C"
        
        if "降水機率" in elements:
            pop = elements["降水機率"].get("data", [])
            if i < len(pop):
                row["降水機率"] = pop[i]["value"] + " %"
        
        if "舒適度" in elements:
            ci = elements["舒適度"].get("data", [])
            if i < len(ci):
                row["舒適度"] = ci[i]["value"]
        
        if row.get("日期"):
            data_list.append(row)
    
    if data_list:
        return pd.DataFrame(data_list)
    
    return None


def main():
    st.set_page_config(page_title="天氣預報查詢系統", layout="wide")
    # 初始化資料庫
    init_db()
    st.title("🌤️ 中央氣象署天氣預報查詢系統")
    
    # 側邊欄輸入
    with st.sidebar:
        st.header("查詢設定")
        county_list = [
            "台北市", "新北市", "桃園市", "新竹市", "新竹縣",
            "苗栗縣", "台中市", "彰化縣", "南投縣", "雲林縣",
            "嘉義市", "嘉義縣", "台南市", "高雄市", "屏東縣",
            "宜蘭縣", "花蓮縣", "台東縣", "基隆市", "澎湖縣",
            "金門縣", "連江縣"
        ]
        
        selected_county = st.selectbox(
            "選擇縣市",
            options=county_list,
            help="選擇要查詢天氣的縣市"
        )
    
    # 主要內容區域
    if selected_county:
        st.write(f"正在查詢 **{selected_county}** 的天氣預報...")
        
        weather_data = get_weather_details(selected_county)
        
        if weather_data:
            st.success(f"✅ 成功取得 {selected_county} 的天氣資訊！")
            
            # 建立標籤頁（增加儲存紀錄分頁）
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 預報概覽", "🌡️ 溫度趨勢", "☔ 降水機率", "📋 詳細表格", "💾 儲存紀錄"])
            
            with tab1:
                st.subheader("預報摘要")
                location = weather_data["locations"][0]
                
                col1, col2, col3 = st.columns(3)
                
                # 當前天氣
                wx_data = location["elements"].get("天氣狀況", {}).get("data", [])
                if wx_data:
                    with col1:
                        st.metric("當前天氣", wx_data[0]["value"])
                
                # 最高溫度
                max_t = location["elements"].get("最高溫度", {}).get("data", [])
                if max_t:
                    with col2:
                        st.metric("最高溫度", max_t[0]["value"] + " °C")
                
                # 最低溫度
                min_t = location["elements"].get("最低溫度", {}).get("data", [])
                if min_t:
                    with col3:
                        st.metric("最低溫度", min_t[0]["value"] + " °C")
                
                # 舒適度
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                ci_data = location["elements"].get("舒適度", {}).get("data", [])
                if ci_data:
                    with col1:
                        st.info(f"**舒適度**: {ci_data[0]['value']}")
                
                pop_data = location["elements"].get("降水機率", {}).get("data", [])
                if pop_data:
                    with col2:
                        st.info(f"**降水機率**: {pop_data[0]['value']} %")
            
            with tab2:
                st.subheader("溫度預報趨勢")
                temp_chart = create_temperature_chart(weather_data)
                if temp_chart:
                    st.plotly_chart(temp_chart, width='stretch')
                else:
                    st.warning("無法生成溫度圖表")
            
            with tab3:
                st.subheader("降水機率預報")
                pop_chart = create_pop_chart(weather_data)
                if pop_chart:
                    st.plotly_chart(pop_chart, width='stretch')
                else:
                    st.warning("無法生成降水機率圖表")
            
            with tab4:
                st.subheader("詳細預報表格")
                weather_table = create_weather_table(weather_data)
                if weather_table is not None:
                    st.dataframe(weather_table, width='stretch')
                else:
                    st.warning("無法生成預報表格")
            
            with tab5:
                st.subheader("儲存紀錄（資料庫）")
                # 儲存本次查詢到資料庫
                try:
                    save_weather_to_db(selected_county, weather_data)
                    st.success("已將本次資料存入本機資料庫")
                except Exception as e:
                    st.error(f"儲存資料時發生錯誤: {e}")

                # 顯示最近的紀錄供檢視
                records = get_recent_weather(selected_county, limit=50)
                if records:
                    df_rec = pd.DataFrame([{"id": r['id'], "fetched_at": r['fetched_at'], "county": r['county']} for r in records])
                    st.table(df_rec)

                    rec_ids = [r['id'] for r in records]
                    sel_id = st.selectbox("選擇紀錄 ID 以檢視詳細資料", options=rec_ids)
                    sel_row = next((r for r in records if r['id'] == sel_id), None)
                    if sel_row:
                        try:
                            stored = json.loads(sel_row['data_json'])
                            st.json(stored)
                            st.markdown("---")
                            st.subheader("該紀錄的表格檢視")
                            tbl = create_weather_table(stored)
                            if tbl is not None:
                                st.dataframe(tbl, width='stretch')
                        except Exception as e:
                            st.error(f"載入紀錄錯誤: {e}")
                else:
                    st.info("目前沒有儲存的紀錄")
        
        else:
            st.error(f"❌ 無法取得 {selected_county} 的天氣資訊，請稍後再試")


if __name__ == "__main__":
    main()
