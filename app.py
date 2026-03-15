import streamlit as st
import pandas as pd
import requests
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 1. 設定（GASのURLを自分のものに書き換えてください）
# ==========================================
GAS_URL = "https://script.google.com/macros/s/AKfycbzTfWNIiGoPKZtLlTVBQGIFGDstVTNNGShGtpbK61ce_JS1tslkt0UHGdMRAyRIY98_/exec"
SHEET_NAME = "Equipment Management Sheet"
WORKSHEET_NAME = "備品マスター"

# ==========================================
# 2. Google Sheets 接続設定
# ==========================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# GitHub/Streamlit Cloud環境（Secrets）とローカル環境の両方に対応
if "gcp_service_account" in st.secrets:
    # クラウド環境
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
else:
    # ローカル環境（テスト用）
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scope
    )

client = gspread.authorize(creds)

# データを最新状態で読み込む関数
def get_data():
    sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# ==========================================
# 3. UI・メイン処理
# ==========================================
st.set_page_config(page_title="工場備品管理", layout="centered")
st.title("📦 工場備品 QR発注システム")

# 最新データの取得
df = get_data()

# URLパラメータ (?code=...) または手入力から品番を取得
params = st.query_params
url_code = params.get("code", "")
code = st.text_input("QRコード（品番）を入力", value=url_code)

if code:
    # 品番の完全一致検索（文字列として比較、前後空白を削除）
    target_code = str(code).strip()
    # 品番列を文字列に変換して検索
    item_df = df[df["品番"].astype(str).str.strip() == target_code]

    if item_df.empty:
        st.error(f"品番「{target_code}」は見つかりません。")
        # デバッグ用：どうしても見つからない場合に、今読み込んでいる品番を5件だけ出す
        with st.expander("スプレッドシート側の品番サンプル"):
            st.write(df["品番"].head().tolist())
    else:
        item = item_df.iloc[0]
        st.success(f"照合完了: {item['品名']}")

        # 情報表示
        st.subheader(f"品名: {item['品名']}")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**型式:** {item['発注型式']}")
            st.write(f"**棚-箱:** {item['棚']}-{item['箱']}")
        with col2:
            st.write(f"**発注数:** {item['発注数量']} {item['発注単位']}")
            st.write(f"**発注先:** {item['発注先']}")

        # --- 状態に応じたボタン処理 ---
        if item["状態"] == "発注中":
            st.warning(f"⚠️ 現在発注中です（担当: {item['発注者']} / 日付: {item['発注日']}）")
            if st.button("✅ 入荷完了（在庫に戻す）", use_container_width=True):
                # GASへ送信（入荷アクション）
                requests.post(GAS_URL, json={"action": "arrival", "code": target_code})
                st.success("ステータスを更新しました。")
                st.rerun()
        else:
            st.info(f"現在の状態: {item['状態']}")
            requester = st.text_input("あなたの名前を入力してください")
            
            if st.button("📧 発注ステータス更新 ＆ メール作成", use_container_width=True):
                if not requester:
                    st.error("発注者名を入力してください。")
                else:
                    # 1. メールURL生成
                    subject = f"【備品発注】{item['品名']}"
                    body = f"品名:{item['品名']}\n型式:{item['発注型式']}\n数量:{item['発注数量']}\n場所:{item['棚']}-{item['箱']}\n発注者:{requester}"
                    mailto_url = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                    
                    # 2. GASへ送信（発注アクション）
                    requests.post(GAS_URL, json={
                        "action": "order",
                        "code": target_code,
                        "requester": requester
                    })
                    
                    # 3. メールボタン表示（Safari対策）
                    st.link_button("📬 メールアプリを起動して送信", mailto_url, type="primary", use_container_width=True)
                    st.success("シートを『発注中』に更新しました。上のボタンから送信してください。")