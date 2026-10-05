FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && \
    groupadd --system complied && useradd --system --gid complied --home /app complied && \
    mkdir -p /data && chown complied:complied /data
COPY src /app/src
COPY scripts /app/scripts
USER complied
EXPOSE 8080
CMD ["python","-m","complied.web","--host","0.0.0.0","--db","/data/complied.sqlite3"]
