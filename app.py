import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="備品Pro", page_icon="📦")

# 業務アプリ特化型スタイル
st.markdown("""
    <style>
    .item-title { font-size: 2.2rem !important; font-weight: 800; color: #111827; margin-bottom: 0px; }
    .stButton>button { height: 4rem; font-size: 1.2rem; border-radius: 12px; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

GAS_URL = st.secrets.get("https://script.google.com/macros/s/AKfycbxryPnT0-QJ7t-J2lWumLrYdNR0VtClgp6su556Wv6yrflpRPKjWa1Y1Jxgjk01GnA/exec")

# --- 状態管理ロジック（Sランクの鍵） ---
current_code = st.query_params.get("code", "")

if "last_code" not in st.session_state:
    st.session_state.last_code = current_code
    st.session_state.done = False
    st.session_state.processing = False

# QRが切り替わったら全フラグをリセット（運用での詰まりを防止）
if st.session_state.last_code != current_code:
    st.session_state.done = False
    st.session_state.processing = False
    st.session_state.last_code = current_code

def get_item(code):
    try:
        res = requests.get(GAS_URL, params={"code": code}, timeout=3)
        return res.json()
    except: return {"status": "network_error"}

def post_action(payload):
    try:
        res = requests.post(GAS_URL, json=payload, timeout=7)
        return res.json()
    except: return {"status": "busy"}

# --- メインロジック ---
if not current_code:
    st.info("📷 QRコードをスキャンしてください")
    st.stop()

# 完了状態の表示
if st.session_state.done:
    st.success("✅ 操作は正常に完了しました。画面を閉じてください。")
    st.stop()

# 最新データ取得
with st.spinner("照合中..."):
    data = get_item(current_code)

if data.get("status") != "ok":
    st.error(f"❌ 品番エラー: {data.get('status', 'unknown')}")
    st.stop()

item = data["item"]
st.toast(f"{item['品名']} 読込完了", icon="📦")

# 表示エリア
st.markdown(f'<p class="item-title">{item["品名"]}</p>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
col1.metric("棚番", f"{item['棚']}-{item['箱']}")
col2.metric("発注単位", f"{item['発注数量']}{item['発注単位']}")
st.caption(f"型式: {item['発注型式']} | 発注先: {item['発注先']}")
st.divider()

if st.session_state.processing:
    st.warning("⏳ 処理中です... そのままお待ちください")
    st.stop()

# --- 状態別アクション ---
if item.get("状態") == "発注中":
    st.error(f"🚫 発注済み: {item.get('発注者','')} ({item.get('発注日','')})")
    
    # 誤操作防止の2段階確認
    confirm = st.checkbox("入荷を確認しました")
    if st.button("✅ 入荷完了（在庫復帰）", disabled=not confirm, use_container_width=True):
        st.session_state.processing = True
        res = post_action({"action": "arrival", "code": current_code})
        st.session_state.processing = False
        if res.get("status") == "ok":
            st.session_state.done = True
            st.rerun()
else:
    st.success("🟢 在庫あり（発注可能）")
    name = st.text_input("担当者名", placeholder="氏名を入力", label_visibility="collapsed")
    
    if st.button("🚀 発注を確定する", use_container_width=True, type="primary"):
        if not name:
            st.warning("⚠️ 名前を入力してください")
        else:
            st.session_state.processing = True
            res = post_action({"action": "order", "code": current_code, "requester": name})
            st.session_state.processing = False
            
            if res.get("status") == "ok":
                # ② 最終整合チェック（自分の操作結果かを確認）
                fresh = get_item(current_code)
                fresh_item = fresh.get("item", {})
                if fresh_item.get("状態") == "発注中" and fresh_item.get("発注者") == name:
                    st.session_state.done = True
                    st.success("✅ 処理完了。報告メールを作成してください。")
                    
                    # メール送信
                    subject = f"【備品発注】{item['品名']}"
                    body = (f"品名: {item['品名']}\n型式: {item['発注型式']}\n"
                            f"数量: {item['発注数量']}{item['発注単位']}\n"
                            f"場所: {item['棚']}-{item['箱']}\n依頼者: {name}")
                    mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                    st.link_button("📧 メール送信（最終ステップ）", mailto, use_container_width=True)
                    st.toast("メール送信で完了です", icon="📧")
                else:
                    st.error("⚠️ 状態不整合。他の人が同時に操作した可能性があります。")
            elif res.get("status") == "duplicate":
                st.error("⚠️ 他の人が既に発注しました。")
                st.rerun()
            else:
                st.error("❌ 更新失敗。通信環境を確認してください。")