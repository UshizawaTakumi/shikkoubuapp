# app.py

import streamlit as st
import pandas as pd

# --- 1. 定数設定 ---
ID_COLUMN = "学籍番号"
NAME_COLUMN = "氏名"
DEPT_COLUMN = "所属"
ATTEND_COLUMN = "出欠席"
TIME_COLUMN = "チェックイン"

# Streamlitのセッションステートにデータを保持するキー
ROSTER_DF_KEY = 'roster_df'

# --- 2. ページ設定とUI ---
st.set_page_config(
    page_title="参加者名簿管理システム",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤝 参加者名簿管理システム")
st.markdown("---")
st.subheader("ステップ1: 名簿ファイルのアップロード")

# ファイルアップローダー
uploaded_file = st.file_uploader(
    "当日参加者名簿ファイル（Excel: 例. 当日参加者まとめ0524.xlsx）をアップロードしてください", 
    type=['xlsx'], 
    key="uploader_roster"
)

def load_roster_web(uploaded_file):
    """アップロードされたExcelファイルをDataFrameとして読み込み、セッションステートに保存"""
    try:
        # Excelファイルを読み込み
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        # ID列を文字列型に統一
        df[ID_COLUMN] = df[ID_COLUMN].astype(str)
        
        # check.py のロジックを踏襲し、出欠席/チェックイン列が存在しない場合は追加
        if ATTEND_COLUMN not in df.columns:
            df[ATTEND_COLUMN] = "欠席" # 初期値
        if TIME_COLUMN not in df.columns:
            df[TIME_COLUMN] = "" # 初期値
        
        st.session_state[ROSTER_DF_KEY] = df
        st.success("✅ 名簿ファイルが読み込まれ、全ページで利用可能になりました。")
        st.dataframe(df.head(), use_container_width=True)
        st.info("左側のサイドバーから「チェックイン」または「状況確認」ページへ進んでください。")

    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")

# ファイルがアップロードされ、かつDataFrameがセッションステートにまだない場合に読み込み
if uploaded_file and ROSTER_DF_KEY not in st.session_state:
    load_roster_web(uploaded_file)
    
if ROSTER_DF_KEY not in st.session_state:
     st.warning("ファイルをアップロードすると、サイドバーのページにアクセスできるようになります。")

# サイドバーの説明
with st.sidebar:
    st.subheader("操作手順")
    st.markdown("""
    1. **`app.py`** で名簿ファイルをアップロード
    2. **`1. チェックイン`** ページでバーコードをスキャン
    3. **`2. 状況確認`** ページで分析レポートを表示
    """)
