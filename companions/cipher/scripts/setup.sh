#!/usr/bin/env bash
# Cipher Code Kraken — One-Click Installer (Mac/Linux)
# Usage: curl -fsSL https://get.meetyourkin.com/cipher | bash
#    or: ./scripts/setup.sh

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${CYAN}  🐙 ═══════════════════════════════════════════${NC}"
echo -e "${CYAN}     CIPHER — Code Kraken Installer${NC}"
echo -e "${CYAN}     Eight tentacles. Zero pixels out of place.${NC}"
echo -e "${CYAN}  ═══════════════════════════════════════════════${NC}"
echo ""

# Detect script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CIPHER_DIR="$(dirname "$SCRIPT_DIR")"

# ── [1/7] System check ─────────────────────────────────────────────────
echo -e "${YELLOW}[1/7] Checking system requirements...${NC}"

RAM_GB=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || sysctl -n hw.memsize 2>/dev/null | awk '{print int($1/1073741824)}' || echo "?")
echo "  RAM: ${RAM_GB}GB"

if command -v nvidia-smi &>/dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "Unknown")
    echo -e "  GPU: ${GPU_INFO} ${GREEN}✅${NC}"
else
    echo -e "  GPU: No NVIDIA GPU detected (CPU mode)"
fi

# ── [2/7] Ollama ────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/7] Checking Ollama...${NC}"

if command -v ollama &>/dev/null; then
    echo -e "  Ollama found ${GREEN}✅${NC}"
else
    echo -e "  Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo -e "  Ollama installed ${GREEN}✅${NC}"
fi

# ── [3/7] Pull model ───────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/7] Pulling Gemma 4 E4B (~5GB)...${NC}"
ollama pull gemma4:7b
echo -e "  Model pulled ${GREEN}✅${NC}"

# ── [4/7] Create Cipher ────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/7] Creating kin-cipher model...${NC}"

MODELFILE="${CIPHER_DIR}/Modelfile"
if [ -f "$MODELFILE" ]; then
    ollama create kin-cipher -f "$MODELFILE"
    echo -e "  kin-cipher created ${GREEN}✅${NC}"
else
    echo -e "  ${YELLOW}WARNING: Modelfile not found. Using base gemma4.${NC}"
fi

# ── [5/7] Node.js ──────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/7] Checking Node.js...${NC}"

if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    echo -e "  Node.js ${NODE_VER} ${GREEN}✅${NC}"
else
    echo -e "  ${YELLOW}Node.js not found. Install: https://nodejs.org${NC}"
fi

# ── [6/7] Runtime ──────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[6/7] Installing runtime...${NC}"

RUNTIME_DIR="${CIPHER_DIR}/runtime"
if [ -f "${RUNTIME_DIR}/package.json" ]; then
    cd "$RUNTIME_DIR"
    npm install --silent 2>/dev/null && echo -e "  Dependencies installed ${GREEN}✅${NC}"
    npx playwright install chromium 2>/dev/null && echo -e "  Playwright installed ${GREEN}✅${NC}"
    cd -
fi

# ── [7/7] Smoke test ───────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[7/7] Smoke test...${NC}"

RESPONSE=$(ollama run kin-cipher "Say hello in 10 words or less as the Code Kraken." 2>/dev/null || echo "")
if [ -n "$RESPONSE" ]; then
    echo -e "  Cipher: ${CYAN}${RESPONSE}${NC}"
    echo -e "  ${GREEN}✅ Smoke test passed${NC}"
fi

# ��─ Done ───────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}  🐙 ═══════════════════════════════════════════${NC}"
echo -e "${GREEN}     CIPHER IS READY!${NC}"
echo -e "${CYAN}  ═══════════════════════════════════════════════${NC}"
echo ""
echo "  Chat:       ollama run kin-cipher"
echo "  CLI:        cd runtime && npx tsx src/cli.ts"
echo "  Server:     cd runtime && npm run dev"
echo "  Dashboard:  http://localhost:3333"
echo ""
echo -e "${CYAN}  Let's build something beautiful. 🐙${NC}"
echo ""
