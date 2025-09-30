# pages/2_状況確認.py

import streamlit as st
import pandas as pd
from collections import Counter
import io
import openpyxl

# app.pyから定数とキーをインポート
from app import ROSTER_DF_KEY

st.set_page_config(page_title="状況確認", layout="wide")

st.title("📊 出席・集計状況確認レポート")
st.markdown("---")

# --- 3. print.py のロジックをWebアプリ用に調整 ---

def run_analysis_web(delegation_file_bytes, current_roster_df):
    """
    アップロードされた委任状ファイルと現在の名簿DFを使って分析を実行
    (print.pyのmain関数ロジックを改変)
    """
    try:
        # 1. 委任状データ読み込み・flatten
        all_data_1 = []
        # BytesIOでファイルデータをPandasに渡す
        sheets_1 = pd.read_excel(io.BytesIO(delegation_file_bytes), sheet_name=None, engine="openpyxl")
        for name, df in sheets_1.items():
            flattened = df.values.flatten()
            all_data_1.extend([str(x) for x in flattened if pd.notna(x)])
        
        # 2. 当日参加者データ（現在の名簿DF）からIDを抽出
        # check.pyの名簿は「学籍番号」列にデータが集中しているため、これを使用
        all_data_2 = [str(x) for x in current_roster_df['学籍番号'].values.flatten() if pd.notna(x)]
        
        
        # --- 重複チェックと集計 (print.py ロジック) ---
        
        # 委任状データ
        counter1 = Counter(all_data_1)
        unique_list1 = list(counter1.keys())
        # 重複項目と重複数（削除数）を計算
        duplicates1 = {k: v for k, v in counter1.items() if v > 1}
        duplicate_count1 = sum(v - 1 for v in counter1.values() if v > 1)

        # 当日参加者データ（名簿）
        counter2 = Counter(all_data_2)
        unique_list2 = list(counter2.keys())
        duplicates2 = {k: v for k, v in counter2.items() if v > 1}
        duplicate_count2 = sum(v - 1 for v in counter2.values() if v > 1)

        # 集合演算
        set1 = set(unique_list1)
        set2 = set(unique_list2)
        total_unique_set = set1 | set2  # 和集合（重複なしの合計人数）
        both_present_set = set1 & set2  # 積集合（両方に載っている人）

        # 最終レポート (print.py のフルカウントは10905を流用)
        full_count = 10905 
        total_unique_count = len(total_unique_set)
        
        st.session_state['analysis_result'] = {
            'unique_delegation': len(set1),
            'unique_attendee': len(set2),
            'duplicate_in_delegation': len(duplicates1),
            'total_unique': total_unique_count,
            'both_present': len(both_present_set),
            'full_count': full_count
        }

    except Exception as e:
        st.error(f"分析中にエラーが発生しました: {e}")
        st.exception(e)
        st.session_state['analysis_result'] = None

# --- UIメインロジック ---

if ROSTER_DF_KEY not in st.session_state:
    st.error("⚠️ メインページで名簿ファイルをアップロードしてください。")
else:
    current_roster_df = st.session_state[ROSTER_DF_KEY]
    
    # リアルタイム出席者数 (「出席」と記録されている行をカウント)
    attendee_count = len(current_roster_df[current_roster_df['出欠席'] == '出席'])
    roster_size = len(current_roster_df)
    
    st.subheader("名簿データ (リアルタイム)")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("👥 現在のチェックイン済み人数", value=attendee_count, delta=f"名簿登録者 {roster_size} 人中")
    with col_b:
        st.metric("⏳ 未チェックイン人数", value=roster_size - attendee_count)

    st.markdown("---")
    
    # --- print.py 分析エリア ---
    st.subheader("委任状との統合分析レポート")
    
    delegation_file = st.file_uploader(
        "委任状ファイル（Excel: 例. 委任状2025.xlsx）をアップロードしてください", 
        type=['xlsx'], 
        key="uploader_delegation"
    )

    if delegation_file:
        if st.button("統合分析を実行"):
            with st.spinner("分析を実行中..."):
                file_bytes = delegation_file.getvalue()
                run_analysis_web(file_bytes, current_roster_df)

    if 'analysis_result' in st.session_state and st.session_state['analysis_result']:
        results = st.session_state['analysis_result']
        
        st.subheader("統合分析結果 (重複排除済み)")
        col1, col2, col3 = st.columns(3)
        
        col1.metric("総会員数 (基数)", value=f"{results['full_count']:,}人")
        col2.metric("📋 委任状の一意な人数", value=f"{results['unique_delegation']:,}人")
        col3.metric("👤 当日名簿の一意な人数", value=f"{results['unique_attendee']:,}人")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col4, col5 = st.columns(2)
        col4.metric(
            "⭐ 最終的な一意な合計人数", 
            value=f"{results['total_unique']:,}人",
            help="委任状と当日名簿を統合し、重複を排除した人数です。"
        )
        col5.metric(
            "🔀 重複して載っている人数", 
            value=f"{results['both_present']:,}人",
            help="委任状と当日名簿の両方にIDが載っている人数です。"
        )
        
        st.markdown("---")
        st.markdown("### 📜 最終レポートテキスト")
        st.code(f"""
〇令和7年5月1日時点の学友会会員数：{results['full_count']}名
◎委任状と当日参加者リストを統合した一意な人数：{results['total_unique']}名
△委任状、当日参加者リストの重複を除去した上での重複者数（両方に載っている人）：{results['both_present']}名
        """)

    st.markdown("---")
    st.subheader("名簿データプレビュー")
    st.dataframe(current_roster_df.sort_values('チェックイン', ascending=False), use_container_width=True)
