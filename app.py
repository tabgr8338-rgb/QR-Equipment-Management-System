import streamlit as st
import pandas as pd
import requests
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials

# 設定（ここを書き換えてください）
GAS_URL = "https://script.google.com/macros/s/AKfycbzTfWNIiGoPKZtLlTVBQGIFGDstVTNNGShGtpbK61ce_JS1tslkt0UHGdMRAyRIY98_/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1b3C5aKitYcrFHv8DWCOP-h9EUPGm2lTGrfhyR0Yg8Bs/edit?gid=0#gid=0"

# Sheets接続
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).get_worksheet(0)

# データ読み込み（状態を最新にするためキャッシュなし）
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("工場備品 QR発注システム")

# URLから品番取得
params = st.query_params
default_code = params.get("code", "")

code = st.text_input("QRコード（品番）", value=default_code)

if code:
    item = df[df["品番"] == code]
    if item.empty:
        st.error("品番が見つかりません")
    else:
        item = item.iloc[0]
        st.subheader(f"品名: {item['品名']}")

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**型式:** {item['発注型式']}")
            st.write(f"**場所:** {item['棚']}-{item['箱']}")
        with col2:
            st.write(f"**発注量:** {item['発注数量']} {item['発注単位']}")
            st.write(f"**発注先:** {item['発注先']}")

        if item["状態"] == "発注中":
            st.warning(f"⚠️ 発注中（{item['発注者']} / {item['発注日']}）")
            if st.button("✅ 入荷完了（在庫に戻す）"):
                requests.post(GAS_URL, json={"action": "arrival", "code": code})
                st.success("在庫に戻しました。画面を更新してください。")
                st.rerun()
        else:
            requester = st.text_input("あなたの名前を入力")
            if st.button("📧 発注メール作成"):
                if not requester:
                    st.error("名前を入力してください")
                else:
                    # メールリンク
                    subject = f"【備品発注】{item['品名']}"
                    body = f"品名: {item['品名']}\n型式: {item['発注型式']}\n数量: {item['発注数量']} {item['発注単位']}\n発注先: {item['発注先']}\n発注者: {requester}"
                    url = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                    
                    # GAS更新
                    requests.post(GAS_URL, json={"action": "order", "code": code, "requester": requester})
                    
                    st.markdown(f"### [👉 こちらをタップしてメール送信]({url})")
                    st.success("ステータスを「発注中」に更新しました。")