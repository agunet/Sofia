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
*   **Razonamiento de Enjambre Híbrido:** Integra expertos fijos (Lógico, Lateral, Escéptico, Filósofo) con **Múltiples Expertos Generados Dinámicamente** (Legión JIT). El sistema decide cuántos y qué tipo de especialistas invitar a la mesa.
*   **Consenso Adversarial:** Antes de la respuesta final, los agentes entran en una **"Ronda de Crítica"**. Se atacan mutuamente buscando falacias lógicas. Solo los argumentos que sobreviven al "Fiscal" pasan a la síntesis final.
*   **Investigación Profunda Autónoma:** El Sistema 2 tiene "ojos". Detecta proactivamente vacíos de información, realiza **Búsquedas Autónomas**, selecciona las mejores fuentes y **Lee en Profundidad** antes de debatir.
*   **Enjambre Transitorio:** Los agentes nacen, resuelven y desaparecen. Sin registros persistentes.
*   **Transparencia:** Puedes ver el pensamiento en vivo (`↳ [Swarm] Invitando a la mesa...`).
*   **Caché de Razonamiento:** Si resuelve un problema difícil, recuerda la *lógica*. La próxima vez responde al instante (`⚡ [Cache]`).
*   **Laboratorio Mental:** Simula escenarios hipotéticos (`/simulate`) sin confundirlos con la realidad.

### 3. Memoria Persistente y Auto-Reparable 💾
*   **Ghost Anchors (Contexto Infinito):** Cuando la memoria RAM se llena, los recuerdos menos usados no se borran. Se comprimen en **"Fantasmas"** (anclajes de texto de alta densidad) que permanecen en el contexto, evitando la amnesia sin saturar la VRAM.
*   **Grafo de Conocimiento (SQLite):** Guarda hechos (`Sofía -> es -> IA`).
*   **Auto-Corrección:** Si le dices "Eso es mentira", busca el recuerdo específico y castiga su nivel de confianza.
*   **Síntesis:** Algoritmos que extraen reglas abstractas de datos repetitivos.
*   **Estrategia Social:** Analiza *cómo* hablas y adapta su estilo (Conciso, Técnico, ELI5).

### 4. Sueño Generativo (Autonomía y Génesis) 🌌
Cuando está inactiva, Sofía entra en **"Modo Sueño"**:
*   **Reflexiona** sobre memorias existentes.
*   **Investiga** en la web para llenar vacíos de conocimiento.
*   **Sistema Límbico (Motivación Intrínseca):** Su curiosidad no es aleatoria. Está impulsada por `drives.json` (Curiosidad, Coherencia, Novedad, Profundidad).
*   **Agencia Dirigida:** Guiada por `objectives.json`, enfoca su investigación en límites específicos (ej. Filosofía de la Ciencia) y evita el ruido.
*   **Sueño Adaptativo:** Gestiona su energía: duerme más cuando no hay nada nuevo que aprender y despierta rápido cuando la curiosidad llega al máximo.

---

## 🛠️ Instalación y Requisitos
... [Resto de instalación] ...

## ▶️ Uso
... [Resto de uso] ...

---

## 🎮 Comandos

Mientras chateas en `main.py` o usas el Dashboard:

| Comando | Descripción |
| :--- | :--- |
| `/focus <tema>` | Fuerza al motor de sueño a estudiar un tema específico. |
| `/drives` | Muestra el estado actual del Sistema Límbico (Impulsos Internos). |
| `/set_drive <nombre> <0-1>` | Ajusta manualmente las motivaciones de Sofía (ej. `/set_drive curiosity 0.9`). |
| `/current_focus` | Muestra los límites de investigación activos de `objectives.json`. |
| `/explain_motivation <X>` | Le pide a Sofía que justifique por qué le interesa investigar el tema X. |
| `/simulate <qué pasaría si>` | Ejecuta una simulación de alta fidelidad. |
| `/synthesize` | Dispara la compresión de memoria (Extracción de Reglas). |
| `/log` | Activa/Desactiva logs detallados en la terminal. |
| `Mentira/Incorrecto` | Dispara el **Feedback Loop** para corregir errores. |

---

## 📜 Lista Completa de Features (V2.5)

### Núcleo Cognitivo
- [x] **Enjambre Híbrido:** Inyección dinámica de agentes especialistas.
- [x] **Arquitectura Transitoria:** Generación stateless de agentes.
- [x] **Auto-Juez:** Sistema de puntuación (0-10) para validar respuestas.
- [x] **Verificador de Hechos:** Cotejo contra el Grafo interno.
- [x] **Perfilado de Usuario:** Detección de humor y estilo preferido.
- [x] **Trazas de Meta-Razonamiento:** Visualización del hilo de pensamiento.

### Memoria y Aprendizaje
- [x] **Grafo Ponderado:** Nodos con scores de importancia y confianza.
- [x] **Feedback Loop:** Castigo y eliminación de nodos.
- [x] **Consolidation Total:** Síntesis de hechos + Auto-Poda.
- [x] **Caché de Razonamiento:** "Memoria Muscular" para problemas complejos.
- [x] **Filtro de Relevancia Semántica:** Poda por distancia cosidinal.
- [x] **Poda Sináptica:** Eliminación autónoma de memorias débiles.
- [x] **Ghost Anchors (Fantasmas):** Retención de contexto basada en resúmenes.

### Autonomía y Agencia
- [x] **Sueño Dirigido:** Capacidad de enfocar al agente autónomo.
- [x] **Sistema Límbico:** Motivación intrínseca mediante recompensas de Curiosidad/Coherencia.
- [x] **Investigación Orientada a Objetivos:** Filtrado de temas basado en metas a largo plazo.
- [x] **Laboratorio Mental:** Motor de simulación para contrafactuales.
- [x] **Registro de Logros:** Los descubrimientos de alto impacto se graban en `achievements.log`.
- [x] **Investiga Autónoma:** Capacidad de leer artículos web completos.

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
