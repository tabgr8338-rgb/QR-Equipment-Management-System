import streamlit as st
import requests
import urllib.parse

# --- 基本設定 ---
st.set_page_config(page_title="備品管理Pro", page_icon="📦")

# Secretsから設定取得（事前にStreamlit CloudのSettingsで設定が必要）
GAS_URL = st.secrets.get("https://script.google.com/macros/s/AKfycbyPzdk1rcOjOVo9yy6war8b4_y6dj1VJKzGldh4iblhawgfG_xdqTVYmRq4Ci3dUxhu/exec")
API_TOKEN = st.secrets.get("API_TOKEN")

if not GAS_URL or not API_TOKEN:
    st.error("⚠️ 設定エラー: Secretsに GAS_URL と API_TOKEN を登録してください。")
    st.stop()

# セッション状態の管理
if "processing" not in st.session_state: st.session_state.processing = False
if "done" not in st.session_state: st.session_state.done = False

# URLから品番(code)を取得
query_params = st.query_params
target_code = query_params.get("code", "")

# --- API連携関数 ---
def call_gas_get(code):
    try:
        res = requests.get(GAS_URL, params={"code": code, "token": API_TOKEN}, timeout=5)
        return res.json()
    except: return {"status": "network_error"}

def call_gas_post(payload):
    try:
        payload["token"] = API_TOKEN
        res = requests.post(GAS_URL, json=payload, timeout=10)
        return res.json()
    except: return {"status": "busy"}

# --- メイン画面 ---
if not target_code:
    st.info("📷 備品のQRコードをスキャンして開いてください。")
    st.stop()

if st.session_state.done:
    st.success("✅ 処理が完了しました。この画面を閉じてください。")
    st.stop()

# データ取得
data = call_gas_get(target_code)

if data.get("status") == "unauthorized":
    st.error("🔐 認証エラー: トークンが一致しません。")
    st.stop()
elif data.get("status") == "not_found":
    st.error("❌ 登録されていない、または削除された品番です。")
    st.stop()
elif data.get("status") != "ok":
    st.error(f"⚠️ エラー: {data.get('status')}")
    st.stop()

item = data["item"]

# --- 表示部 ---
st.title(f"📦 {item.get('品名')}")
col1, col2 = st.columns(2)
with col1:
    st.metric("保管場所", f"{item.get('棚')}-{item.get('箱')}")
with col2:
    st.metric("現在の状態", item.get("状態", "在庫"))

st.write(f"**型式:** {item.get('発注型式', '-')}")
st.write(f"**発注単位:** {item.get('发注数量', '')} {item.get('発注単位', '')} ({item.get('発注先', '')})")
st.divider()

if st.session_state.processing:
    st.warning("⏳ 通信中...")
    st.stop()

# --- アクション制御 ---
status = item.get("状態")

if status == "発注中":
    st.warning(f"🚫 発注済み: {item.get('発注者','')} ({item.get('発注日','')})")
    confirm = st.checkbox("現物の入荷を確認しました")
    if st.button("✅ 入荷完了（在庫を戻す）", disabled=not confirm, use_container_width=True):
        st.session_state.processing = True
        res = call_gas_post({"action": "arrival", "code": target_code})
        if res.get("status") == "ok":
            st.session_state.done = True
            st.rerun()
        else:
            st.error("更新に失敗しました。")
            st.session_state.processing = False
else:
    st.success("🟢 在庫あり（発注可能です）")
    requester = st.text_input("発注担当者名", placeholder="名前を入力")
    
    if st.button("🚀 発注を確定する", type="primary", use_container_width=True):
        if not requester:
            st.warning("担当者名を入力してください。")
        else:
            st.session_state.processing = True
            res = call_gas_post({"action": "order", "code": target_code, "requester": requester})
            if res.get("status") == "ok":
                # メール連携（mailtoリンク）
                subject = f"【備品発注リマインド】{item['品名']}"
                body = f"品名: {item['品名']}\n型式: {item['発注型式']}\n場所: {item['棚']}-{item['箱']}\n依頼者: {requester}"
                mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                
                st.balloons()
                st.link_button("📧 承認依頼メールを作成して終了", mailto, use_container_width=True)
                st.session_state.done = True
            else:
                st.error(f"エラー: {res.get('status')}")
                st.session_state.processing = False