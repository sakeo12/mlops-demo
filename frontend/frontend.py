import os
import time

import pymysql
import requests
import streamlit as st


# =========================
# 기본 설정
# =========================

API_URL = os.getenv(
    "API_URL",
    "http://server:8000/summarize"
)

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_NAME = os.getenv("DB_NAME", "summarize_db")


# =========================
# MySQL 연결
# =========================

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4"
    )


# =========================
# 테이블 생성
# =========================

def init_db():
    # MySQL 컨테이너가 처음 시작될 때 준비 시간이 필요할 수 있음
    for _ in range(10):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url TEXT NOT NULL,
                    model VARCHAR(255) NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()
            return

        except pymysql.MySQLError:
            time.sleep(2)

    st.error("MySQL DB에 연결할 수 없습니다.")


# =========================
# 요약 결과 저장
# =========================

def save_summary(url, model, summary):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO summaries (url, model, summary)
        VALUES (%s, %s, %s)
    """, (url, model, summary))

    conn.commit()
    cursor.close()
    conn.close()


# =========================
# 히스토리 조회
# =========================

def get_history(keyword=""):
    conn = get_db_connection()
    cursor = conn.cursor()

    if keyword:
        search = f"%{keyword}%"

        cursor.execute("""
            SELECT id, url, model, summary, created_at
            FROM summaries
            WHERE url LIKE %s
               OR model LIKE %s
               OR summary LIKE %s
            ORDER BY id DESC
        """, (search, search, search))

    else:
        cursor.execute("""
            SELECT id, url, model, summary, created_at
            FROM summaries
            ORDER BY id DESC
        """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


# =========================
# DB 초기화
# =========================

init_db()


# =========================
# Streamlit 화면
# =========================

st.set_page_config(
    page_title="Hugging Face Summarizer"
)

st.title("Hugging Face 모델 기반 텍스트 요약")


# =========================
# 메뉴
# =========================

menu = st.radio(
    "메뉴",
    ["요약", "히스토리"],
    horizontal=True
)


# =========================
# 요약 화면
# =========================

if menu == "요약":

    url = st.text_input(
        "기사 URL",
        placeholder="https://..."
    )

    model = st.selectbox(
        "모델 선택",
        [
            "facebook/bart-large-cnn",
            "google-t5/t5-small"
        ]
    )

    max_length = st.slider(
        "최대 길이",
        50,
        300,
        150
    )

    min_length = st.slider(
        "최소 길이",
        20,
        100,
        40
    )

    if st.button("요약하기"):

        if not url:
            st.warning("URL을 입력하세요.")

        else:
            with st.spinner("요약 중입니다..."):

                try:
                    response = requests.post(
                        API_URL,
                        json={
                            "url": url,
                            "model": model,
                            "max_length": max_length,
                            "min_length": min_length
                        },
                        timeout=300
                    )

                    if response.status_code == 200:

                        result = response.json()

                        # MySQL에 요약 결과 저장
                        save_summary(
                            url,
                            result["model"],
                            result["summary"]
                        )

                        st.success("요약 완료 및 DB 저장 완료")

                        st.markdown("### 선택한 모델")
                        st.write(result["model"])

                        st.markdown("### 요약 결과")
                        st.write(result["summary"])

                    else:
                        st.error(response.text)

                except requests.exceptions.RequestException as e:
                    st.error(f"백엔드 연결 오류: {e}")

                except pymysql.MySQLError as e:
                    st.error(f"DB 저장 오류: {e}")


# =========================
# 히스토리 화면
# =========================

elif menu == "히스토리":

    st.subheader("요약 히스토리")

    keyword = st.text_input(
        "검색",
        placeholder="URL, 모델명, 요약 내용 검색"
    )

    try:
        history = get_history(keyword)

        st.write(f"검색 결과: {len(history)}건")

        if not history:
            st.info("저장된 요약 결과가 없습니다.")

        else:
            for row in history:

                history_id = row[0]
                history_url = row[1]
                history_model = row[2]
                history_summary = row[3]
                created_at = row[4]

                with st.expander(
                    f"#{history_id} | {history_model} | {created_at}"
                ):
                    st.markdown("**URL**")
                    st.write(history_url)

                    st.markdown("**모델**")
                    st.write(history_model)

                    st.markdown("**요약 결과**")
                    st.write(history_summary)

    except pymysql.MySQLError as e:
        st.error(f"DB 조회 오류: {e}")
