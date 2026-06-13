# 성적 처리 프로그램 (sungjuk.py)
import streamlit as st
import pandas as pd
import sqlite3
import os
import streamlit.components.v1 as components

DB_DIR = r'.\db'
DB_FILE = os.path.join(DB_DIR, 'MembersDB.db')

def init_db():
    """SQLite 데이터베이스 및 테이블 초기화"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=15)
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS jumsu (
                name TEXT PRIMARY KEY,
                kor INTEGER,
                eng INTEGER,
                math INTEGER
            )
        ''')
        conn.commit()
    finally:
        conn.close()

def get_grade(average):
    """평균 점수를 바탕으로 학점을 반환하는 함수"""
    if average >= 90:
        return 'A'
    elif average >= 80:
        return 'B'
    elif average >= 70:
        return 'C'
    elif average >= 60:
        return 'D'
    else:
        return 'F'

def set_focus(label):
    """지정된 라벨(aria-label)을 가진 입력창으로 커서를 자동 이동시키는 기능"""
    components.html(
        f"""
        <script>
            setTimeout(function() {{
                var inputs = window.parent.document.querySelectorAll('input[aria-label="{label}"]');
                if (inputs.length > 0) {{
                    inputs[0].focus();
                }}
            }}, 100);
        </script>
        """,
        height=0
    )

def main():
    st.title("📝 성적 처리 프로그램")
    
    # SQLite DB 초기화 (세션당 1회만 실행하여 DB Lock 방지)
    if 'db_initialized' not in st.session_state:
        init_db()
        st.session_state.db_initialized = True

    # 세션 상태로 모드 관리 (상단 탭/메뉴 역할)
    if 'mode' not in st.session_state:
        st.session_state.mode = '조회'

    # 상단 메뉴 버튼 구성
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("➕ 등록", use_container_width=True):
        st.session_state.mode = '등록'
    if col2.button("✏️ 수정", use_container_width=True):
        st.session_state.mode = '수정'
    if col3.button("️🗑️ 삭제", use_container_width=True):
        st.session_state.mode = '삭제'
    if col4.button("🔍 조회", use_container_width=True):
        st.session_state.mode = '조회'

    st.markdown("---")
    
    # ----------------------------------------
    # 1. 등록 모드 (데이터 입력)
    # ----------------------------------------
    if st.session_state.mode == '등록':
        st.header("1. 성적 등록")
        
        if 'input_rows' not in st.session_state:
            st.session_state.input_rows = 3
            
        if st.button("➕ 입력 칸 추가"):
            st.session_state.input_rows += 1

        with st.form("multi_input_form", clear_on_submit=True):
            cols = st.columns(4)
            cols[0].write("**이름**")
            cols[1].write("**국어**")
            cols[2].write("**영어**")
            cols[3].write("**수학**")
            
            for i in range(st.session_state.input_rows):
                cols = st.columns(4)
                with cols[0]:
                    st.text_input(f"이름_{i}", label_visibility="collapsed", key=f"name_{i}")
                with cols[1]:
                    st.number_input(f"국어_{i}", min_value=0, max_value=100, step=1, label_visibility="collapsed", key=f"kor_{i}")
                with cols[2]:
                    st.number_input(f"영어_{i}", min_value=0, max_value=100, step=1, label_visibility="collapsed", key=f"eng_{i}")
                with cols[3]:
                    st.number_input(f"수학_{i}", min_value=0, max_value=100, step=1, label_visibility="collapsed", key=f"math_{i}")
                    
            submitted = st.form_submit_button("등록 완료")

        # 등록 모드일 때 첫 번째 이름 입력칸으로 포커스 이동
        set_focus("이름_0")

        if submitted:
            conn = sqlite3.connect(DB_FILE, timeout=15)
            try:
                c = conn.cursor()
                
                # 1. 폼에 입력된 이름 추출 및 입력칸 자체 중복 검사
                input_names = []
                for i in range(st.session_state.input_rows):
                    s_name = st.session_state[f"name_{i}"].strip()
                    if s_name:
                        input_names.append(s_name)
                        
                if not input_names:
                    st.warning("학생 이름을 하나 이상 입력해주세요.")
                elif len(input_names) != len(set(input_names)):
                    st.error("입력하신 이름 중 중복된 이름이 있습니다. 중복 없이 입력해 주세요.")
                else:
                    # 2. DB에 이미 존재하는 이름인지 사전 검사
                    placeholders = ','.join('?' for _ in input_names)
                    c.execute(f"SELECT name FROM jumsu WHERE name IN ({placeholders})", input_names)
                    existing_names = [row[0] for row in c.fetchall()]
                    
                    if existing_names:
                        st.error(f"이미 성적 등록이 완료된 학생이 포함되어 있습니다: {', '.join(existing_names)} (전체 등록 취소)")
                    else:
                        # 3. 중복이 전혀 없을 때만 전체 데이터 INSERT
                        added_count = 0
                        for i in range(st.session_state.input_rows):
                            s_name = st.session_state[f"name_{i}"].strip()
                            if s_name:
                                kor = st.session_state[f"kor_{i}"]
                                eng = st.session_state[f"eng_{i}"]
                                math = st.session_state[f"math_{i}"]
                                
                                c.execute('''
                                    INSERT INTO jumsu (name, kor, eng, math) 
                                    VALUES (?, ?, ?, ?)
                                ''', (s_name, kor, eng, math))
                                added_count += 1
                        conn.commit()
                        st.success(f"{added_count}명의 학생 성적이 성공적으로 등록되었습니다.")
            finally:
                conn.close()

    # ----------------------------------------
    # 2. 수정 모드 (기존 데이터 업데이트)
    # ----------------------------------------
    elif st.session_state.mode == '수정':
        st.header("2. 성적 수정")
        conn = sqlite3.connect(DB_FILE, timeout=15)
        try:
            df_names = pd.read_sql_query("SELECT name FROM jumsu", conn)
            
            if df_names.empty:
                st.info("등록된 데이터가 없습니다. 먼저 학생 성적을 등록해주세요.")
            else:
                student_list = df_names['name'].tolist()
                target_name = st.selectbox("수정할 학생 이름 선택", student_list)
                
                c = conn.cursor()
                c.execute("SELECT kor, eng, math FROM jumsu WHERE name=?", (target_name,))
                row = c.fetchone()
                
                with st.form("modify_form"):
                    st.write(f"**{target_name}** 학생 점수 수정")
                    new_kor = st.number_input("국어", value=row[0], min_value=0, max_value=100, step=1)
                    new_eng = st.number_input("영어", value=row[1], min_value=0, max_value=100, step=1)
                    new_math = st.number_input("수학", value=row[2], min_value=0, max_value=100, step=1)
                    
                    if st.form_submit_button("수정 완료"):
                        c.execute("UPDATE jumsu SET kor=?, eng=?, math=? WHERE name=?", (new_kor, new_eng, new_math, target_name))
                        conn.commit()
                        st.success(f"'{target_name}' 학생의 성적이 성공적으로 수정되었습니다.")
        finally:
            conn.close()

    # ----------------------------------------
    # 3. 삭제 모드 (개별 데이터 삭제)
    # ----------------------------------------
    elif st.session_state.mode == '삭제':
        st.header("3. 성적 삭제")
        conn = sqlite3.connect(DB_FILE, timeout=15)
        try:
            df_names = pd.read_sql_query("SELECT name FROM jumsu", conn)
            
            if df_names.empty:
                st.warning("삭제할 학생 성적이 없습니다.")
            else:
                student_list = df_names['name'].tolist()
                target_name = st.selectbox("삭제할 학생 이름 선택", student_list)
                
                if st.button("삭제 완료"):
                    c = conn.cursor()
                    c.execute("DELETE FROM jumsu WHERE name=?", (target_name,))
                    conn.commit()
                    st.success(f"'{target_name}' 학생의 성적이 성공적으로 삭제되었습니다.")
                    st.rerun()
        finally:
            conn.close()

    # ----------------------------------------
    # 4. 조회 모드 (데이터 검색 및 출력)
    # ----------------------------------------
    elif st.session_state.mode == '조회':
        st.header("4. 성적 조회")
        
        search_keyword = st.text_input("🔍 이름으로 검색 (전체 조회 시 비워두세요)")
        
        # 조회 모드일 때 검색어 입력칸으로 포커스 이동
        set_focus("🔍 이름으로 검색 (전체 조회 시 비워두세요)")
        
        conn = sqlite3.connect(DB_FILE, timeout=15)
        try:
            if search_keyword.strip():
                df_db = pd.read_sql_query("SELECT * FROM jumsu WHERE name LIKE ?", conn, params=('%' + search_keyword.strip() + '%',))
            else:
                df_db = pd.read_sql_query("SELECT * FROM jumsu", conn)
        finally:
            conn.close()

        if df_db.empty:
            st.info("현재 저장된 성적 데이터가 없습니다. (DB가 새로 생성되었을 수 있으니 [➕ 등록] 메뉴에서 먼저 데이터를 추가해 주세요.)")
        else:
            table_data = []
            for index, row in df_db.iterrows():
                total = row['kor'] + row['eng'] + row['math']
                avg = total / 3
                grade = get_grade(avg)
                
                table_data.append({
                    "이름": row['name'],
                    "국어": row['kor'],
                    "영어": row['eng'],
                    "수학": row['math'],
                    "총점": total,
                    "평균": f"{avg:.2f}",
                    "학점": grade
                })
                
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            
        st.markdown("---")
        if st.button("🚨 모든 데이터 초기화 (전체 삭제)"):
            conn = sqlite3.connect(DB_FILE, timeout=15)
            try:
                c = conn.cursor()
                c.execute('DELETE FROM jumsu')
                conn.commit()
            finally:
                conn.close()
            st.success("모든 데이터가 삭제되었습니다.")
            st.rerun()

if __name__ == "__main__":
    main()
