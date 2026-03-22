import streamlit as st
import requests
import urllib.parse

# --- 1. ページ設定（現場での視認性を最優先） ---
st.set_page_config(page_title="備品管理Pro", page_icon="📦", layout="centered")

# モバイル最適化CSS：枠をスリムに、文字を最大化
st.markdown("""
    <style>
    /* ボタンを大きく押しやすく */
    .stButton>button { 
        height: 3.8em; 
        font-size: 1.3rem; 
        font-weight: bold; 
        border-radius: 15px; 
        border: 2px solid #007bff;
        margin-top: 10px;
    }
    /* 情報カード：余白を最小限にし、文字を大きく */
    .status-card { 
        padding: 10px 15px; 
        border-radius: 10px; 
        background-color: #f8f9fa; 
        border-left: 10px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        line-height: 1.2;
    }
    .item-id { font-size: 0.8rem; color: #666; margin: 0; }
    .item-name { font-size: 2.0rem; font-weight: bold; color: #1a1a1a; margin: 4px 0; }
    .item-loc { font-size: 1.6rem; color: #007bff; font-weight: bold; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# Secretsから取得
try:
    GAS_URL = st.secrets["GAS_URL"]
    API_TOKEN = st.secrets["API_TOKEN"]
except Exception as e:
    st.error(f"❌ Secrets読み込みエラー: {e}")
    st.info("Streamlit CloudのSettings > Secretsを確認してください。")
    st.stop()
    
# URLパラメータ解析
params = st.query_params
target_code = str(params.get("code", ""))

# --- 2. 画面分岐 ---
if not target_code:
    st.title("📦 備品管理システム")
    st.info("💡 **QRコードをスキャンしてください**")
    st.stop()

# --- 3. API通信関数 ---
def call_gas(method, payload=None):
    try:
        if method == "GET":
            res = requests.get(GAS_URL, params={"code": target_code, "token": API_TOKEN}, timeout=15)
        else:
            payload["token"] = API_TOKEN
            payload["code"] = target_code
            res = requests.post(GAS_URL, json=payload, timeout=15)
        return res.json()
    except Exception as e:
        return {"status": "error", "message": f"通信失敗: {str(e)}"}

# --- 4. メインUI表示 ---
with st.spinner("確認中..."):
    data = call_gas("GET")

if data.get("status") == "ok":
    item = data["item"]
    status = item.get("状態", "在庫")

    # 🛠️ 改善版デザイン：品番は最小、品名と場所を画面いっぱいに表示
    st.markdown(f"""
        <div class="status-card">
            <p class="item-id">品番: {target_code}</p>
            <div class="item-name">{item['品名']}</div>
            <div class="item-loc">📍 {item['棚']} - {item['箱']}</div>
        </div>
        """, unsafe_allow_html=True)

    # 状態に応じたアクション
    if status == "発注中":
        st.error(f"🛑 **【発注中】** {item.get('発注者', '担当者不明')}様が依頼済み")
        st.caption(f"📅 依頼日: {item.get('発注日', '-')}")
        
        if st.button("✅ 入荷完了（在庫に戻す）", use_container_width=True):
            with st.spinner("更新中..."):
                res = call_gas("POST", {"action": "arrival"})
                if res.get("status") == "ok":
                    st.balloons()
                    st.success("在庫を更新しました！")
                    st.rerun()
    
    else:
        st.success("🟢 **在庫あり（発注可能）**")
        col1, col2 = st.columns(2)
        with col1:
            st.caption("型式")
            st.write(item.get('発注型式', '-'))
        with col2:
            st.caption("単位")
            st.write(f"{item.get('発注数量', '')}{item.get('発注単位', '')}")