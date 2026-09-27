FROM node:22-bookworm-slim AS codex
RUN npm install -g @openai/codex@0.157.1

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PASSAGE_DB=/tmp/passage.db HOME=/tmp
COPY --from=codex /usr/local/bin/node /usr/local/bin/node
COPY --from=codex /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/@openai/codex/bin/codex.js /usr/local/bin/codex \
    && codex --version
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY passage ./passage
COPY data/corpus_theses.json data/programmes_demo.json ./data/
COPY methods ./methods
EXPOSE 10000
USER 10001
RUN TURSO_DATABASE_URL= PASSAGE_DB=/tmp/build-check/passage.db python -c "from passage.codex_brain import CodexClient; client = CodexClient('build-check'); client.close()"
CMD ["sh", "-c", "uvicorn passage.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]
