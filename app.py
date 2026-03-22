import streamlit as st
import requests
import urllib.parse

# --- 1. ページ設定（モバイルで見やすく） ---
st.set_page_config(page_title="備品管理Pro", page_icon="📦", layout="centered")

# CSSでボタンを大きく、視認性を向上
st.markdown("""
    <style>
    .stButton>button { height: 3em; font-size: 1.2rem; font-weight: bold; border-radius: 10px; }
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Secretsから取得
GAS_URL = st.secrets.get("https://script.google.com/macros/s/AKfycbxHG2Al8nn_jN7Dh6xHHD9NFZaBJw0DqbrW4v48L9TELC9ZHjae6671wGBuDhSr4ZcM/exec")
API_TOKEN = st.secrets.get("EMSystem-qr-secure-2026")

# --- 2. URLパラメータ解析（iPhone対策） ---
# st.query_paramsから値を取得。リストで返る場合があるためstrに変換
params = st.query_params
target_code = str(params.get("code", ""))

if not target_code:
    st.info("💡 QRコードをスキャンして備品を表示してください。")
    st.stop()

# --- 3. API連携（堅牢なGET/POST） ---
def call_gas(method, payload=None):
    try:
        if method == "GET":
            res = requests.get(GAS_URL, params={"code": target_code, "token": API_TOKEN}, timeout=10)
        else:
            payload["token"] = API_TOKEN
            payload["code"] = target_code
            res = requests.post(GAS_URL, json=payload, timeout=10)
        
        # レスポンスがJSONでない場合のエラー回避
        return res.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 4. メイン画面の構築 ---
data = call_gas("GET")

if data.get("status") == "ok":
    item = data["item"]
    status = item.get("状態", "")

    # タイトルと場所（大きく表示）
    st.title(f"📦 {item['品名']}")
    st.subheader(f"📍 保管場所: {item['棚']}-{item['箱']}")
    
    # 状態によって表示を出し分け
    if status == "発注中":
        st.error(f"⚠️ 現在【発注中】です")
        st.info(f"👤 依頼者: {item.get('発注者')}\n\n📅 日時: {item.get('発注日')}")
        
        st.divider()
        if st.button("✅ 現物が届いた（入荷完了）", use_container_width=True):
            with st.spinner("更新中..."):
                res = call_gas("POST", {"action": "arrival"})
                if res.get("status") == "ok":
                    st.success("在庫を更新しました！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"更新失敗: {res.get('status')}")
    
    else:
        st.success("🟢 在庫あり（発注可能です）")
        st.write(f"型式: {item.get('発注型式', '-')}")
        st.write(f"単位: {item.get('発注数量', '')} {item.get('発注単位', '')}")
        
        st.divider()
        requester = st.text_input("👤 あなたの名前を入力してください", placeholder="例：山田")
        
        if st.button("🚀 発注を確定する", type="primary", use_container_width=True):
            if not requester:
                st.warning("名前を入力してください。")
            else:
                with st.spinner("通信中..."):
                    res = call_gas("POST", {"action": "order", "requester": requester})
                    if res.get("status") == "ok":
                        # メール連携用のリンク作成
                        subject = f"【備品発注】{item['品名']}"
                        body = f"品目: {item['品名']}\n型式: {item['発注型式']}\n依頼者: {requester}"
                        mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                        
                        st.success("発注を記録しました！")
                        st.balloons()
                        st.link_button("📧 承認依頼メールを作成", mailto, use_container_width=True)
                    else:
                        st.error(f"エラー: {res.get('status')}")

else:
    # エラー時のデバッグ情報表示（iPhoneで原因を特定するため）
    st.error(f"❌ 読み込み失敗")
    st.write(f"Status: {data.get('status')}")
    if "debug" in data: st.code(data['debug'])
    if "message" in data: st.code(data['message'])