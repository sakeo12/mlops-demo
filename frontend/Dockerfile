FROM python:3.11-slim

WORKDIR /app

COPY frontend.py .

RUN pip install --no-cache-dir \
    streamlit \
    requests \
    pymysql

ENV API_URL=http://server:8000/summarize

EXPOSE 8501

CMD ["streamlit", "run", "frontend.py", "--server.address=0.0.0.0", "--server.port=8501"]
