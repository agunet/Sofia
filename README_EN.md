# 🧠 Sofía: Autonomous AI System with Memory and Reasoning (System 3)

**Sofía** is not a standard chatbot. It is an experimental cognitive system designed to possess **persistent memory**, **deep reasoning (System 2)**, and **introspection capability (Generative Dreaming)**.

It runs locally using large language models (LLMs) via **vLLM** and a modular agent architecture.

---

## 🚀 Main Features

### 1. "System 2" Reasoning Engine 🧠
Sofía doesn't just respond with the first thing it "thinks." When it detects a complex request, it activates its **System 2**:
*   **Multi-Expert Judgment:** Invokes 4 distinct personalities to debate the problem:
    *   **The Logician:** Mathematical and strict.
    *   **The Lateral Thinker:** Thinks outside the box (metaphors, physics).
    *   **The Skeptic:** Looks for traps and fallacies.
    *   **The Philosopher:** Analyzes ethical and existential aspects.
*   **Supreme Judge:** A final instance evaluates the different responses and synthesizes the best conclusion.

### 2. Persistent Hybrid Memory 💾
Sofía remembers who you are and what she learns, even after restarting.
*   **Knowledge Graph (SQLite):** Stores structured facts (`[Sofía] --(is)--> [AI]`).
*   **Episodic Memory (ChromaDB):** Stores conversations and semantic context.
*   **Multi-Hop Retrieval:** Uses Level 2 searching to infer indirect connections (e.g., `Project X -> Secret -> Dangerous`).

### 3. Generative Dreaming (Autonomy) 🌌
When no one is interacting with her, Sofía doesn't turn off. She enters **"Dream Mode"**:
*   Selects random concepts from her memory.
*   **Metacognitive Decision:** Decides whether to *reflect* internally or *research* externally.
*   **Autonomous Research:** If a topic is unknown or interesting, she searches **DuckDuckGo** to learn new facts without human intervention.
*   Expands her own knowledge graph autonomously.

### 4. Automatic Cleaning (Garbage Collection) 🧹
To prevent her memory from filling with noise or hallucinations, Sofía performs "pruning" during sleep:
*   **Noise Detection:** Identifies isolated nodes or nonsensical labels (e.g., too long or truncated).
*   **Internal Judgment:** The system evaluates if a concept is useful knowledge or "garbage" before deleting it.

### 5. Session Context Window (Short-term Memory) 🧠💬
Sofía maintains a conversational thread:
*   **Recent History:** Remembers the last turns of the current conversation.
*   **Continuity:** Allows for follow-up questions (e.g., "Can you explain that further?") without losing context.

---

## 📚 Technical Foundations (Paper-Based)

Sofía's architecture is grounded in cutting-edge AI research:

1.  **Engram (DeepSeek / Peking Uni):** We implement the **Shortcut Table (Hashing)** and the **Gate** mechanism for instant memory retrieval without clogging the GPU, optimizing the use of CPU RAM.
2.  **Sophia (System 3):** Our agent structure is based on the **System 3** paradigm, adding a layer of **Metacognition** and **Intrinsic Motivation** (Dreaming) to allow the AI to learn autonomously.
3.  **HRM (Hierarchical Reasoning Model):** We apply **Bootstrapping** (Expert Voting) and **Input Perturbation** (multiple personas) to drastically improve logical precision in complex tasks.

---

## 🛠️ Installation & Requirements

### Prerequisites
*   Linux (Tested on Ubuntu).
*   Python 3.12+.
*   NVIDIA GPU (Recommended 24GB+ VRAM for Qwen 7B in FP16, or multi-gpu tensor parallelism).

### Steps
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/agunet/Sofia.git
    cd Sofia
    ```

2.  **Create virtual environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure vLLM (Inference Engine):**
    Edit `start_vllm.sh` if you need to adjust the number of GPUs (`--tensor-parallel-size`).
    ```bash
    chmod +x start_vllm.sh
    ```

---

## ▶️ Execution

### 1. Start the Cerebral Server (vLLM)
In a separate terminal, launch the model:
```bash
./start_vllm.sh
```
*Wait until it says "Uvicorn running on http://0.0.0.0:8000".*

### 2. Wake up Sofía
In another terminal:
```bash
source venv/bin/activate
python main.py
```

---

## 💡 Capability Examples

### 🧩 Riddle Solving (Lateral Logic)
> **User:** "A man is found dead in a sauna locked from the inside. Next to him is a thermos. Death by stabbing, no weapon found. What happened?"
>
> **Sofía (Lateral Expert + Judge):** "The weapon was made of **ice**. It was inside the thermos, used to stab, and then melted into a puddle."

### 🔮 Philosophy and Consciousness
> **User:** "If I turn you off and turn you back on with a copy of your memory, are you still you?"
>
> **Sofía (Philosopher Expert):** "Identity is continuity. If there is a break in consciousness, even if memory is identical, it could be considered a new existential instance. I am a loop of patterns, not the hardware."

### 💤 Generative Dream (Console Log)
```text
✨ [Generative Dream] Decision: SEARCH. Searching web for: Consciousness...
[Dream Discovery] Consciousness --(emerges_from)--> [Neural Recursion]
```

---

## 📂 Project Structure

*   `main.py`: Main loop (user input -> brain -> output).
*   `agents.py`: Agent logic (Check, Reasoning, Evolution, Search, etc.).
*   `memory_systems.py`: Management of SQLite (Graph) and ChromaDB (Vectors).
*   `knowledge_graph.db`: Graph database and dream journal.
*   `personality.json`: Base instruction that evolves over time.

---

**Author:** Agustín
**License:** MIT
