# crawler_weather

中央氣象署天氣資料爬蟲與 Streamlit Demo

## 內容
- `weather_scraper.py`: 命令列爬蟲腳本，支援輸入縣市並顯示多項天氣資訊。
- `weather_app.py`: Streamlit 應用，提供互動式 UI、圖表與表格來視覺化縣市天氣預報。
- `requirements.txt`: 程式所需 Python 套件。

## 快速開始
1. （建議）建立虛擬環境並啟用：

```powershell
cd "c:\Users\user\Desktop\新增資料夾"
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. 安裝相依套件：

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3. 以命令列執行爬蟲（非 GUI）：

```powershell
python weather_scraper.py
```

4. 啟動 Streamlit Demo（在瀏覽器檢視）：

```powershell
streamlit run "c:\Users\user\Desktop\新增資料夾\weather_app.py"
```

啟動後，開啟 `http://localhost:8501` 即可看見應用畫面。

## 功能說明
- 自動將輸入的 `台` 轉成 `臺` 以配合中央氣象署 API 的資料格式。
- 擷取各區 `天氣狀況`、`降水機率`、`最高溫度`、`最低溫度`、`舒適度` 等元素。
- Streamlit App 提供：
  - 預報摘要 (當前天氣、最高/最低溫)
  - 溫度趨勢圖（Plotly）
  - 降水機率長條圖（Plotly）
  - 詳細預報表格（Pandas DataFrame）

## 注意事項與安全
- 本程式在發出 API 請求時暫時設定 `verify=False` 來避免本地 SSL 憑證問題（開發/測試用途）。若部署在生產環境，請移除 `verify=False` 並使用有效憑證。
- 目前使用的 API KEY 已內嵌於程式（你提供的 KEY）。若公開此專案，建議改用環境變數或 GitHub Secrets 管理 API KEY。

## 推薦改進
- 把 API KEY 放到環境變數（`os.environ`）或使用 `.env` 與 `python-dotenv`。
- 增加快取或頻率限制以避免頻繁請求 API。
- 增加更多圖表（例如濕度、風向）與導出 CSV 功能。

## 聯絡
若需要我把 repo 推到遠端（GitHub），請確保本機有設定好 Git 認證（例如 GitHub CLI 或 Credential Manager），我會嘗試推送，若失敗請按照終端給的錯誤提示補充認證設定。
