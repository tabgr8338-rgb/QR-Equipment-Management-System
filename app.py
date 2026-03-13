import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

DB = "inventory.db"
CSV = "items.csv"

# ----------------------------
# DB接続
# ----------------------------

conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# ----------------------------
# 初期テーブル作成
# ----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS items (
code TEXT PRIMARY KEY,
name TEXT,
location TEXT,
box TEXT,
order_qty INTEGER,
status TEXT,
person TEXT,
order_date TEXT
)
""")

conn.commit()

# ----------------------------
# CSV → DB 初期登録
# ----------------------------

df = pd.read_csv(CSV, encoding="cp932")

df["科目"] = df["科目"].astype(str).str.zfill(2)
df["種類"] = df["種類"].astype(str).str.zfill(2)
df["ID"] = df["ID"].astype(str).str.zfill(3)
df["箱"] = df["箱"].astype(str).str.zfill(2)

df["code"] = (
df["科目"]+"-"+df["種類"]+"-"+df["ID"]+"-"+df["棚"]+"-"+df["箱"]
)

for _,r in df.iterrows():

    cursor.execute("""
    INSERT OR IGNORE INTO items
    VALUES (?,?,?,?,?,?,?,?)
    """,(
        r["code"],
        r["品名"],
        r["棚"],
        r["箱"],
        r["発注量"],
        "未発注",
        "",
        ""
    ))

conn.commit()

# ----------------------------
# 画面
# ----------------------------

st.title("工場備品QR発注")

code = st.text_input("QRコード")

if code:

    item = cursor.execute(
    "SELECT * FROM items WHERE code=?",
    (code,)
    ).fetchone()

    if not item:
        st.error("備品が見つかりません")
        st.stop()

    name = item[1]
    location = item[2]
    box = item[3]
    qty = item[4]
    status = item[5]

    st.subheader(name)
    st.write("棚:",location)
    st.write("箱:",box)
    st.write("状態:",status)

    person = st.text_input("発注者")

# ----------------------------
# 発注
# ----------------------------

    if status == "未発注":

        if st.button("発注"):

            if person == "":
                st.error("名前入力")
                st.stop()

            cursor.execute("""
            UPDATE items
            SET status='発注中',
                person=?,
                order_date=?
            WHERE code=?
            """,(person,datetime.now(),code))

            conn.commit()

            subject = f"備品発注 {name}"

            body = f"""
品名:{name}
品番:{code}
数量:{qty}
発注者:{person}
"""

            url = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

            st.success("発注登録しました")

            st.markdown(f"[メール送信]( {url} )")

# ----------------------------
# 入荷
# ----------------------------

    if status == "発注中":

        if st.button("入荷処理"):

            cursor.execute("""
            UPDATE items
            SET status='未発注',
                person='',
                order_date=''
            WHERE code=?
            """,(code,))

            conn.commit()

            st.success("入荷登録しました")