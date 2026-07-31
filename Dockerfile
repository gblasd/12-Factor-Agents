FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY FoundationsOfAgenticTool ./FoundationsOfAgenticTool
COPY README.md ./README.md

ENV OPENAI_API_KEY=""

CMD ["python", "FoundationsOfAgenticTool/main.py"]
