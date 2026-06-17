import random
from flask import Flask, jsonify, render_template, request
import pandas as pd

app = Flask(__name__)

# 直接讀取 Excel 檔案，完全不用理會 CSV 亂碼與編碼崩潰問題
df = pd.read_excel("data.xlsx")

# 強迫清理欄位與內容的隱形空格
df.columns = df.columns.str.strip()
df["餐廳名稱"] = df["餐廳名稱"].astype(str).str.strip()
df["價格區間"] = df["價格區間"].astype(str).str.strip()


@app.route("/")
def index():
  # 抓取清理後的不重複價格區間
  budgets = df["價格區間"].dropna().unique().tolist()
  budgets = [b for b in budgets if b != "nan" and b != "None"]
  return render_template("index.html", budgets=budgets)


@app.route("/get_restaurants", methods=["POST"])
def get_restaurants():
  data = request.get_json()
  selected_budget = data.get("budget")

  filtered_df = df.copy()

  # 根據預算篩選
  if selected_budget and selected_budget != "all":
    filtered_df = filtered_df[filtered_df["價格區間"] == selected_budget]

  if filtered_df.empty:
    return jsonify({"status": "empty", "restaurants": []})

  # 把資料庫裡的 NaN（空值）換成空字串，防止前端 JavaScript 認不得而無法運作
  filtered_df = filtered_df.fillna("-")
  restaurants_list = filtered_df.to_dict(orient="records")

  # 如果符合條件的餐廳太多，隨機抽 8 家出來做成轉盤
  if len(restaurants_list) > 8:
    restaurants_list = random.sample(restaurants_list, 8)

  return jsonify({"status": "success", "restaurants": restaurants_list})


if __name__ == "__main__":
  # 【關鍵修正】調整為雲端伺服器佈署設定，允許外部所有 IP 連線進來
  app.run(debug=True, host="0.0.0.0", port=5000)
