FROM python:3.11-slim

WORKDIR /app

# Install dependencies in a cached layer before copying source
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./

# Copy the root alembic.ini and patch script_location for the container layout.
# Locally the ini lives at the project root with script_location = backend/alembic;
# inside the container the alembic/ directory is directly under WORKDIR /app.
COPY alembic.ini ./alembic.ini
RUN sed -i 's|script_location = backend/alembic|script_location = alembic|' alembic.ini \
    && chmod +x ./entrypoint.sh

# Drop to a non-root user for runtime security
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# entrypoint runs `alembic upgrade head` then starts uvicorn
ENTRYPOINT ["./entrypoint.sh"]
