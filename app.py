import streamlit as st
import requests
import urllib.parse

# ===== 設定 =====
GAS_URL = "https://script.google.com/macros/s/AKfycbzTfWNIiGoPKZtLlTVBQGIFGDstVTNNGShGtpbK61ce_JS1tslkt0UHGdMRAyRIY98_/exec"

# 常に最新を取得するため、キャッシュ（@st.cache_data）は使用しない
def fetch_item(code):
    try:
        response = requests.get(f"{GAS_URL}?code={code}")
        return response.json()
    except:
        return {"status": "error"}

st.set_page_config(page_title="工場備品発注システム", layout="centered")
st.title("📦 工場備品 QR発注システム")

# URLパラメータ取得
code = st.query_params.get("code", "")
code = st.text_input("QRコード（品番）", value=code)

if code:
    res = fetch_item(code)
    
    if res["status"] == "not_found":
        st.error("品番が見つかりません。")
    elif res["status"] == "ok":
        item = res["item"]
        st.subheader(f"品名: {item['品名']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**型式:** {item['発注型式']}")
            st.write(f"**場所:** {item['棚']}-{item['箱']}")
        with col2:
            st.write(f"**発注数:** {item['発注数量']} {item['発注単位']}")
            st.write(f"**発注先:** {item['発注先']}")

        if item["状態"] == "発注中":
            st.warning(f"⚠️ 発注中 ({item['発注者']} / {item['発注日']})")
            if st.button("✅ 入荷完了（在庫に戻す）", use_container_width=True):
                requests.post(GAS_URL, json={"action": "arrival", "code": code})
                st.rerun()
        else:
            requester = st.text_input("あなたの名前を入力")
            if st.button("📝 発注ステータスに更新（メール作成）", use_container_width=True):
                if not requester:
                    st.error("名前を入力してください。")
                else:
                    subject = f"【備品発注】{item['品名']}"
                    body = f"品名:{item['品名']}\n型式:{item['発注型式']}\n数量:{item['発注数量']}\n発注者:{requester}"
                    mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                    
                    # GAS更新
                    requests.post(GAS_URL, json={"action": "order", "code": code, "requester": requester})
                    
                    # Safari対策：リンクボタンでメール起動
                    st.link_button("📬 メールアプリを起動して送信", mailto, type="primary", use_container_width=True)
                    st.success("ステータスを更新しました。上のボタンを押して送信を完了してください。")