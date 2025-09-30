# pages/1_チェックイン.py

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import openpyxl

# app.pyから定数とキーをインポート
from app import ID_COLUMN, NAME_COLUMN, DEPT_COLUMN, ATTEND_COLUMN, TIME_COLUMN, ROSTER_DF_KEY 

st.set_page_config(page_title="チェックイン", layout="wide")

st.title("バーコードリーダー：出席チェックイン")
st.markdown("---")

if ROSTER_DF_KEY not in st.session_state:
    st.error("⚠️ メインページで名簿ファイルをアップロードしてください。")
else:
    # データフレームを取得
    df = st.session_state[ROSTER_DF_KEY]
    
    # 状態管理のためのキー
    if 'last_status' not in st.session_state:
         st.session_state['last_status'] = {'type': 'info', 'message': 'IDスキャンをお待ちしています...'}

    def display_status(type, message):
        """直感的なステータス表示（セッションステートで更新）"""
        st.session_state['last_status'] = {'type': type, 'message': message}
        # この関数を呼び出した後、UI全体を再実行して最新の状態を表示させる

    # 大きなステータス表示エリア
    status_placeholder = st.empty()
    
    # --- ID入力フォーム ---
    with st.form("checkin_form", clear_on_submit=True):
        st.subheader("ID/学籍番号入力欄")
        # バーコードリーダーから入力されることを想定し、フォーカスが当たるように設定
        scanned_id = st.text_input("IDをスキャンまたは入力してください", key="scanned_id_input").strip()
        submit_button = st.form_submit_button("チェックイン処理実行")
        
        if submit_button and scanned_id:
            # --- check.pyのロジックを実行 ---
            matched = df[df[ID_COLUMN] == scanned_id]
            
            if not matched.empty:
                # 既存の人物の場合：出席を記録
                i = matched.index[0]
                
                # 既に「出席」の場合は重複チェックとして警告
                if df.loc[i, ATTEND_COLUMN] == "出席":
                    display_status('warning', f"**⚠️ {df.loc[i, NAME_COLUMN]}** 様は既に**{df.loc[i, TIME_COLUMN]}**に出席記録があります。")
                    st.toast("既にチェックイン済みです")
                else:
                    # 未出席の場合に出席を記録
                    name = df.loc[i, NAME_COLUMN]
                    dept = df.loc[i, DEPT_COLUMN]
                    now = datetime.now().strftime("%Y/%m/%d %H:%M")

                    df.loc[i, ATTEND_COLUMN] = "出席"
                    df.loc[i, TIME_COLUMN] = now
                    st.session_state[ROSTER_DF_KEY] = df # セッションステートを更新
                    
                    display_status('success', f"**✅ {name}**（{dept}）：**{now}** に出席を記録しました。")
                    st.toast("チェックイン完了")
            else:
                # 新規登録の場合：氏名入力フォームを呼び出し
                display_status('error', "❌ このIDは名簿に登録されていません。下記フォームで新規登録してください。")
                st.session_state['new_id_to_register'] = scanned_id
            
    # --- 新規登録フォーム（IDが見つからなかった場合のみ表示） ---
    if 'new_id_to_register' in st.session_state and st.session_state['new_id_to_register']:
        scanned_id_to_register = st.session_state['new_id_to_register']
        
        # 新規登録ロジック
        def register_new_person(scanned_id, name, dept):
            now = datetime.now().strftime("%Y/%m/%d %H:%M")
            new_record = {
                ID_COLUMN: scanned_id,
                NAME_COLUMN: name,
                DEPT_COLUMN: dept,
                ATTEND_COLUMN: "出席",
                TIME_COLUMN: now
            }
            # 新しいレコードをDataFrameに追加
            new_df = pd.concat([st.session_state[ROSTER_DF_KEY], pd.DataFrame([new_record])], ignore_index=True)
            st.session_state[ROSTER_DF_KEY] = new_df # セッションステートを更新
            
            display_status('success', f"**✅ {name}**（{dept}）：**{now}** に新規登録＆出席記録しました。")
            del st.session_state['new_id_to_register'] # 登録完了後、ステートをクリア
            st.toast("新規登録完了")

        with st.expander(f"新規登録フォーム (ID: {scanned_id_to_register})", expanded=True):
             with st.form("new_person_form"):
                new_name = st.text_input("氏名を入力してください").strip()
                new_dept = st.selectbox("所属を選択してください", ["一般", "職員", "来賓"], index=0)
                register_button = st.form_submit_button("新規登録＆チェックイン")
                
                if register_button and new_name:
                    register_new_person(scanned_id_to_register, new_name, new_dept)
    
    # --- 画面上部のステータス表示を更新 ---
    status = st.session_state['last_status']
    if status['type'] == 'success':
        status_placeholder.success(f"# {status['message']}")
    elif status['type'] == 'warning':
        status_placeholder.warning(f"# {status['message']}")
    elif status['type'] == 'error':
        status_placeholder.error(f"# {status['message']}")
    else:
        status_placeholder.info(f"# {status['message']}")


    st.markdown("---")
    # ファイルダウンロードエリア
    st.subheader("名簿データ管理")
    
    # DataFrameをExcel形式のバイトデータに変換
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # check.pyのSHEET_NAME（出席者まとめ）を適用
        df.to_excel(writer, sheet_name="出席者まとめ", index=False) 
    excel_data = output.getvalue()
    
    st.download_button(
        label="🔽 更新済み名簿ファイルをダウンロード",
        data=excel_data,
        file_name=f"更新済み名簿_{datetime.now().strftime('%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.caption("最新のデータは、左側の「状況確認」ページでも確認できます。")
