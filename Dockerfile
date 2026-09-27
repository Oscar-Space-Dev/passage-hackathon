FROM node:22-bookworm-slim AS codex
RUN npm install -g @openai/codex

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PASSAGE_DB=/tmp/passage.db
COPY --from=codex /usr/local/bin/node /usr/local/bin/node
COPY --from=codex /usr/local/bin/codex /usr/local/bin/codex
COPY --from=codex /usr/local/lib/node_modules /usr/local/lib/node_modules
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY passage ./passage
COPY data/corpus_theses.json data/programmes_demo.json ./data/
COPY methods ./methods
EXPOSE 10000
CMD ["sh", "-c", "uvicorn passage.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]
