import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# -----------------------------
# Google Sheets 接続
# -----------------------------

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=scope
)

client = gspread.authorize(creds)

SHEET_URL = "あなたのGoogleシートURL"

sheet = client.open_by_url(SHEET_URL).sheet1

data = sheet.get_all_records()
df = pd.DataFrame(data)

# -----------------------------
# QR読み取り
# -----------------------------

st.title("工場備品QR発注")

code = st.text_input("QRコード")

if code:

    item = df[df["品番"] == code]

    if item.empty:
        st.error("品番なし")
    else:

        item = item.iloc[0]

        st.subheader(item["品名"])

        st.write("棚:", item["棚"])
        st.write("箱:", item["箱"])
        st.write("発注型式:", item["発注型式"])
        st.write("数量:", item["発注数量"])
        st.write("発注先:", item["発注先"])

        # -----------------------------
        # 重複発注チェック
        # -----------------------------

        if item["状態"] == "発注中":

            st.error("⚠既に発注中")

            st.write("発注者:", item["発注者"])
            st.write("発注日:", item["発注日"])

        else:

            name = st.text_input("発注者")

            if st.button("発注メール作成"):

                subject = "備品発注"

                body = f"""
品番:{code}
品名:{item['品名']}
型式:{item['発注型式']}
数量:{item['発注数量']}
発注先:{item['発注先']}
棚:{item['棚']}
箱:{item['箱']}
"""

                mail = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

                st.markdown(f"[メール作成]({mail})")

                # シート更新

                row = df.index[df["品番"] == code][0] + 2

                sheet.update_cell(row, 14, "発注中")
                sheet.update_cell(row, 15, name)
                sheet.update_cell(row, 16, str(datetime.today().date()))

                st.success("発注登録しました")

# -----------------------------
# 入荷処理
# -----------------------------

st.divider()

st.subheader("入荷処理")

code2 = st.text_input("入荷QR")

if code2:

    row = df.index[df["品番"] == code2][0] + 2

    if st.button("入荷登録"):

        sheet.update_cell(row, 14, "在庫")
        sheet.update_cell(row, 15, "")
        sheet.update_cell(row, 16, "")

        st.success("在庫に戻しました")