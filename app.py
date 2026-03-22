import streamlit as st
import requests
import urllib.parse

# --- 1. ページ設定（現場で見やすく） ---
st.set_page_config(page_title="備品管理Pro", page_icon="📦", layout="centered")

# モバイル用カスタムCSS（ボタンを大きく、カード型デザインに）
st.markdown("""
    <style>
    .stButton>button { height: 3.5em; font-size: 1.2rem; font-weight: bold; border-radius: 12px; border: 2px solid #007bff; }
    .status-card { padding: 20px; border-radius: 15px; background-color: #f8f9fa; border-left: 10px solid #007bff; }
    .info-label { color: #666; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# Secretsから取得（ここがNoneだとエラーになります）
GAS_URL = st.secrets.get("https://script.google.com/macros/s/AKfycbxHG2Al8nn_jN7Dh6xHHD9NFZaBJw0DqbrW4v48L9TELC9ZHjae6671wGBuDhSr4ZcM/exec")
API_TOKEN = st.secrets.get("EMSystem-qr-secure-2026")

# URLパラメータ解析（iPhone/PC共通）
# 新しいStreamlitの仕様に合わせ、確実に文字列として取得
params = st.query_params
target_code = str(params.get("code", ""))

# --- 2. 画面分岐 ---
if not target_code:
    st.title("📦 備品管理システム")
    st.info("💡 **QRコードをスキャンしてください**\n\nカメラでQRを読み取ると、ここに備品の詳細が表示されます。")
    st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=TEST", caption="テスト用QR（動作確認用）")
    st.stop()

if not GAS_URL or GAS_URL == "None":
    st.error("⚠️ 設定エラー: StreamlitのSecretsに 'GAS_URL' が登録されていません。")
    st.stop()

# --- 3. API通信関数 ---
def call_gas(method, payload=None):
    try:
        if method == "GET":
            # 認証トークンを確実に付与
            res = requests.get(GAS_URL, params={"code": target_code, "token": API_TOKEN}, timeout=15)
        else:
            payload["token"] = API_TOKEN
            payload["code"] = target_code
            res = requests.post(GAS_URL, json=payload, timeout=15)
        
        return res.json()
    except Exception as e:
        return {"status": "error", "message": f"通信失敗: {str(e)}"}

# --- 4. メインUI表示 ---
with st.spinner("データを取得中..."):
    data = call_gas("GET")

if data.get("status") == "ok":
    item = data["item"]
    status = item.get("状態", "在庫")

    # カード型デザインで表示
    st.markdown(f"""
        <div class="status-card">
            <p class="info-label">品番: {target_code}</p>
            <h1 style='margin-top:0;'>{item['品名']}</h1>
            <h3>📍 {item['棚']} - {item['箱']}</h3>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- 状態に応じたボタン配置 ---
    if status == "発注中":
        st.error(f"🛑 **現在【発注中】です**")
        st.write(f"👤 **依頼者:** {item.get('発注者')}")
        st.write(f"📅 **発注日:** {item.get('発注日')}")
        
        st.write("---")
        if st.button("✅ 現物が届いた（入荷処理）", use_container_width=True):
            with st.spinner("更新中..."):
                res = call_gas("POST", {"action": "arrival"})
                if res.get("status") == "ok":
                    st.balloons()
                    st.success("在庫を更新しました！")
                    st.rerun()
                else:
                    st.error(f"更新失敗: {res.get('status')}")
    
    else:
        st.success("🟢 **在庫あり（発注可能）**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**型式:**\n{item.get('発注型式', '-')}")
        with col2:
            st.write(f"**発注先:**\n{item.get('発注先', '-')}")
        
        st.write(f"**発注単位:** {item.get('発注数量', '')} {item.get('発注単位', '')}")

        st.divider()
        requester = st.text_input("👤 あなたの名前（担当者名）", placeholder="例：山田")
        
        if st.button("🚀 発注を確定する", type="primary", use_container_width=True):
            if not requester:
                st.warning("担当者名を入力してください。")
            else:
                with st.spinner("通信中..."):
                    res = call_gas("POST", {"action": "order", "requester": requester})
                    if res.get("status") == "ok":
                        # メールリンク
                        subject = f"【備品発注】{item['品名']}"
                        body = f"品目: {item['品名']}\n型式: {item['発注型式']}\n依頼者: {requester}"
                        mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                        
                        st.balloons()
                        st.success("発注を記録しました！")
                        st.link_button("📧 承認依頼メールを作成", mailto, use_container_width=True)
                    else:
                        st.error(f"エラー: {res.get('status')}")

else:
    # 認証エラーや品番ミスの場合
    st.error(f"❌ 読み込み失敗")
    st.info(f"理由: {data.get('status')}")
    if "debug" in data: st.warning(f"Debug: {data['debug']}")
    if "message" in data: st.code(data['message'])