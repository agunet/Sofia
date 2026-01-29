#!/bin/bash

# Configuración para vLLM con Llama-3-8B-Instruct
# Asegúrate de haber instalado vllm: pip install vllm

# MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct"
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct"
# MODEL_NAME="casperhansen/deepseek-r1-distill-qwen-32b-awq"

echo "--- Iniciando vLLM Server con $MODEL ---"
echo "Usando puerto 8000 y formato compatible con OpenAI"
echo "Si es la primera vez, el modelo se descargará automáticamente (aprox 15GB)."

# Ejecutamos vLLM
# --gpu-memory-utilization 0.8: Usa 80% de la VRAM disponible para evitar OOM
# --tensor-parallel-size 2: Usa 2 GPUs.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_NAME \
    --host 0.0.0.0 \
    --port 8085 \
    --gpu-memory-utilization 0.8 \
    --tensor-parallel-size 2 \
    --max-model-len 24000 \
    --trust-remote-code \
    "$@"
