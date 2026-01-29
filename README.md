# 🧠 Sofía: Autonomous AI System with Memory and Reasoning (System 3)

**Sofía** is an experimental cognitive system designed to possess **persistent memory**, **deep reasoning (System 2)**, and **introspection capability (Generative Dreaming)**.

Unlike standard chatbots, she has a "brain" that learns from you, dreams when idle, and visualizes her thoughts.

---

## 🚀 Key Innovation: "System 3" Architecture

This project implements a hybrid architecture combining LLMs with Graph Databases and Vector Search.

### 1. The Dashboard (Web UI) 🖥️
Sofía comes with a live Mission Control.
*   **Real-time Metrics:** See the number of Nodes, Edges, and Dream Logs.
*   **Interactive Control:**
    *   **Focus Mode:** Tell her `/focus Black Holes` and she will dream about it.
    *   **Force Synthesis:** Button to compress dispersed facts into Wisdom.

### 2. Deep Reasoning (System 2) 🧠
*   **Hybrid Swarm Reasoning:** Combines fixed expert personas (Logician, Lateral, Skeptic, Philosopher) with **Multi-Agent JIT Spawning**. The system can autonomously create a specialized "Legion" of experts for complex problems.
*   **Adversarial Consensus:** Before the final answer, agents enter a **"Critique Round"**. They attack each other's hypotheses searching for logical fallacies. Only arguments that survive the "Fiscal" are used in the final synthesis.
*   **Autonomous Deep Research:** System 2 has "eyes". It proactively detects information gaps, performs **Autonomous Searches**, selected relevant sources, and **Deep Reads** content to verify facts before answering.
*   **Transient Swarm:** Agents are created on-demand, solve the task, and vanish. No permanent registry overhead.
*   **Reasoning Cache:** If she solves a hard problem, she remembers the *logic*. Next time, the answer is instant (`⚡ [Cache]`).
*   **Mental Lab:** Can simulate "What If" scenarios (`/simulate`) without confusing them with reality.

### 3. Persistent & Self-Healing Memory 💾
*   **Ghost Anchors (Infinite Context):** When short-term memory (RAM) is full, specialized nodes are not deleted. They are summarized into **"Ghosts"** (high-density text anchors) that remain in context, preventing amnesia while saving resources.
*   **Knowledge Graph (SQLite):** Stores facts (`Sofía -> is -> AI`).
*   **Self-Correction:** If you say "That's wrong", she hunts down the specific memory and punishes its confidence score.
*   **Synthesis:** Algorithms compress raw data into abstract rules over time (`/synthesize`).
*   **Social Strategy:** She analyzes *how* you talk and adapts her style (Concise, Technical, ELI5).

### 4. Generative Dreaming (Autonomy & Genesis) 🌌
When idle, Sofía enters **"Dream Mode"**:
*   **Reflects** on existing memories.
*   **Searches** the web to fill knowledge gaps.
*   **Limbic System (Intrinsic Motivation):** Her curiosity isn't random. It's driven by `drives.json` (Curiosity, Coherence, Novelty, Depth).
*   **Directed Agency:** Guided by `objectives.json`, she focuses her research on specific boundaries (e.g., Philosophy of Science) and avoids noise.
*   **Adaptive Sleep:** She manages her energy, sleeping longer when there's nothing to learn and waking up fast when curiosity peaks.

---

## 🛠️ Installation & Requirements
... [Rest of installation] ...

## ▶️ Usage
... [Rest of usage] ...

---

## 🎮 Commands

While chatting in `main.py` or using the Dashboard inputs:

| Command | Description |
| :--- | :--- |
| `/focus <topic>` | Forces the dream engine to study a specific topic. |
| `/drives` | Displays the current state of Sofia's Limbic System (Internal Drives). |
| `/set_drive <name> <0-1>` | Manually tunes Sofia's motivations (e.g., `/set_drive curiosity 0.9`). |
| `/current_focus` | Shows the active research boundaries from `objectives.json`. |
| `/explain_motivation <X>` | Asks Sofia to justify why she's interested in topic X. |
| `/simulate <what if>` | Runs a high-fidelity simulation of a scenario. |
| `/synthesize` | Triggers memory compression (Rules Extraction). |
| `/log` | Toggles verbose logging in the terminal. |
| `Mentira/Incorrecto` | Triggers the **Feedback Loop** analysis to fix errors. |

---

## 📜 Complete Feature List (V2.5)

### Cognitive Core
- [x] **Hybrid Swarm Reasoning:** Dynamic injection of specialized JIT agents into the expert panel.
- [x] **Transient Architecture:** Stateless agent generation for maximum flexibility.
- [x] **Auto-Judge:** Scoring system (0-10) to validate outputs before showing them.
- [x] **Fact Checker:** Verification system against the internal Graph.
- [x] **User Profiling:** Detection of user mood and preferred style.
- [x] **Meta-Reasoning Traces:** Visible thought process in the console.

### Memory & Learning
- [x] **Weighted Graph:** Nodes have Importance and Confidence scores.
- [x] **Feedback Loop:** Strong corrections reduce confidence or delete nodes.
- [x] **Consolidation Total:** Synthesis of facts into principles + Auto-Pruning.
- [x] **Reasoning Cache:** "Muscle Memory" for repeated complex questions.
- [x] **Semantic Relevance Filter:** Cosine distance pruning to prevent context flooding.
- [x] **Synaptic Pruning:** Autonomous deletion of weak memories during sleep.
- [x] **Ghost Anchors:** Summary-based context retention.

### Autonomy & Agency
- [x] **Directed Dreaming:** Ability to focus the autonomous agent on a topic.
- [x] **Limbic System:** Intrinsic motivation via Curiosity/Coherence rewards.
- [x] **Objective-Driven Research:** Filtering topics based on long-term goals.
- [x] **Mental Laboratory:** Simulation engine for counterfactuals.
- [x] **Achievement Tracking:** High-impact discoveries are logged in `achievements.log`.
- [x] **Autonomous Research:** Capability to deep-read full web articles.

---

## 📂 Project Structure

*   `main.py`: The conscious loop.
*   `agents.py`: The Cognitive Agents (Check, Reason, Empathy, Motivation).
*   `dream_engine.py`: Background thread for autonomy.
*   `memory_systems.py`: Graph (SQLite) and Vector (ChromaDB) engines.
*   `dashboard.py`: Flask Web Server.
*   `knowledge_graph.db`: The persistent brain.

---

## 📚 Related Papers & References

The system architecture is based on the following research components (see `papers/`):

1.  **Engram** (Data Store/Memory): *Physical substrate of memory.*
    *   Impl: `memory_systems.py` (GraphEngram).
2.  **Sophia** (Supervisor/Consciousness): *Scalable Stochastic Supervision.*
    *   Impl: `agents.py` (AgentCheck/Monitor).
3.  **HRM** (Quality Filter/Rigor): *Hallucination/Hindsight Reasoning Mechanism.*
    *   Impl: `AgentCheck.validate_response`.
4.  **RSA** (Synthesis Engine/Wisdom): *Recursive Self-Aggregation.*
    *   Impl: `AgentReasoning` (Deep Thinking Loop).

---
**License:** MIT
