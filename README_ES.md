# 🧠 Sofía: Sistema de IA Autónoma con Memoria y Razonamiento (Sistema 3)

**Sofía** es un sistema cognitivo experimental diseñado para tener **memoria persistente**, **razonamiento profundo (Sistema 2)** y **capacidad de introspección (Sueño Generativo)**.

A diferencia de los chatbots estándar, Sofía tiene un "cerebro" que crece, aprende de ti, sueña cuando no la usas y visualiza sus pensamientos.

---

## 🚀 Innovaciones Clave: Arquitectura "Sistema 3"

### 1. Panel de Control (Dashboard Web) 🖥️
Sofía incluye un Centro de Mando en tiempo real.
*   **Métricas Vivas:** Visualiza Nodos, Conexiones y Actividad de Sueño.
*   **Control Interactivo:**
    *   **Modo Foco:** Ordénale `/focus Agujeros Negros` y dedicará sus sueños a investigarlo.
    *   **Síntesis Forzada:** Botón para comprimir hechos dispersos en sabiduría.

### 2. Razonamiento Profundo (Sistema 2) 🧠
*   **Votación Meta-Cognitiva:** 4 Expertos (Lógico, Lateral, Escéptico, Filósofo) debaten las respuestas complejas.
*   **Transparencia:** Puedes ver el pensamiento en vivo (`↳ [Experto: Lateral] Hipótesis generada...`).
*   **Caché de Razonamiento:** Si resuelve un problema difícil, recuerda la *lógica*. La próxima vez responde al instante (`⚡ [Cache]`).
*   **Laboratorio Mental:** Simula escenarios hipotéticos (`/simulate`) sin confundirlos con la realidad.

### 3. Memoria Persistente y Auto-Reparable 💾
*   **Grafo de Conocimiento (SQLite):** Guarda hechos (`Sofía -> es -> IA`).
*   **Auto-Corrección:** Si le dices "Eso es mentira", busca el recuerdo específico y castiga su nivel de confianza.
*   **Síntesis:** Algoritmos que extraen reglas abstractas de datos repetitivos.
*   **Estrategia Social:** Analiza *cómo* hablas y adapta su estilo (Conciso, Técnico, ELI5).

### 4. Sueño Generativo (Autonomía) 🌌
Cuando está inactiva, Sofía entra en **"Modo Sueño"**:
*   **Reflexiona** sobre memorias existentes.
*   **Investiga** en la web para llenar vacíos de conocimiento.
*   **Sueño Dirigido:** Tú controlas su curiosidad con `/focus`.

---

## 🛠️ Instalación y Requisitos

### Prerrequisitos
*   Linux (Recomendado Ubuntu).
*   Python 3.12+.
*   GPU NVIDIA (24GB+ VRAM para Qwen 7B, o equivalente).

### Pasos
1.  **Clonar:**
    ```bash
    git clone https://github.com/agunet/Sofia.git
    cd Sofia
    ```

2.  **Instalar:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Lanzar vLLM (El Cerebro):**
    ```bash
    ./start_vllm.sh
    ```

---

## ▶️ Uso

### 1. Iniciar la Voz (Terminal)
```bash
python main.py
```
Este es el bucle principal de consciencia. Habla con ella aquí.

### 2. Iniciar el Dashboard (Web)
En otra terminal:
```bash
source venv/bin/activate
python dashboard.py
```
Abre **http://localhost:5000** en tu navegador.

---

## 🎮 Comandos

Mientras chateas en `main.py` o usas el Dashboard:

| Comando | Descripción |
| :--- | :--- |
| `/focus <tema>` | Fuerza al motor de sueño a estudiar un tema específico. |
| `/simulate <qué pasaría si>` | Ejecuta una simulación de alta fidelidad. |
| `/synthesize` | Dispara la compresión de memoria (Extracción de Reglas). |
| `/log` | Activa/Desactiva logs detallados en la terminal. |
| `Mentira/Incorrecto` | Dispara el **Feedback Loop** para corregir errores. |

---

## 📜 Lista Completa de Features (V2.0)

### Núcleo Cognitivo
- [x] **Auto-Juez:** Sistema de puntuación (0-10) para validar respuestas.
- [x] **Verificador de Hechos:** Cotejo contra el Grafo interno.
- [x] **Perfilado de Usuario:** Detección de humor y estilo preferido.
- [x] **Trazas de Meta-Razonamiento:** Visualización del hilo de pensamiento.

### Memoria y Aprendizaje
- [x] **Grafo Ponderado:** Nodos con scores de importancia y confianza.
- [x] **Feedback Loop:** Castigo y eliminación de nodos ante correcciones.
- [x] **Compresión de Memoria:** Síntesis de hechos en principios.
- [x] **Caché de Razonamiento:** "Memoria Muscular" para problemas complejos.

### Autonomía
- [x] **Sueño Dirigido:** Capacidad de enfocar al agente autónomo.
- [x] **Laboratorio Mental:** Motor de simulación para contrafactuales.
- [x] **Protocolo Génesis:** Sembrado automático si el cerebro está vacío.
- [x] **Análisis de Estrategia:** Aprendizaje de reglas retóricas.

---

## 📂 Estructura del Proyecto

*   `main.py`: Bucle de consciencia principal.
*   `agents.py`: Agentes Cognitivos (Monitor, Razonamiento, Empatía, Motivación).
*   `dream_engine.py`: Hilo de fondo para autonomía.
*   `memory_systems.py`: Motores de Grafo (SQLite) y Vectorial (ChromaDB).
*   `dashboard.py`: Servidor Web Flask.
*   `knowledge_graph.db`: El cerebro persistente.

---

## 📚 Referencias y Papers Implementados

La arquitectura del sistema se basa en los siguientes componentes de investigación (ver carpeta `papers/`):

1.  **Engram**: Es el almacén de datos (Memoria).
    *   *Implementación*: `memory_systems.py` (GraphEngram).
2.  **Sophia (Paper)**: Es el supervisor (Consciencia).
    *   *Implementación*: `agents.py` (Monitor/Consciencia).
3.  **HRM**: Es el filtro de calidad (Rigor).
    *   *Implementación*: `AgentCheck.validate_response`.
4.  **RSA**: Es el motor de síntesis (Sabiduría).
    *   *Implementación*: `AgentReasoning` (Bucle de Pensamiento Profundo).

---
**Licencia:** MIT
