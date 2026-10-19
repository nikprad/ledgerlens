FROM python:3.11-slim-bookworm

# Install Node.js LTS and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    build-essential \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifests
COPY requirements.txt package*.json tsconfig.json ./

# Install Python and Node dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN npm install

# Copy application source code
COPY . .

# Ensure start script is executable
RUN chmod +x scripts/start.sh

# Configurable environment variables for Ollama & backend host
ENV BACKEND_HOST="0.0.0.0"
ENV BACKEND_PORT=8000
ENV FRONTEND_PORT=3000
ENV BACKEND_URL="http://127.0.0.1:8000"
ENV OLLAMA_BASE_URL="http://localhost:11434"
ENV GEMMA_VISION_MODEL="gemma3:4b"
ENV OLLAMA_MOCK_FALLBACK="true"
ENV TABPFN_MODE="LOCAL"
ENV ENABLE_TABPFN_API="false"

EXPOSE 3000 8000

CMD ["./scripts/start.sh"]
