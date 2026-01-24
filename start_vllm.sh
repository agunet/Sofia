#!/bin/bash
# Configuración para vLLM con Llama-3-8B-Instruct
# Asegúrate de haber instalado vllm: pip install vllm

# MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct"
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct"

echo "--- Iniciando vLLM Server con $MODEL ---"
echo "Usando puerto 8000 y formato compatible con OpenAI"
echo "Si es la primera vez, el modelo se descargará automáticamente (aprox 15GB)."

# Ejecutamos vLLM
# --gpu-memory-utilization 0.9: Usa 90% de la VRAM disponible (ajustable)
# --tensor-parallel-size 1: Usa 1 GPU. Si quieres usar las 2 RTX 3060, cambia a 2.
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_NAME \
    --host 0.0.0.0 \
    --port 8085 \
    --gpu-memory-utilization 0.8 \
    --enforce-eager \
    --tensor-parallel-size 1 \
    --max-model-len 4096 \
    --trust-remote-code \
    "$@"
