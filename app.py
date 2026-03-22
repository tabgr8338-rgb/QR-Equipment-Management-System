import streamlit as st
import requests
import urllib.parse

# --- 1. ページ設定 ---
st.set_page_config(page_title="備品管理Pro [公式]", page_icon="📦", layout="centered")

# --- 2. セッション初期化 ---
if "processing" not in st.session_state:
    st.session_state.processing = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "confirm_arrival" not in st.session_state:
    st.session_state.confirm_arrival = False
if "done" not in st.session_state:
    st.session_state.done = False

# --- 3. CSS ---
st.markdown("""
<style>
.stButton>button { 
    height: 3.8em; font-size: 1.3rem; font-weight: bold; border-radius: 15px; border: 2px solid #007bff; margin-top: 10px;
}
.status-card { 
    padding: 10px 15px; border-radius: 10px; background-color: #f8f9fa; border-left: 10px solid #007bff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; line-height: 1.2;
}
.item-id { font-size: 0.8rem; color: #666; margin: 0; }
.item-name { font-size: 2.0rem; font-weight: bold; color: #1a1a1a; margin: 4px 0; }
.item-loc { font-size: 1.6rem; color: #007bff; font-weight: bold; margin: 0; }
</style>
""", unsafe_allow_html=True)

# --- 4. Secrets ---
try:
    GAS_URL = st.secrets["GAS_URL"]
    API_TOKEN = st.secrets["API_TOKEN"]
except:
    st.error("❌ システム設定（Secrets）が未完了です。")
    st.stop()

# --- 5. URLパラメータ ---
params = st.query_params
target_code = str(params.get("code", ""))
src = params.get("src", "qr")

# --- 6. QR未スキャン ---
if not target_code:
    st.title("📦 備品管理システム")
    st.info("💡 QRコードをスキャンしてください")
    st.stop()

# --- 7. API通信 ---
def call_gas(method, payload=None):
    try:
        if method == "GET":
            res = requests.get(
                GAS_URL,
                params={"code": target_code, "token": API_TOKEN, "src": src},
                timeout=15
            )
        else:
            payload = payload or {}
            payload.update({"token": API_TOKEN, "code": target_code, "src": src})
            res = requests.post(GAS_URL, json=payload, timeout=15)

        if res.status_code != 200:
            return {"status": "error", "message": f"サーバー応答エラー({res.status_code})"}

        return res.json()

    except Exception as e:
        return {"status": "error", "message": f"通信失敗: {str(e)}"}

# --- 8. データ取得 ---
with st.spinner("データを取得中..."):
    data = call_gas("GET")

# --- 9. エラー処理 ---
if data.get("status") == "error":
    st.error(f"⚠️ {data.get('message')}")
    if st.button("🔄 再試行する"):
        st.rerun()
    st.stop()

# --- 10. バージョンチェック ---
if data.get("version") != 3:
    st.error("⚠️ システム不整合（バージョン不一致）")
    st.stop()

# --- 11. データ安全取得 ---
item = data.get("item", {})
if not item:
    st.error("データ形式エラー")
    st.stop()

status = item.get("状態", "在庫")

# --- viewログ送信 ---
call_gas("POST", {"action": "view"})

# --- 表示 ---
st.markdown(f"""
<div class="status-card">
    <p class="item-id">品番: {target_code}</p>
    <div class="item-name">{item.get('品名','-')}</div>
    <div class="item-loc">📍 {item.get('棚','-')} - {item.get('箱','-')}</div>
</div>
""", unsafe_allow_html=True)

st.caption(f"source: {src} / code: {target_code}")

st.divider()

# =========================
# 発注中
# =========================
if status == "発注中":
    st.error("🛑 現在【発注中】です")
    st.write(f"👤 {item.get('発注者', '不明')} / 📅 {item.get('発注日', '-')}")

    if not st.session_state.confirm_arrival:
        if st.button("✅ 現物が届いた（入荷処理）", use_container_width=True, disabled=st.session_state.processing):
            st.session_state.confirm_arrival = True
            st.rerun()
    else:
        st.warning("⚠️ 入荷処理を実行しますか？")
        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("✅ はい、実行する", type="primary", use_container_width=True, disabled=st.session_state.processing):
                st.session_state.confirm_arrival = False
                st.session_state.processing = True

                res = {"status": "error"}
                try:
                    with st.spinner("更新中..."):
                        res = call_gas("POST", {"action": "arrival"})
                finally:
                    st.session_state.processing = False

                if res.get("status") == "ok":
                    st.success("在庫を更新しました！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"更新失敗: {res.get('message', '不明なエラー')}")

        with col_no:
            if st.button("❌ いいえ、戻る", use_container_width=True):
                st.session_state.confirm_arrival = False
                st.rerun()

# =========================
# 在庫あり
# =========================
else:
    if st.session_state.done:
        st.success("発注済みです")
        st.stop()

    st.success("🟢 在庫あり（発注可能）")

    col1, col2 = st.columns(2)
    with col1:
        st.caption("型式")
        st.write(item.get('発注型式', '-'))
    with col2:
        st.caption("単位")
        st.write(f"{item.get('発注数量', '')} {item.get('発注単位', '')}")

    st.divider()

    requester = st.text_input("👤 あなたの名前", value=st.session_state.user_name, placeholder="例：山田")

    if requester:
        st.session_state.user_name = requester

    # 在庫不一致
    if st.button("👀 現物なし（在庫不一致）"):
        call_gas("POST", {"action": "report_missing"})
        st.warning("在庫不一致を報告しました")

    if st.button("🚀 発注を確定する", type="primary", use_container_width=True, disabled=st.session_state.processing):

        if not requester:
            st.warning("担当者名を入力してください")
        else:
            st.session_state.processing = True

            res = {"status": "error"}
            try:
                with st.spinner("送信中..."):
                    res = call_gas("POST", {"action": "order", "requester": requester})
            finally:
                st.session_state.processing = False

            if res.get("status") == "ok":
                st.session_state.done = True

                subject = f"【備品発注】{item.get('品名','')}"
                body = f"品目: {item.get('品名','')}\n型式: {item.get('発注型式','')}\n依頼者: {requester}"
                mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

                st.success("発注を記録しました！")
                st.balloons()
                st.link_button("📧 承認依頼メールを作成", mailto, use_container_width=True)
            else:
                st.error(f"エラー: {res.get('message','不明なエラー')}")

# --- 12. 品番エラー ---
if data.get("status") != "ok":
    st.error("❌ 該当する品番が見つかりません")
    if st.button("🔄 最初に戻る"):
        st.query_params.clear()
        st.rerun()
