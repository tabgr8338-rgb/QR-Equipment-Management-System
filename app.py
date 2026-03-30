import streamlit as st
import urllib.parse
import html
from datetime import date, timedelta
from supabase import create_client, Client

st.set_page_config(
    page_title="備品管理",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans JP', -apple-system, sans-serif !important; }
.main .block-container { max-width: 480px; padding: 0 16px 80px; margin: 0 auto; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #f5f5f2; }

.card { background:#fff; border:0.5px solid rgba(0,0,0,0.12); border-radius:14px; padding:14px 16px; margin-bottom:8px; }

.badge { display:inline-block; font-size:12px; font-weight:700; padding:5px 12px; border-radius:20px; white-space:nowrap; }
.badge-stock { background:#1D9E75; color:#fff; }
.badge-order { background:#BA7517; color:#fff; }

/* ── メトリクス ── */
.metric-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:12px 0 16px; }
.metric-card { background:#fff; border:0.5px solid rgba(0,0,0,0.12); border-radius:12px; padding:14px 10px; text-align:center; }
.metric-label { font-size:13px; font-weight:700; color:#1a1a18; letter-spacing:0.02em; margin-bottom:6px; }
.metric-value { font-size:32px; font-weight:700; line-height:1; }
.metric-value.green { color:#1D9E75; }
.metric-value.amber { color:#BA7517; }
.metric-value.blue  { color:#185FA5; }

/* ── 備品ヘッダー ── */
.item-header { background:#fff; border:0.5px solid rgba(0,0,0,0.12); border-radius:14px; padding:18px 20px; margin-bottom:12px; }
.item-code { font-size:13px; color:#6b6b67; margin-bottom:4px; }
.item-name { font-size:26px; font-weight:700; color:#1a1a18; margin-bottom:8px; line-height:1.3; }
.item-loc  { font-size:18px; color:#1D9E75; font-weight:700; }

.sec-label { font-size:12px; font-weight:700; color:#1a1a18; letter-spacing:0.07em; text-transform:uppercase; margin:18px 0 8px; padding:0 2px; }

/* ── 情報テーブル ── */
.info-table { width:100%; border-collapse:collapse; }
.info-table td { padding:10px 0; font-size:15px; border-bottom:0.5px solid rgba(0,0,0,0.08); }
.info-table tr:last-child td { border-bottom:none; }
.info-key { color:#6b6b67; width:42%; font-weight:500; }
.info-val { font-weight:600; color:#1a1a18; }

/* ── 備品リストカード（タップ可能） ── */
.item-card {
    background:#fff; border:0.5px solid rgba(0,0,0,0.12);
    border-radius:12px; padding:14px 16px; margin-bottom:8px;
    display:flex; align-items:center; gap:12px;
    cursor:pointer; text-decoration:none;
    transition:background 0.12s;
}
.item-card:hover { background:#f8f8f5; }
.item-card:active { background:#f0f0ec; }
.item-card-name { font-size:15px; font-weight:700; color:#1a1a18; }
.item-card-sub  { font-size:13px; color:#6b6b67; margin-top:3px; }
.item-card-arrow { font-size:18px; color:#c0c0ba; flex-shrink:0; }

/* ── フィルターボタン（選択状態を明確に） ── */
.filter-wrap { display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap; }
.filter-btn {
    padding:8px 18px; font-size:14px; font-weight:700;
    border-radius:20px; cursor:pointer; border:2px solid rgba(0,0,0,0.2);
    background:#fff; color:#6b6b67;
    transition:all 0.15s;
}
.filter-btn.active {
    background:#1a1a18; color:#fff; border-color:#1a1a18;
}

/* ── 確認ボックス ── */
.confirm-box { background:#EBF4FF; border:1px solid #185FA5; border-radius:12px; padding:14px 16px; margin-bottom:8px; }
.confirm-title { font-size:15px; font-weight:700; color:#0C447C; margin-bottom:4px; }
.confirm-msg   { font-size:14px; color:#185FA5; }
.info-box { background:#E1F5EE; border:1px solid #1D9E75; border-radius:12px; padding:14px 16px; margin-bottom:8px; font-size:14px; color:#0F6E56; font-weight:500; line-height:1.7; }

/* ── ボタン ── */
.stButton > button {
    width:100%; padding:14px !important; font-size:16px !important;
    font-weight:700 !important; border-radius:10px !important;
    border:none !important; transition:opacity .15s,transform .1s !important;
    font-family:'Noto Sans JP',sans-serif !important; margin-top:6px !important;
}
.stButton > button:active { transform:scale(0.98) !important; }
div[data-testid="stButton"]:has(button[kind="primary"]) > button { background:#1D9E75 !important; color:#fff !important; }
.btn-blue > button { background:#185FA5 !important; color:#fff !important; }
div[data-testid="stButton"]:has(button[kind="secondary"]) > button { background:#e8e8e4 !important; color:#1a1a18 !important; border:0.5px solid rgba(0,0,0,0.2) !important; }

/* ── テキスト入力 ── */
.stTextInput > div > div > input {
    border-radius:10px !important; border:1px solid rgba(0,0,0,0.2) !important;
    background:#fff !important; padding:12px 14px !important;
    font-size:16px !important; font-family:'Noto Sans JP',sans-serif !important; color:#1a1a18 !important;
}
.stTextInput > div > div > input:focus { border-color:#1D9E75 !important; box-shadow:0 0 0 3px rgba(29,158,117,0.2) !important; }
.stTextInput > label { font-size:14px !important; color:#1a1a18 !important; font-weight:600 !important; }

/* ── タブ ── */
.stTabs [data-baseweb="tab-list"] { background:#d8d8d4; border-radius:10px; padding:3px; gap:2px; }
.stTabs [data-baseweb="tab"] { border-radius:8px; font-size:14px !important; font-weight:700 !important; padding:8px 16px !important; color:#1a1a18 !important; }
.stTabs [aria-selected="true"] { background:#fff !important; color:#1a1a18 !important; }
.stTabs [aria-selected="false"] { color:#1a1a18 !important; opacity:0.6; }

/* ── セレクトボックス ── */
.stSelectbox > div > div { background:#fff !important; border:1px solid rgba(0,0,0,0.2) !important; border-radius:10px !important; color:#1a1a18 !important; font-weight:600 !important; font-size:15px !important; }

/* ── アラート ── */
.stAlert { border-radius:10px !important; font-size:15px !important; }
.stAlert p { color:#1a1a18 !important; font-weight:500 !important; }
.stSpinner > div { border-top-color:#1D9E75 !important; }
hr { border:none; border-top:0.5px solid rgba(0,0,0,0.1); margin:14px 0 !important; }
</style>
""", unsafe_allow_html=True)

def s(v):
    return html.escape(str(v or ""))

@st.cache_resource
def get_supabase() -> Client:
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Supabase接続エラー: {e}")
        st.stop()

supabase = get_supabase()

for k, v in [("confirm_arrival", False), ("done", False), ("user_name", ""),
             ("import_done", False), ("import_msg", ""), ("import_protected", []),
             ("status_filter", "すべて")]:
    if k not in st.session_state:
        st.session_state[k] = v

# URLパラメータ
params      = st.query_params
target_code = str(params.get("code", "")).strip()
base_url    = "https://qremsver2-s72yvfqdyihvvjjz9fbwsw.streamlit.app/"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ダッシュボード
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if not target_code:

    st.markdown("""
    <div style="padding:20px 0 4px;">
        <div style="font-size:24px;font-weight:700;color:#1a1a18;">📦 備品管理</div>
        <div style="font-size:14px;color:#6b6b67;margin-top:3px;">QRコードをスキャンして発注・入荷処理ができます</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        rows = supabase.table("equipment").select(
            "品番,品名,棚,箱,状態,発注者,発注日,発注先"
        ).order("品番").execute().data or []
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        st.stop()

    total    = len(rows)
    ordering = sum(1 for r in rows if r.get("状態") == "発注中")
    in_stock = sum(1 for r in rows if r.get("状態") == "在庫")

    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card"><div class="metric-label">総備品数</div><div class="metric-value blue">{total}</div></div>
        <div class="metric-card"><div class="metric-label">発注中</div><div class="metric-value amber">{ordering}</div></div>
        <div class="metric-card"><div class="metric-label">在庫あり</div><div class="metric-value green">{in_stock}</div></div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 備品一覧", "🕐 発注履歴", "⬆ CSV取込"])

    # ─── 備品一覧 ─────────────────────────────────────────
    with tab1:
        if not rows:
            st.warning("データがありません。「CSV取込」タブからマスターを読み込んでください。")
        else:
            # フィルターボタン（選択状態を明確に表示）
            filters = ["すべて", "在庫", "発注中"]
            cols = st.columns(len(filters))
            for i, f in enumerate(filters):
                with cols[i]:
                    active = st.session_state.status_filter == f
                    label = f"{'✓ ' if active else ''}{f}"
                    if st.button(label, key=f"filter_{f}",
                                 type="primary" if active else "secondary",
                                 use_container_width=True):
                        st.session_state.status_filter = f
                        st.rerun()

            search_q = st.text_input("品名・品番で検索", placeholder="例: インシュロック、M6...")

            filtered = [
                r for r in rows
                if (st.session_state.status_filter == "すべて" or r.get("状態") == st.session_state.status_filter)
                and (not search_q or
                     search_q.lower() in str(r.get("品名","")).lower() or
                     search_q.lower() in str(r.get("品番","")).lower())
            ]
            st.markdown(f"<div style='font-size:13px;color:#6b6b67;margin-bottom:8px;'>{len(filtered)} 件表示中</div>", unsafe_allow_html=True)

            if not filtered:
                st.info("該当する備品がありません。")

            # カードをリンクにして品番ページへ遷移
            for item in filtered:
                is_o  = item.get("状態") == "発注中"
                bc    = "#BA7517" if is_o else "#1D9E75"
                badge = "発注中" if is_o else "在庫"
                bcls  = "badge-order" if is_o else "badge-stock"
                code  = item.get("品番","")
                link  = f"{base_url}?code={urllib.parse.quote(str(code))}"
                sub   = f"👤 {s(item.get('発注者'))}　📅 {s(item.get('発注日'))}" if is_o else f"{s(item.get('棚'))}棚-{s(item.get('箱'))}箱 · {s(item.get('発注先'))}"
                st.markdown(f"""
                <a href="{link}" target="_self" class="item-card" style="border-left:3px solid {bc}; text-decoration:none;">
                    <div style="flex:1;">
                        <div class="item-card-name">{s(item.get('品名','-'))}</div>
                        <div class="item-card-sub">{s(code)} · {sub}</div>
                    </div>
                    <span class="badge {bcls}">{badge}</span>
                    <span class="item-card-arrow">›</span>
                </a>
                """, unsafe_allow_html=True)

    # ─── 発注履歴 ─────────────────────────────────────────
    with tab2:
        period_map    = {"1ヶ月":1, "3ヶ月":3, "6ヶ月":6, "12ヶ月":12}
        period_labels = list(period_map.keys())
        try:
            s_res = supabase.table("settings").select("value").eq("key","history_retention_months").execute()
            saved_months = int(s_res.data[0]["value"]) if s_res.data else 3
        except Exception:
            saved_months = 3
        saved_label = next((k for k,v in period_map.items() if v == saved_months), "3ヶ月")

        st.markdown("<div class='sec-label'>保存期間の設定</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="info-box">
            現在の設定: <strong>{saved_label}</strong> 以内のデータを保存<br>
            期間を変更して「設定を保存して古いデータを削除」を押すと期間外のデータが削除されます。
        </div>
        """, unsafe_allow_html=True)

        new_period = st.selectbox("保存期間を選択", period_labels, index=period_labels.index(saved_label))
        if st.button("🗑 設定を保存して古いデータを削除", type="primary"):
            new_months = period_map[new_period]
            cutoff = (date.today() - timedelta(days=new_months*30)).isoformat()
            with st.spinner("処理中..."):
                supabase.table("settings").upsert(
                    {"key":"history_retention_months","value":str(new_months)}, on_conflict="key"
                ).execute()
                res = supabase.table("order_history").delete().lt("created_at", cutoff).execute()
                deleted = len(res.data) if res.data else 0
            saved_months = new_months
            saved_label  = new_period
            msg = f"✅ 保存期間を「{new_period}」に変更し、{deleted} 件の古いデータを削除しました。" if deleted > 0 \
                  else f"✅ 保存期間を「{new_period}」に変更しました。（削除対象なし）"
            st.success(msg)

        st.markdown("<div class='sec-label'>履歴一覧</div>", unsafe_allow_html=True)
        try:
            since = (date.today() - timedelta(days=saved_months*30)).isoformat()
            history = supabase.table("order_history").select("*").order(
                "created_at", desc=True).gte("created_at", since).limit(200).execute().data or []
        except Exception as e:
            st.error(f"履歴取得エラー: {e}")
            history = []

        st.markdown(f"<div style='font-size:13px;color:#6b6b67;margin-bottom:8px;'>{len(history)} 件（{saved_label}分）</div>", unsafe_allow_html=True)
        if not history:
            st.info("この期間の履歴はありません。")
        for h in history:
            action = h.get("アクション","")
            is_arr = action == "入荷"
            bc     = "#1D9E75" if is_arr else "#BA7517"
            icon   = "✅" if is_arr else "📤"
            st.markdown(f"""
            <div class="item-card" style="border-left:3px solid {bc}; cursor:default;">
                <div style="flex:1;">
                    <div class="item-card-name">{icon} {s(h.get('品名','-'))}</div>
                    <div class="item-card-sub">{s(h.get('品番'))} · 👤 {s(h.get('担当者'))} · 📅 {s(h.get('日付'))}</div>
                </div>
                <span class="badge {'badge-stock' if is_arr else 'badge-order'}">{action}</span>
            </div>
            """, unsafe_allow_html=True)

    # ─── CSV取込 ──────────────────────────────────────────
    with tab3:
        st.markdown("<div class='sec-label'>CSVファイルをアップロード</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            ✅ 状態・発注者・発注日はCSVから読み取りません。<br>
            ✅ 発注中・在庫のステータスは一切変更されません。<br>
            ✅ 品目情報（品名・型式・発注先など）のみ更新します。
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.import_done:
            st.success(st.session_state.import_msg)
            if st.session_state.import_protected:
                st.info(f"🔒 発注中のため保護した品番: {', '.join(st.session_state.import_protected)}")
            if st.button("✅ 閉じる"):
                st.session_state.import_done      = False
                st.session_state.import_msg       = ""
                st.session_state.import_protected = []
                st.rerun()

        uploaded = st.file_uploader("CSVファイルを選択", type=["csv"])
        if uploaded and not st.session_state.import_done:
            import pandas as pd, io
            try:
                df = pd.read_csv(io.BytesIO(uploaded.read()), encoding="utf-8-sig", dtype=str)
                df = df[df["品番"].notna() & ~df["品番"].str.startswith("00-00-000")]
                df = df[df["品名"].notna() & (df["品名"].str.strip() != "")]
                for col in ["状態","発注者","発注日"]:
                    if col in df.columns:
                        df = df.drop(columns=[col])
                df = df.fillna("")
                records = df.to_dict(orient="records")

                st.markdown(f"<div style='font-size:15px;font-weight:600;color:#1a1a18;margin:8px 0;'>📋 {len(records)} 件を検出しました</div>", unsafe_allow_html=True)

                if st.button("⬆ Supabaseに取り込む", type="primary"):
                    progress = st.progress(0, text="準備中...")
                    total_r  = len(records)
                    protected = []

                    with st.spinner("発注中データを確認しています..."):
                        res = supabase.table("equipment").select("品番").eq("状態","発注中").execute()
                        ordering_codes = {r["品番"] for r in (res.data or [])}

                    for i in range(0, total_r, 100):
                        batch = records[i:i+100]
                        for rec in batch:
                            code = str(rec.get("品番","")).strip()
                            if code in ordering_codes:
                                protected.append(code)
                        supabase.table("equipment").upsert(
                            batch, on_conflict="品番", ignore_duplicates=False,
                        ).execute()
                        pct = min((i+100) / total_r, 1.0)
                        progress.progress(pct, text=f"取り込み中... {min(i+100, total_r)}/{total_r} 件")

                    progress.progress(1.0, text="✅ 完了！")
                    st.session_state.import_done      = True
                    st.session_state.import_msg       = f"✅ {total_r} 件の取り込みが完了しました！"
                    st.session_state.import_protected = list(set(protected))
                    st.rerun()

            except Exception as e:
                st.error(f"読み込みエラー: {e}")

    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  QRスキャン後 — 品番ページ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
try:
    result = supabase.table("equipment").select("*").eq("品番", target_code).execute()
except Exception as e:
    st.error(f"データベース接続エラー: {e}")
    st.stop()

if not result.data:
    st.markdown(f"""
    <div style="padding:48px 0;text-align:center;">
        <div style="font-size:40px;margin-bottom:12px;">🔍</div>
        <div style="font-size:18px;font-weight:700;color:#1a1a18;">品番が見つかりません</div>
        <div style="font-size:14px;color:#6b6b67;margin-top:6px;">{s(target_code)}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("← ダッシュボードに戻る", type="secondary"):
        st.query_params.clear()
        st.rerun()
    st.stop()

item     = result.data[0]
status   = item.get("状態","在庫")
is_order = status == "発注中"
border_col = "#BA7517" if is_order else "#1D9E75"
badge_cls  = "badge-order" if is_order else "badge-stock"
badge_lbl  = "発注中" if is_order else "在庫あり"

# ← 戻るリンク（ページ上部）
st.markdown(f"""
<div style="padding:12px 0 4px;">
    <a href="{base_url}" target="_self"
       style="font-size:15px;font-weight:600;color:#1D9E75;text-decoration:none;">
        ← ダッシュボードに戻る
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="item-header" style="border-left:4px solid {border_col};">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div style="flex:1;">
            <div class="item-code">品番: {s(target_code)}</div>
            <div class="item-name">{s(item.get('品名','-'))}</div>
            <div class="item-loc">📍 {s(item.get('棚','-'))} 棚 — {s(item.get('箱','-'))} 箱</div>
        </div>
        <span class="badge {badge_cls}" style="margin-top:4px;">{badge_lbl}</span>
    </div>
</div>
""", unsafe_allow_html=True)

rows_info = [
    ("発注型式", s(item.get("発注型式","-"))),
    ("発注先",   s(item.get("発注先","-"))),
    ("発注数量", f"{s(item.get('発注数量'))} {s(item.get('発注単位'))}"),
    ("発注点",   f"{s(item.get('発注点'))} {s(item.get('発注単位'))}"),
]
if is_order:
    rows_info += [("発注者", s(item.get("発注者","-"))), ("発注日", s(item.get("発注日","-")))]

st.markdown(f"""
<div class='sec-label'>備品情報</div>
<div class="card">
    <table class="info-table">
        {''.join(f"<tr><td class='info-key'>{k}</td><td class='info-val'>{v}</td></tr>" for k,v in rows_info)}
    </table>
</div>
<div style='height:4px'></div>
""", unsafe_allow_html=True)

# ── 発注中フロー ─────────────────────────────────────────
if is_order:
    st.warning("🛑 現在【発注中】のため新規発注はできません。")
    if not st.session_state.confirm_arrival:
        if st.button("✅ 現物が届いた — 入荷処理", type="secondary"):
            st.session_state.confirm_arrival = True
            st.rerun()
    else:
        st.markdown("""
        <div class="confirm-box">
            <div class="confirm-title">確認</div>
            <div class="confirm-msg">ステータスを「在庫あり」に戻します。よろしいですか？</div>
        </div>
        """, unsafe_allow_html=True)
        col_yes, col_no = st.columns(2)
        with col_yes:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("Y — 入荷処理を実行", use_container_width=True):
                try:
                    with st.spinner("更新中..."):
                        res = supabase.table("equipment").update({
                            "状態":"在庫","発注者":None,"発注日":None,
                        }).eq("品番", target_code).eq("状態","発注中").execute()
                        if not res.data:
                            st.error("⚠️ ステータスがすでに変更されています。画面を更新してください。")
                            st.stop()
                        supabase.table("order_history").insert({
                            "品番":target_code,"品名":item.get("品名"),
                            "アクション":"入荷","担当者":item.get("発注者"),
                            "日付":str(date.today()),
                        }).execute()
                    st.session_state.confirm_arrival = False
                    st.success("✅ 在庫に戻しました！")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"更新エラー: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        with col_no:
            if st.button("N — キャンセル", type="secondary", use_container_width=True):
                st.session_state.confirm_arrival = False
                st.rerun()

# ── 在庫あり → 発注フロー ────────────────────────────────
else:
    if st.session_state.done:
        st.success("✅ 発注済みです。このウィンドウを閉じてください。")
        st.stop()

    st.markdown("<div class='sec-label'>発注担当者</div>", unsafe_allow_html=True)
    requester = st.text_input("あなたの名前", value=st.session_state.user_name, placeholder="例：山田")
    if requester:
        st.session_state.user_name = requester

    if st.button("🚀 発注を確定する", type="primary"):
        if not requester.strip():
            st.warning("⚠️ 担当者名を入力してください。")
        else:
            try:
                with st.spinner("送信中..."):
                    res = supabase.table("equipment").update({
                        "状態":"発注中","発注者":requester.strip(),"発注日":str(date.today()),
                    }).eq("品番", target_code).eq("状態","在庫").execute()
                    if not res.data:
                        st.error("⚠️ すでに他の人が発注しました。画面を更新して確認してください。")
                        st.stop()
                    supabase.table("order_history").insert({
                        "品番":target_code,"品名":item.get("品名"),
                        "アクション":"発注","担当者":requester.strip(),"日付":str(date.today()),
                    }).execute()
                st.session_state.done = True
                subject = f"【備品発注依頼】{item.get('品名','')}（{item.get('発注型式','')}）"
                body = (
                    f"いつもお世話になっております。\n以下の備品を発注いたします。\n\n"
                    f"品名　　: {item.get('品名','')}\n型式　　: {item.get('発注型式','')}\n"
                    f"発注数量: {item.get('発注数量','')} {item.get('発注単位','')}\n"
                    f"依頼者　: {requester.strip()}\n日付　　: {date.today()}\n\nよろしくお願いいたします。"
                )
                mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                st.success("✅ 発注を記録しました！")
                st.balloons()
                st.link_button("📧 発注メールを作成する →", mailto, use_container_width=True)
            except Exception as e:
                st.error(f"更新エラー: {e}")
