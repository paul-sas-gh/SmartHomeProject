#!/bin/bash
set -e

MODEL="${OLLAMA_MODEL:-gemma4:4b}"

echo "============================================"
echo " Ollama LLM Server"
echo " Model: ${MODEL}"
echo "============================================"

# Porneste serverul Ollama in background
ollama serve &
OLLAMA_PID=$!

# Asteapta ca serverul sa fie disponibil (folosim ollama list, fara curl)
echo "[startup] Astept Ollama sa fie gata..."
MAX_WAIT=60
WAITED=0
until ollama list > /dev/null 2>&1; do
    sleep 2
    WAITED=$((WAITED + 2))
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "[ERROR] Ollama nu a pornit in ${MAX_WAIT}s. Iesire."
        exit 1
    fi
done
echo "[startup] Ollama este disponibil."

# Verifica daca modelul exista deja local
if ollama list | grep -q "^${MODEL}"; then
    echo "[startup] Modelul '${MODEL}' exista deja local. Sar peste download."
else
    echo "[startup] Descarc modelul '${MODEL}'... (poate dura cateva minute)"
    ollama pull "${MODEL}"
    echo "[startup] Model descarcat cu succes."
fi

echo "[startup] Gata. Ollama ruleaza cu modelul '${MODEL}'."

# Asteapta procesul principal
wait $OLLAMA_PID
