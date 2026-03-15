import streamlit as st
import requests
import urllib.parse

# ==========================================
# 1. 基本設定
# ==========================================
# Streamlit Cloud の Secrets に設定した GAS_URL を読み込む
try:
    GAS_URL = st.secrets["https://script.google.com/macros/s/AKfycbxzSvCpR-wSPLaz6lgfWYRWUe23gIlQjS8Wgyys13HML6tic_29QPAFmy_j08WPmqQI/exec"]
except:
    st.error("Secrets に GAS_URL が設定されていません。")
    st.stop()

# ==========================================
# 2. GAS API 呼び出し関数
# ==========================================
def get_item(code: str):
    """GAS doGet で品番検索"""
    try:
        # 品番をパラメータに付けてGET送信
        res = requests.get(GAS_URL, params={"code": code}, timeout=10)
        res.raise_for_status()
        result = res.json()
        if result.get("status") == "ok":
            return result["item"]
        return None
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return None

def post_action(payload: dict) -> bool:
    """GAS doPost で状態更新"""
    try:
        # 更新内容をJSONでPOST送信
        res = requests.post(GAS_URL, json=payload, timeout=10)
        res.raise_for_status()
        # JSONを解析して status が ok かチェック
        return res.json().get("status") == "ok"
    except Exception as e:
        st.error(f"更新エラー: {e}")
        return False

# ==========================================
# 3. UI・メイン処理
# ==========================================
st.set_page_config(page_title="工場備品管理システム", layout="centered")
st.title("📦 工場備品 QR発注システム")

# URLパラメータ (?code=...) または手入力から品番を取得
params = st.query_params
url_code = params.get("code", "")
code = st.text_input("QRコード（品番）を入力してください", value=url_code)

if not code:
    st.info("QRコードをスキャンするか、品番を入力してください。")
    st.stop()

target_code = str(code).strip()

# データ取得（GAS経由）
with st.spinner("最新データを取得中..."):
    item = get_item(target_code)

if item is None:
    st.error(f"品番「{target_code}」は見つかりませんでした。")
    st.stop()

st.success(f"照合成功: {item.get('品名', '')}")
st.markdown("---")

# 備品情報の表示
st.subheader(f"品名: {item.get('品名', '')}")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**型式:** {item.get('発注型式', '')}")
    st.write(f"**場所:** {item.get('棚', '')}-{item.get('箱', '')}")
with col2:
    st.write(f"**発注数:** {item.get('発注数量', '')} {item.get('発注単位', '')}")
    st.write(f"**発注先:** {item.get('発注先', '')}")

st.markdown("---")

# --- 状態に応じた処理 ---
status = str(item.get("状態", "在庫"))

if status == "発注中":
    st.warning(f"⚠️ 現在発注中です（担当: {item.get('発注者', '')} / 日付: {item.get('発注日', '')}）")
    if st.button("✅ 入荷完了（在庫に戻す）", use_container_width=True):
        if post_action({"action": "arrival", "code": target_code}):
            st.success("ステータスを更新しました。")
            st.rerun()
else:
    st.info(f"現在の状態: {status}")
    requester = st.text_input("あなたの名前を入力してください")
    
    if st.button("📧 発注ステータス更新 ＆ メール作成", use_container_width=True):
        if not requester:
            st.error("お名前を入力してください。")
        else:
            # 1. GASへ送信（発注アクション）
            ok = post_action({
                "action": "order",
                "code": target_code,
                "requester": requester
            })
            
            # 2. メールURL生成
            subject = f"【備品発注】{item.get('品名', '')}"
            body = f"品名:{item.get('品名', '')}\n型式:{item.get('発注型式', '')}\n数量:{item.get('発注数量', '')}\n発注者:{requester}"
            mailto_url = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            
            # 3. リンクボタン表示（Safari対策）
            st.link_button("📬 メールアプリを起動して送信", mailto_url, type="primary", use_container_width=True)
            
            if ok:
                st.success("シートを更新しました。上のボタンから送信してください。")