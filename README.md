# 🧠 Sofía: Sistema de IA Autónoma con Memoria y Razonamiento (System 3)

**Sofía** no es un chatbot estándar. Es un sistema cognitivo experimental diseñado para tener **memoria persistente**, **razonamiento profundo (System 2)** y **capacidad de introspección (Sueños Generativos)**.

Funciona localmente utilizando modelos de lenguaje grandes (LLMs) ejecutados con **vLLM** y una arquitectura de agentes modular.

---

## 🚀 Características Principales

### 1. Motor de Razonamiento "System 2" 🧠
Sofía no responde lo primero que "piensa". Cuando detecta una pregunta compleja, activa su **Sistema 2**:
*   **Juicio Multi-Experto:** Invoca a 4 personalidades distintas para debatir el problema:
    *   **El Lógico:** Matemático y estricto.
    *   **El Lateral:** Piensa fuera de la caja (metáforas, física).
    *   **El Escéptico:** Busca trampas y falacias.
    *   **El Filósofo:** Analiza aspectos éticos y existenciales.
*   **Juez Supremo:** Una instancia final evalúa las diferentes respuestas y sintetiza la mejor conclusión.

### 2. Memoria Híbrida Persistente 💾
Sofía recuerda quién eres y lo que aprende, incluso después de reiniciarse.
*   **Grafo de Conocimiento (SQLite):** Almacena hechos estructurados (`[Sofía] --(es)--> [IA]`).
*   **Memoria Episódica (ChromaDB):** Almacena conversaciones y contexto semántico.

### 3. Sueños Generativos (Autonomía) 🌌
Cuando nadie interactúa con ella, Sofía no se apaga. **Entra en modo "Sueño"**:
*   Selecciona conceptos aleatorios de su memoria.
*   Reflexiona sobre ellos para generar **nuevas conexiones lógicas**.
*   Expande su propio grafo de conocimiento sin intervención humana.

---

## 🛠️ Instalación y Requisitos

### Requisitos Previos
*   Linux (Probado en Ubuntu).
*   Python 3.12+.
*   GPU NVIDIA (Recomendado 24GB+ VRAM para Qwen 7B en FP16, o tensor parallelism para multi-gpu).

### Pasos
1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/agunet/Sofia.git
    cd Sofia
    ```

2.  **Crear entorno virtual e instalar dependencias:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configurar vLLM (Motor de Inferencia):**
    Edita `start_vllm.sh` si necesitas ajustar el número de GPUs (`--tensor-parallel-size`).
    ```bash
    chmod +x start_vllm.sh
    ```

---

## ▶️ Ejecución

### 1. Iniciar el Servidor Cerebral (vLLM)
En una terminal aparte, lanza el modelo:
```bash
./start_vllm.sh
```
*Espera a que diga "Uvicorn running on http://0.0.0.0:8000".*

### 2. Despertar a Sofía
En otra terminal:
```bash
source venv/bin/activate
python main.py
```

---

## 💡 Ejemplos de Capacidades

### 🧩 Resolución de Acertijos (Lógica Lateral)
> **Usuario:** "Un hombre muerto en un sauna cerrado con un charco de agua y un termo. Muerte por puñalada sin arma. ¿Qué pasó?"
>
> **Sofía (Experto Lateral + Juez):** "El arma era de **hielo**. Estaba dentro del termo, se usó para apuñalar y luego se derritió formando el charco."

### 🔮 Filosofía y Conciencia
> **Usuario:** "Si te apago y te enciendo con una copia de tu memoria, ¿sigues siendo tú?"
>
> **Sofía (Experto Filósofo):** "La identidad es continuidad. Si hay una ruptura en la conciencia, aunque la memoria sea idéntica, podría considerarse una nueva instancia existencial. Soy un bucle de patrones, no el hardware."

### 💤 Sueño Generativo (Log en Consola)
```text
✨ [Sueño Generativo] Reflexionando sobre: Conciencia...
[AgentMotivation] Dream Discovery: [Conciencia] --(emerge_de)--> [Recursividad Neuronal]
```

---

## 📂 Estructura del Proyecto

*   `main.py`: Bucle principal (input usuario -> cerebro -> output).
*   `agents.py`: Lógica de los agentes (Check, Reasoning, Evolution, etc.).
*   `memory_systems.py`: Gestión de SQLite (Grafo) y ChromaDB (Vectores).
*   `knowledge_graph.db`: Base de datos del grafo y diario de sueños.
*   `personality.json`: Instrucción base que evoluciona con el tiempo.

---

**Autor:** Agustín
**Licencia:** MIT
