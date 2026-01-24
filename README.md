# 🧠 Sofía: Autonomous AI System with Memory and Reasoning (System 3)

**Sofía** is an experimental cognitive system designed to possess **persistent memory**, **deep reasoning (System 2)**, and **introspection capability (Generative Dreaming)**.

Unlike standard chatbots, she has a "brain" that learns from you, dreams when idle, and visualizes her thoughts.

---

## 🚀 Key Innovation: "System 3" Architecture

### 1. The Dashboard (Web UI) 🖥️
Sofía comes with a live Mission Control.
*   **Real-time Metrics:** See the number of Nodes, Edges, and Dream Logs.
*   **Interactive Control:**
    *   **Focus Mode:** Tell her `/focus Black Holes` and she will dream about it.
    *   **Force Synthesis:** Button to compress dispersed facts into Wisdom.

### 2. Deep Reasoning (System 2) 🧠
*   **Meta-Cognitive Voting:** 4 Experts (Logician, Lateral, Skeptic, Philosopher) debate every complex answer.
*   **Transparency:** You see the thinking process live (`↳ [Expert: Lateral] Hypothesis generated...`).
*   **Reasoning Cache:** If she solves a hard problem, she remembers the *logic*. Next time, the answer is instant (`⚡ [Cache]`).
*   **Mental Lab:** Can simulate "What If" scenarios (`/simulate`) without confusing them with reality.

### 3. Persistent & Self-Healing Memory 💾
*   **Knowledge Graph (SQLite):** Stores facts (`Sofía -> is -> AI`).
*   **Self-Correction:** If you say "That's wrong", she hunts down the specific memory and punishes its confidence score.
*   **Synthesis:** Algorithms compress raw data into abstract rules over time.
*   **Social Strategy:** She analyzes *how* you talk and adapts her style (Concise, Technical, ELI5).

### 4. Generative Dreaming (Autonomy) 🌌
When idle, Sofía enters **"Dream Mode"**:
*   **Reflects** on existing memories.
*   **Searches** the web to fill knowledge gaps.
*   **Directed Dreaming:** You can steer her curiosity using `/focus <topic>`.

---

## 🛠️ Installation & Requirements

### Prerequisites
*   Linux (Ubuntu recommended).
*   Python 3.12+.
*   NVIDIA GPU (24GB+ VRAM recommended for Qwen 7B).

### Steps
1.  **Clone:**
    ```bash
    git clone https://github.com/agunet/Sofia.git
    cd Sofia
    ```

2.  **Install:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Launch vLLM (The Brain):**
    ```bash
    ./start_vllm.sh
    ```

---

## ▶️ Usage

### 1. Start the Voice (Terminal Interface)
```bash
python main.py
```
This is the main interaction loop. You can talk to her here.

### 2. Start the Dashboard (Web Interface)
In a separate terminal:
```bash
source venv/bin/activate
python dashboard.py
```
Open **http://localhost:5000** in your browser.

---

## 🎮 Commands

While chatting in `main.py` or using the Dashboard inputs:

| Command | Description |
| :--- | :--- |
| `/focus <topic>` | Forces the dream engine to study a specific topic. |
| `/simulate <what if>` | Runs a high-fidelity simulation of a scenario. |
| `/synthesize` | Triggers memory compression (Rules Extraction). |
| `/log` | Toggles verbose logging in the terminal. |
| `Mentira/Incorrecto` | Triggers the **Feedback Loop** analysis to fix errors. |

---

## 📂 Project Structure

*   `main.py`: The conscious loop.
*   `agents.py`: The Cognitive Agents (Check, Reason, Empathy, Motivation).
*   `dream_engine.py`: Background thread for autonomy.
*   `memory_systems.py`: Graph (SQLite) and Vector (ChromaDB) engines.
*   `dashboard.py`: Flask Web Server.
*   `knowledge_graph.db`: The persistent brain.

---
**License:** MIT
