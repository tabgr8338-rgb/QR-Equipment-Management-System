import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="備品管理Pro", page_icon="📦")

GAS_URL = st.secrets.get("https://script.google.com/macros/s/AKfycbxHG2Al8nn_jN7Dh6xHHD9NFZaBJw0DqbrW4v48L9TELC9ZHjae6671wGBuDhSr4ZcM/exec")
API_TOKEN = st.secrets.get("API_TOKEN")

query_params = st.query_params
target_code = query_params.get("code", "")

if not target_code:
    st.info("📷 QRコードをスキャンしてください。")
    st.stop()

# 📡 データ取得（GET）
@st.cache_data(ttl=5)
def get_item(code):
    # ✅ tokenを付与してリクエスト
    res = requests.get(GAS_URL, params={"code": code, "token": API_TOKEN})
    return res.json()

data = get_item(target_code)

if data.get("status") == "ok":
    item = data["item"]
    st.title(f"📦 {item['品名']}")
    st.metric("保管場所", f"{item['棚']}-{item['箱']}")
    st.write(f"**現在の状態:** {item.get('状態', '在庫')}")
    st.divider()

    if item.get("状態") == "発注中":
        st.warning(f"🚫 発注済み: {item.get('発注者')} ({item.get('発注日')})")
        if st.button("✅ 入荷完了にする", use_container_width=True):
            # ✅ POST時もtokenを同封
            res = requests.post(GAS_URL, json={"action": "arrival", "code": target_code, "token": API_TOKEN})
            if res.json().get("status") == "ok":
                st.success("在庫に戻しました！")
                st.rerun()
    else:
        requester = st.text_input("担当者名を入力")
        if st.button("🚀 発注を確定する", type="primary", use_container_width=True):
            if requester:
                res = requests.post(GAS_URL, json={"action": "order", "code": target_code, "requester": requester, "token": API_TOKEN})
                if res.json().get("status") == "ok":
                    st.balloons()
                    st.success("発注を記録しました。")
            else:
                st.error("担当者名を入力してください。")
else:
    st.error(f"エラー: {data.get('status')} {data.get('debug','')}")