import requests
import json
from datetime import datetime
import urllib3
import sqlite3
import os

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API 配置
API_KEY = "CWA-118F0D40-7F13-4BA2-B316-CC5767CA0CC6"
API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"


# SQLite DB 路徑
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def init_db():
    """初始化 SQLite 資料庫與表格（若不存在則建立）"""
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


def save_weather_to_db(weather_details):
    """將查詢結果存入資料庫（會新增一筆紀錄）

    Args:
        weather_details (dict): 與 `get_weather_details` 相同的結構
    """
    if not weather_details:
        return

    county_name = weather_details.get("county")
    normalized = county_name.replace("台", "臺") if county_name else None

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO weather (county, normalized_name, fetched_at, data_json) VALUES (?, ?, ?, ?)",
            (
                county_name,
                normalized,
                datetime.now().isoformat(),
                json.dumps(weather_details, ensure_ascii=False)
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_weather_details(county_name):
    """
    取得縣市的詳細天氣資訊並轉換為結構化資料
    
    Args:
        county_name (str): 縣市名稱
    
    Returns:
        dict: 包含所有氣象元素的詳細資料
    """
    # 標準化輸入 (台 -> 臺)
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
        
        # 提取和組織所有數據
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
    
    except requests.exceptions.RequestException:
        return None
    except json.JSONDecodeError:
        return None


def display_weather_details(weather_data):
    """
    顯示詳細天氣預報資訊
    
    Args:
        weather_data (dict): 詳細天氣預報資料
    """
    if not weather_data:
        return
    
    county_name = weather_data.get("county", "未知位置")
    print(f"\n========== {county_name} 天氣預報 ==========")
    
    for location in weather_data.get("locations", []):
        area_name = location.get("name", "未知區域")
        print(f"\n【 {area_name} 】")
        
        elements = location.get("elements", {})
        
        for element_name, element_info in elements.items():
            print(f"\n  {element_name}:")
            data = element_info.get("data", [])
            
            for time_data in data[:6]:  # 顯示前6筆
                time_str = time_data.get("time", "").split(" ")[0]
                value = time_data.get("value", "N/A")
                unit = time_data.get("unit", "")
                
                if time_str:
                    if unit:
                        print(f"    {time_str}: {value} {unit}")
                    else:
                        print(f"    {time_str}: {value}")


def main():
    """主程式"""
    print("=" * 50)
    print("中央氣象署天氣預報查詢系統")
    print("=" * 50)
    # 初始化資料庫（若不存在則建立）
    init_db()
    
    while True:
        county = input("\n請輸入縣市名稱 (例如: 台北市、台中市、高雄市，或輸入 'quit' 結束): ").strip()
        
        if county.lower() in ['quit', 'q', '結束']:
            print("程式結束，再見！")
            break
        
        if not county:
            print("縣市名稱不能為空，請重新輸入")
            continue
        
        print(f"正在查詢 {county} 的天氣預報...")
        weather = get_weather_details(county)
        
        if weather:
            display_weather_details(weather)
            # 儲存本次查詢結果到本機資料庫（每次查詢皆新增一筆）
            try:
                save_weather_to_db(weather)
                print("已將本次查詢結果儲存至 data.db")
            except Exception as e:
                print(f"儲存資料時發生錯誤: {e}")
        else:
            print(f"找不到 {county} 的天氣資訊")
        
        another = input("\n是否繼續查詢? (y/n): ").strip().lower()
        if another not in ['y', 'yes', '是']:
            print("程式結束，再見！")
            break


if __name__ == "__main__":
    main()
