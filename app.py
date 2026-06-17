import random
from flask import Flask, jsonify, render_template, request
import pandas as pd

app = Flask(__name__)

# 直接讀取 Excel 檔案
df = pd.read_excel("data.xlsx")

# 強迫清理欄位與內容的隱形空格
df.columns = df.columns.str.strip()
df["餐廳名稱"] = df["餐廳名稱"].astype(str).str.strip()
df["價格區間"] = df["價格區間"].astype(str).str.strip()
df["評價"] = pd.to_numeric(df["評價"], errors="coerce").fillna(0.0)


# 寫一個貼心的小程式，把 Excel 裡的 "10 分 (3.9 公里)" 變成純數字的 10，方便篩選
def extract_minutes(dist_str):
  try:
    if pd.isna(dist_str) or not isinstance(dist_str, str):
      return 999  # 沒寫時間的就排到最後
    if "分" in dist_str:
      # 抓出「分」前面的數字
      num_str = dist_str.split("分")[0].strip()
      return int(num_str)
    return 999
  except Exception:
    return 999


df["純分鐘"] = df["距離元智大學"].apply(extract_minutes)


@app.route("/")
def index():
  # 抓取不重複價格區間
  budgets = df["價格區間"].dropna().unique().tolist()
  budgets = [b for b in budgets if b != "nan" and b != "None"]
  return render_template("index.html", budgets=budgets)


@app.route("/get_restaurants", methods=["POST"])
def get_restaurants():
  data = request.get_json()
  selected_budget = data.get("budget")
  min_rating = float(data.get("rating", 0))
  max_time = int(data.get("time", 999))

  filtered_df = df.copy()

  # 條件 1: 預算篩選
  if selected_budget and selected_budget != "all":
    filtered_df = filtered_df[filtered_df["價格區間"] == selected_budget]

  # 條件 2: 評價篩選 (只選大於等於設定星等的餐廳)
  filtered_df = filtered_df[filtered_df["評價"] >= min_rating]

  # 條件 3: 距離時間篩選 (只選小於等於設定分鐘的餐廳)
  if max_time != 999:
    filtered_df = filtered_df[filtered_df["純分鐘"] <= max_time]

  if filtered_df.empty:
    return jsonify({"status": "empty", "restaurants": []})

  # 把資料庫裡的 NaN（空值）換成空字串，防止前端認不得
  filtered_df = filtered_df.fillna("-")
  restaurants_list = filtered_df.to_dict(orient="records")

  # 隨機抽 8 家出來做成轉盤
  if len(restaurants_list) > 8:
    restaurants_list = random.sample(restaurants_list, 8)

  return jsonify({"status": "success", "restaurants": restaurants_list})


if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=5000)