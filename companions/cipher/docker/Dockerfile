# Cipher Runtime — Multi-stage Docker build
FROM node:22-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

# Copy source
COPY tsconfig.json ./
COPY *.ts ./
COPY tools/ ./tools/
COPY memory/ ./memory/
COPY escalation/ ./escalation/

# Build TypeScript
RUN npx tsc

# ── Production image ────────────────────────────────────────────────────
FROM node:22-slim

WORKDIR /app

# Install Playwright system deps
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy built app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

# Copy soul contracts (for system prompt)
COPY ../soul/ ./soul/

# Install Playwright Chromium
RUN npx playwright install chromium

ENV NODE_ENV=production
EXPOSE 3333 3002

CMD ["node", "dist/server.js"]
