FROM backend-base

WORKDIR /app

COPY backend.py .

RUN python -m pip install --no-cache-dir \
    fastapi \
    uvicorn \
    requests \
    beautifulsoup4 \
    sentencepiece

EXPOSE 8000

CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
