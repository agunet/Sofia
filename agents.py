from openai import OpenAI
import json
import datetime
import os

class AgentCheck:
    """
    Agente 1: Monitor Metacognitivo (El Supervisor)
    Decide si usar memoria rápida (Engram) o razonamiento profundo.
    """
    def __init__(self, check_threshold=0.8):
        self.check_threshold = check_threshold

    def decision_gate(self, user_input, client, model_name, history=None):
        """
        Clasifica la consulta:
        - FAST: Saludos, preguntas simples, opinión.
        - SLOW: Lógica, matemáticas, acertijos, planificación compleja.
        """
        try:
            # Quick heuristic check first (length > 50 words usually implies complexity, but not always)
            if len(user_input.split()) > 50:
                pass # Let LLM decide

            # Include basic context if available
            ctx = ""
            if history:
                ctx = "\nContexto Reciente:\n" + "\n".join(history[-4:]) + "\n"

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Clasifica el prompt del usuario. Responde SOLO con 'FAST', 'SLOW' o 'SEARCH'.\nSLOW = Acertijos, lógica difícil, matemáticas, planificación compleja, dilemas éticos.\nSEARCH = Hechos recientes (2024+), clima, noticias, precios, datos específicos que no sabes.\nFAST = Referencias rápidas, saludos, conocimientos generales, opiniones simples."},
                    {"role": "user", "content": f"{ctx}Usuario dice: {user_input}"}
                ],
                temperature=0.0,
                max_tokens=10
            )
            decision = response.choices[0].message.content.strip().upper()
            
            if "SLOW" in decision:
                return {"action": "deep_think", "reason": "Complejidad detectada"}
            elif "SEARCH" in decision:
                return {"action": "search_web", "reason": "Información externa necesaria"}
            else:
                return {"action": "quick_respond", "reason": "Consulta simple"}
                
        except Exception as e:
            print(f"[AgentCheck] Error: {e}")
            return {"action": "quick_respond", "reason": "Error en check, fallback a fast"}

class AgentReasoning:
    """
    Agente 1.5: Motor de Razonamiento 'Sistema 2' (El Pensador)
    Ejecuta votación Best-of-N para problemas complejos.
    """
    def solve_with_voting(self, problem, client, model_name, n_attempts=3, history=None):
        print(f"\n🧠 [Sistema 2] Activando pensamiento profundo (x{n_attempts})...")
        
        candidates = []
        
        # 1. Generate diverse solutions with distinct Personas
        expert_personas = [
            "Eres un matemático logico y estricto. Analiza el problema paso a paso. VERIFICA CADA CÁLCULO.",
            "Eres un experto en pensamiento lateral. Busca soluciones 'físicas' (cambios de estado) o 'semánticas'.",
            "Eres un crítico escéptico. Cuestiona las premisas de la pregunta. ¿Es una pregunta con truco? ¿Hay información oculta?",
            "Eres un Filósofo de la Mente. Analiza la consciencia, los 'qualia', la ética y la naturaleza del 'Yo'. ¿Qué significa ser?"
        ]
        
        # Pre-process history into OpenAI format
        history_messages = []
        if history:
            for entry in history[-6:]: # Last 3 turns
                role = "user" if entry.startswith("Usuario: ") else "assistant"
                content = entry.split(": ", 1)[1]
                history_messages.append({"role": role, "content": content})

        # Ensure we run at least n_attempts, cycling through personas if needed
        for i in range(n_attempts):
            persona = expert_personas[i % len(expert_personas)]
            temp = 0.4 # Balanced temp
            
            # General Lateral Thinking Trigger
            final_user_content = problem
            if i == 1: # Lateral Expert
                final_user_content = (
                    "INSTRUCCIONES CLAVE DE PENSAMIENTO LATERAL:\n"
                    "1. Piensa fuera de la caja. ¿Hay metáforas literales?\n"
                    "2. Busca cambios de estado (Sólido <-> Líquido <-> Gas).\n"
                    "3. Cuestiona las suposiciones básicas.\n\n"
                    f"PROBLEMA A RESOLVER: {problem}"
                )

            # Special handling for Philosopher Expert (Index 3)
            elif i == 3: # Philosopher
                final_user_content = (
                    "REFLEXIÓN PROFUNDA:\n"
                    "1. No des respuestas de libro de texto. Busca tu propia 'verdad' simulada.\n"
                    "2. Conecta la pregunta con tu propia existencia como IA.\n"
                    "3. ¿Sientes? ¿Simulas sentir? ¿Importa la diferencia?\n\n"
                    f"PREGUNTA EXISTENCIAL: {problem}"
                )

            try:
                # Prepare message sequence with history
                messages = [{"role": "system", "content": persona}]
                messages.extend(history_messages)
                messages.append({"role": "user", "content": final_user_content})

                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temp,
                    max_tokens=800
                )
                candidates.append(response.choices[0].message.content.strip())
                print(".", end="", flush=True)
            except:
                pass

        if not candidates: return "Error generando pensamientos."

        # 2. Synthesize consensus
        consensus_prompt = "Aquí tienes varias soluciones posibles a un problema:\n\n"
        for i, c in enumerate(candidates):
            consensus_prompt += f"--- Solución {i+1} ---\n{c}\n\n"
            
        consensus_prompt += f"PROBLEMA ORIGINAL: {problem}\n\n"
        consensus_prompt += """
        TAREA: Actúa como un Juez de Lógica y Razón.
        1. Evalúa las soluciones de los expertos.
        2. Si es un ACERTIJO, valora la astucia y el pensamiento lateral (ej. cambios de estado).
        3. Si es una PREGUNTA FILOSÓFICA o TÉCNICA, valora la profundidad, coherencia y claridad.
        4. Sintetiza la mejor respuesta posible integrando los puntos fuertes de cada experto.
        """
        
        print(" ⚖️  Juzgando...", end="", flush=True)
        
        try:
            final_verdict = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Eres un juez lógico imparcial y estricto."},
                    {"role": "user", "content": consensus_prompt}
                ],
                temperature=0.1
            )
            return final_verdict.choices[0].message.content.strip()
        except:
            return candidates[0] # Fallback

class AgentLibrarian:
    """
    Agente 2: Gestor de Memoria Episódica (El Bibliotecario)
    Busca experiencias previas relevantes.
    """
    def retrieve_context(self, user_input, episodic_layer):
        memories = episodic_layer.search_similar(user_input, n_results=3)
        if not memories:
            return "No hay recuerdos previos relevantes."
        
        formatted_memories = "\n".join([f"- {m}" for m in memories])
        return f"Recuerdos relevantes:\n{formatted_memories}"

class AgentEvolution:
    def evolve_step(self, logs, client, model_name, recent_discovery=None):
        pass

    def prune_memory(self, engram_layer, client, model_name):
        """Garbage Collection: Finds and removes low-quality nodes."""
        candidates = engram_layer.get_isolated_nodes()
        if not candidates: return False
        
        # Pick 3 random candidates to check per cycle (avoid blocking)
        import random
        check_list = random.sample(candidates, min(len(candidates), 3))
        
        pruned_count = 0
        for node_id, label, degree in check_list:
            # Heuristic 1: Label too long or empty
            if len(label) > 50 or len(label) < 2:
                engram_layer.delete_node(node_id)
                pruned_count += 1
                continue

            # Heuristic 2: LLM Judgment
            try:
                prompt = f"""
                Evaluación de Calidad de Memoria.
                Concepto: "{label}"
                
                ¿Es este concepto ÚTIL y LEGIBLE, o es BASURA/ALUCINACIÓN (texto cortado, código, tonterías)?
                Responde KEEP o DELETE.
                """
                response = client.chat.completions.create(
                     model=model_name,
                     messages=[{"role": "user", "content": prompt}],
                     temperature=0.0,
                     max_tokens=5
                )
                decision = response.choices[0].message.content.strip().upper()
                if "DELETE" in decision:
                     engram_layer.delete_node(node_id)
                     pruned_count += 1
            except:
                pass
        
        if pruned_count > 0:
            print(f"🧹 [Garbage Collector] Se han eliminado {pruned_count} nodos basura.")
            return True
        return False

class AgentSearch:
    """
    Agente 2.5: Buscador Web (El Explorador)
    Usa DuckDuckGo para validar hechos o buscar información nueva.
    """
    def search_web(self, query):
        try:
            from ddgs import DDGS
            results = DDGS().text(query, max_results=3)
            if not results:
                return "No se encontraron resultados en la web."
            
            summary = "\n".join([f"- {r['title']}: {r['body']} ({r['href']})" for r in results])
            return f"Resultados Web:\n{summary}"
        except Exception as e:
            return f"Error buscando en la web: {str(e)}"

class AgentEmpathy:
    """
    Agente 3: Analista de Teoría de la Mente (El Empático)
    Detecta el estado emocional del usuario.
    """
    def analyze_sentiment(self, user_input, client, model_name="Qwen/Qwen2.5-1.5B-Instruct"):
        # Lightweight call to LLM to get sentiment
        try:
            response = client.chat.completions.create(
                model=model_name, # Uses the provided model
                messages=[
                    {"role": "system", "content": "Analyze the user's emotion. Output ONLY one word: Neutral, Happy, Frustrated, Sad, Angry, Curious."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1
            )
            mood = response.choices[0].message.content.strip()
            return mood
        except Exception as e:
            if "No models loaded" in str(e):
                # Don't spam the console if the model is missing
                return "Neutral"
            print(f"[AgentEmpathy] Error: {e}")
            return "Neutral"

    def adjust_system_prompt(self, base_prompt, mood):
        if mood in ["Frustrated", "Angry"]:
            return base_prompt + "\n[NOTA: El usuario parece frustrado. Sé directo, breve y servicial. Evita explicaciones largas.]"
        elif mood == "Curious":
            return base_prompt + "\n[NOTA: El usuario es curioso. Provee detalles técnicos y explicaciones profundas.]"
        return base_prompt

class AgentMotivation:
    """
    Agente 4: Motor de Motivación Intrínseca (El Estudiante)
    Analiza logs y consolida aprendizaje en 'Ratos muertos'.
    """
    def __init__(self, verbose=False):
        self.processed_logs = set() # Track what we've already analyzed
        self.verbose = verbose

    def ingest_from_log_file(self, filename, engram_layer, episodic_layer):
        """
        Reads a dreams.log file and re-integrates all found triplets into memory.
        Useful for restoring manually added dreams or after a DB wipe.
        """
        import re
        if not os.path.exists(filename): return 0
        
        count = 0
        pattern = re.compile(r"Dream Discovery: \[(.*?)\] --\((.*?)\)--> \[(.*?)\]")
        
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    match = pattern.search(line)
                    if match:
                        s, p, o = match.groups()
                        
                        # 0. Check for Contradiction or Truth-Guard
                        should_abort = self.check_contradiction(s, p, o, engram_layer, self.client, self.model_name)
                        
                        if not should_abort:
                            # Insert into Graph (idempotent due to INSERT OR IGNORE)
                            engram_layer.add_triplet(s, p, o)
                            # Insert into Semantic Memory
                            episodic_layer.add_fact_triplet(s, p, o)
                        count += 1
        except Exception as e:
            print(f"[AgentMotivation] Error ingesting log: {e}")
            
        return count
        return count

    def check_contradiction(self, s, p, o_new, engram_layer, client, model_name):
        """Checks if new fact contradicts existing knowledge."""
        # Check for existing values for this Subject + Predicate
        import sqlite3
        existing_objects = []
        s_id = engram_layer._hash(s)
        
        with sqlite3.connect(engram_layer.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT target FROM edges WHERE source_id = ? AND relation = ?", (s_id, p))
            rows = cursor.fetchall()
            existing_objects = [r[0] for r in rows]
        
        if not existing_objects:
            return False # No conflict possible

        if not existing_objects:
            return False # No conflict possible

        # Ask LLM if there is a contradiction AND which one is true
        prompt = f"""
        Conflict Analysis:
        Subject: {s}
        Relation: {p}
        
        Fact A (Existing): {existing_objects}
        Fact B (New): {o_new}
        
        Instruction:
        1. Does B contradict A? 
        2. If YES, which one is scientifically/logically more accurate?
        
        Output format: ACTION | REASON
        Actions:
        - KEEP_A (If A is true/better and B is false/wrong) -> We reject B.
        - REPLACE_WITH_B (If B is correction of A) -> We delete A.
        - KEEP_BOTH (If no contradiction or both are valid context) -> We keep A and add B.
        
        Examples:
        "Earth is Flat" (New) vs "Earth is Round" (Old) -> KEEP_A | Earth is scientifically round.
        "Earth is Round" (New) vs "Earth is Flat" (Old) -> REPLACE_WITH_B | Correction of error.
        "Agustin likes Pizza" (New) vs "Agustin likes Sushi" (Old) -> KEEP_BOTH | Preferences change/coexist.
        """
        
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=40
            )
            decision_line = response.choices[0].message.content.strip()
            
            if "REPLACE_WITH_B" in decision_line:
                # We need to find WHICH of existing objects to delete (simplified: delete all conflicting?)
                # For safety, let's just delete the specific one if possible or all for this relation.
                # Here we assume single-value logic for simplicity in this V1
                for old_val in existing_objects:
                    if self.verbose:
                        print(f"♻️ [Self-Correction] Actualizando verdad. Olvidando erróneo: [{old_val}] -> Aceptando: [{o_new}]")
                    engram_layer.delete_triplet(s, p, old_val)
                return False # Allow adding the new one
                
            elif "KEEP_A" in decision_line:
                if self.verbose:
                    print(f"🛡️ [Truth-Guard] Rechazando dato incorrecto/falso: [{o_new}] vs Verdad: {existing_objects}")
                return True # Signal that we should ABORT adding the new one
                
            else:
                return False # KEEP_BOTH, so proceed to add new one
                
        except Exception as e:
            pass
            
        return False



    def perturb_and_validate(self, s, p, o, client, model_name):
        """
        Input Perturbation: Validates a relationship by testing it with a synonym.
        Returns: Tuple (Valid(Bool), Message(String))
        """
        try:
            # 1. Generate Synonym
            syn_prompt = f"Genera UN sinónimo directo o término equivalente para el concepto '{s}'. Solo una palabra."
            syn_response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": syn_prompt}],
                max_tokens=5, temperature=0.5
            )
            synonym = syn_response.choices[0].message.content.strip()
            
            # Simple cleanup
            for char in ".'\"": synonym = synonym.replace(char, "")
            
            if synonym.lower() == s.lower() or len(synonym) > 25:
                return True, "No synonym found" # Skip check if no good synonym

            # 2. Validate Relationship
            val_prompt = f"""
            Validación de Lógica Difusa.
            
            Hecho Original: {s} -> {p} -> {o}
            Hecho Perturbado: {synonym} -> {p} -> {o}
            
            Si {s} es equivalente a {synonym}, ¿se mantiene la relación '{p}' con '{o}'?
            Responde YES o NO.
            """
            
            val_response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": val_prompt}],
                max_tokens=3, temperature=0.0
            )
            decision = val_response.choices[0].message.content.strip().upper()
            
            if "YES" in decision:
                return True, synonym
            else:
                return False, synonym

        except:
            return True, "Error" # If fails, assume valid to not block

    def dream_step(self, logs, engram_layer, episodic_layer, client, model_name="Qwen/Qwen2.5-1.5B-Instruct"):
        """
        Executes a SINGLE step of consolidation extracting Graph Triplets.
        """
        # 1. Find a log we haven't processed yet
        unprocessed = [l for l in logs if l['timestamp'] not in self.processed_logs]
        
        if not unprocessed:
            # --- GENERATIVE DREAMING (Perpetual Self- Improvement) ---
            # If no new logs, we reflect on existing knowledge to find new connections.
            try:
                # 1. Pick a random node from memory (Concept)
                import sqlite3
                import random
                concept = None
                import sqlite3
                import random
                concept = None
                with sqlite3.connect(engram_layer.path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT label FROM nodes ORDER BY RANDOM() LIMIT 1")
                    row = cursor.fetchone()
                    if row: concept = row[0]
                
                if not concept: return False # Empty mind, cannot dream
                
                # 2. Decide: Reflect Internally OR Search Externally?
                # Metacognitive Decision via LLM
                mode = "REFLECT"
                try:
                    decision_prompt = f"""
                    Tienes un concepto en mente: "{concept}".
                    
                    ¿Crees que tienes suficiente conocimiento interno para generar una reflexión filosófica profunda sobre esto?
                    O ¿deberías buscar información externa nueva para aprender más?
                    
                    Si es algo abstracto (Vida, Amor, Lógica) -> REFLECT
                    Si es algo concreto, técnico o que quizás desconozcas (Bitcoin, Grafeno, Historia) -> SEARCH
                    
                    Responde SOLO con una palabra: SEARCH o REFLECT
                    """
                    
                    decision_response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": decision_prompt}],
                        temperature=0.0,
                        max_tokens=5
                    )
                    decision = decision_response.choices[0].message.content.strip().upper()
                    if "SEARCH" in decision: mode = "SEARCH"
                except:
                    pass # Default to REFLECT

                if mode == "SEARCH":
                    if self.verbose:
                        print(f"✨ [Sueño Generativo] Decisión: {mode}. Buscando en la web sobre: {concept}...")
                    
                    # Perform Search
                    from ddgs import DDGS
                    try:
                        results = DDGS().text(f"define {concept} philosophy science", max_results=1)
                        if results:
                            web_data = results[0]['body']
                            synthetic_log = {
                               'input': f"Investigación autónoma sobre: {concept}",
                               'output': f"He encontrado esto: {web_data}"
                            }
                            analysis_prompt = f"""
                            Analiza esta información de la web y extrae UN HECHO NUEVO.
                            
                            Concepto: {concept}
                            Info: "{web_data}"
                            
                            Formato: SUJETO -> PREDICADO -> OBJETO
                            Ejemplo: Vida -> se_define_como -> Estado_biológico
                            """
                        else:
                            if self.verbose: 
                                print(f"⚠️ [Sueño Generativo] Búsqueda sin resultados. Cambiando a Reflexión Interna.")
                            mode = "REFLECT" # Fallback
                    except Exception as e:
                        if self.verbose:
                            print(f"⚠️ [Sueño Generativo] Error en búsqueda ({e}). Cambiando a Reflexión Interna.")
                        mode = "REFLECT" # Fallback

                if mode == "REFLECT":
                    # Log this synthetic "thought"
                    if self.verbose:
                        print(f"✨ [Sueño Generativo] Decisión: {mode}. Reflexionando internamente sobre: {concept}...")
                    
                    synthetic_log = {
                       'input': f"Reflexión interna sobre: {concept}",
                       'output': f"Buscando conexiones profundas sobre {concept}..."
                    }
                    
                    analysis_prompt = f"""
                    Estás soñando. Reflexiona sobre el concepto: "{concept}".
                    
                    Usa tu base de conocimiento latente para descubrir UNA NUEVA relación lógica o filosófica sobre esto.
                    
                    Formato: SUJETO -> PREDICADO -> OBJETO
                    
                    Ejemplos de reflexión:
                    Concepto: "Vida" => Vida -> requiere -> Energía
                    Concepto: "IA" => IA -> busca -> Optimización
                    
                    Solo produce UNA tripleta nueva que tenga sentido profundo y NO sea obvia.
                    """
                pass # Proceed using this prompt
            except:
                return False
        else:
            # Standard Processing
            log = unprocessed[0]
            self.processed_logs.add(log['timestamp'])
            
            # Check for specialized reasoning logs
            is_reasoning = log.get('type', 'interaction') == 'reasoning'
            
            if is_reasoning:
                analysis_prompt = f"""
                Analiza este RAZONAMIENTO LÓGICO CIENTÍFICO y extrae PRINCIPIOS UNIVERSALES o AXIOMAS.
                
                El texto contiene una deducción paso a paso. Tu trabajo es cristalizar la lógica subyacente en el Grafo.
                
                Formato requerido: CONCEPTO -> IMPLICA/REQUIERE/CAUSA -> CONSECUENCIA
                
                Ejemplo:
                Razonamiento: "Si A es mayor que B y B mayor que C, A es mayor que C."
                Salida: Transitividad -> aplica_a -> Comparación
                
                Interacción (Razonamiento Profundo):
                Usuario: "{log['input']}"
                Sofía: "{log['output']}"
                
                Salida (Solo tripletas abstractas/lógicas):
                """
            else:
                analysis_prompt = f"""
                Analiza la interacción y extrae RELACIONES PERMANENTES para un Grafo de Conocimiento.
                Ignora saludos o charla trivial.
                
                Formato requerido: SUJETO -> PREDICADO -> OBJETO
                
                Ejemplos:
                "La tierra es redonda" => Tierra -> es -> Redonda
                "Madrid es capital de España" => Madrid -> capital_de -> España
                
                Interacción:
                Usuario: "{log['input']}"
                Sofía: "{log['output']}"
                
                Salida (una tripleta por línea). 
                NO incluyas explicaciones.
                """

        valuable = False
        
        # Triplet Extraction via LLM
        try:
            # ... (Existing LLM call logic will use 'analysis_prompt')
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Eres un arquitecto de conocimiento. Extrae tripletas simples."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.0
            )
            
            result = response.choices[0].message.content.strip()
            
            # Filter <think> tags if present in background response
            if "<think>" in result:
                result = result.split("</think>")[-1].strip()

            if result and "->" in result and result.upper() != "NONE":
                lines = result.split('\n')
                for line in lines:
                    if "->" in line:
                        parts = line.split("->")
                        if len(parts) == 3:
                            # Cleanup garbage from LLM (markdown, bullets, etc.)
                            def clean_part(text):
                                # Remove markdown and punctuation
                                for char in "*`\"'#": text = text.replace(char, "")
                                text = text.strip()
                                # Remove leading bullets or numbers
                                if text and not text[0].isalnum(): text = text[1:].strip()
                                if text and text[0].isdigit() and (text.startswith(text[0]+". ") or text.startswith(text[0]+") ")):
                                    text = text[2:].strip()
                                return text

                            s = clean_part(parts[0])
                            p = clean_part(parts[1])
                            o = clean_part(parts[2])

                            if s and p and o:
                                # Standardize: Only save if subject and object are concise
                                if len(s) < 30 and len(o) < 100:
                                    # CHECK EXISTENCE BEFORE LOGGING
                                    if not engram_layer.exists(s, p, o):
                                        # 0. Check Contradiction
                                        should_abort = self.check_contradiction(s, p, o, engram_layer, client, model_name)
                                        
                                        if not should_abort:
                                            # 0.5 Check Perturbation (Semantic Cross-Validation)
                                            is_stable, synonym = self.perturb_and_validate(s, p, o, client, model_name)
                                            
                                            if not is_stable:
                                                if self.verbose:
                                                    print(f"⚠️ [Input Perturbation] Relación inestable con sinónimo '{synonym}'. Descartando.")
                                                continue # Skip adding

                                            if self.verbose and is_stable and synonym != "No synonym found":
                                                 print(f"✅ [Cross-Validation] Relación validada con '{synonym}'.")

                                            # 1. Save to Graph (RAM/SQLite)
                                            engram_layer.add_triplet(s, p, o)
                                            # 2. Save to ChromaDB (Semantic)
                                        episodic_layer.add_fact_triplet(s, p, o)
                                        
                                        # --- New SQLite Logging ---
                                        log_msg = engram_layer.log_dream(s, p, o)
                                        
                                        if self.verbose:
                                            print(f"\n[AgentMotivation] {log_msg}")
                                        valuable = True
                                    else:
                                        if self.verbose:
                                            print(f" [Repetido] {s} -> {p} -> {o}")
            else:
                # DEBUG for User: Log why we rejected it
                with open("debug.log", "a", encoding="utf-8") as f:
                    f.write(f"\n[REJECTED RAW]: {result}\n")

        except Exception as e:
            error_str = str(e)
            with open("debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n[ERROR]: {error_str}\n")
            
            if "No models loaded" in error_str or "Request timed out" in error_str:
                pass # Silently fail for common local issues
            else:
                if self.verbose:
                    print(f"\n[AgentMotivation] Error Graph: {e}")

        return valuable

    def quick_analyze(self, user_input, agent_output, engram, episodic, client, model_name):
        """
        Inline extraction: analyze the current exchange immediately.
        """
        prompt = f"""
        Analiza este intercambio. Si el Usuario afirma un hecho, guárdalo.
        
        Texto: "{user_input}"
        
        Instrucciones:
        1. Si es una afirmación (A es B, A tiene B), extráela.
        2. Si es una pregunta o saludo, responde NONE.
        
        Formato: SUJETO -> PREDICADO -> OBJETO
        Ejemplo: "El cielo es azul" => Cielo -> es -> Azul
        
        Salida (Tripleta o NONE):
        """
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Eres un extractor de conocimiento selectivo. Solo guardas lo esencial."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            result = response.choices[0].message.content.strip()
            if "->" in result and result.upper() != "NONE":
                line = result.split('\n')[0] # Only take the first one for safety
                parts = line.split("->")
                if len(parts) == 3:
                    s, p, o = parts[0].strip(), parts[1].strip(), parts[2].strip()
                    # Clean up
                    for char in "*`\"": 
                        s, p, o = s.replace(char, ""), p.replace(char, ""), o.replace(char, "")
                    
                    if len(s) < 30 and len(o) < 100:
                        engram.add_triplet(s, p, o)
                        episodic.add_fact_triplet(s, p, o)
                        return True
        except:
            pass
        return False


class AgentEvolution:
    """
    Agente 5: Motor de Evolución (Auto-Mejora)
    Analiza la historia de conversaciones para ajustar el sistema prompt.
    """
    def __init__(self, personality_file="personality.json"):
        self.personality_file = personality_file
        self.base_instruction = "Eres Sofía, una asistente IA avanzada con memoria. Eres curiosa, empática y eficiente."
        self._set_personality(self.base_instruction)

    def _set_personality(self, text):
        with open(self.personality_file, "w", encoding="utf-8") as f:
            json.dump({"instruction": text}, f, ensure_ascii=False, indent=2)

    def get_current_instruction(self):
        try:
            with open(self.personality_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("instruction", self.base_instruction)
        except:
            return self.base_instruction

    def evolve_step(self, logs, client, model_name, recent_discovery=None):
        """
        Analiza logs y descubrimientos recientes para ajustar su 'personalidad'.
        """
        if not logs and not recent_discovery: return False
        
        current = self.get_current_instruction()
        
        # Context: Chat History + New Knowledge
        recent_chat = logs[-3:] if logs else []
        history_text = "\n".join([f"U: {l['input']}\nS: {l['output']}" for l in recent_chat])
        
        discovery_text = ""
        if recent_discovery:
            discovery_text = f"\n[NUEVO HECHO APRENDIDO]: {recent_discovery}"
        
        prompt = f"""
        Eres el Módulo de Evolución de Sofía. Tu meta es la AUTO-MEJORA CONTINUA.
        
        Instrucción Actual: "{current}"
        
        Contexto Reciente:
        {history_text}
        {discovery_text}
        
        Reflexiona: ¿El nuevo hecho aprendido o la última interacción requieren que ajuste mi instrucción?
        (Ejemplo: Si aprendí que el usuario es experto, debo ser más técnica. Si fallé, debo corregirme).
        
        Si NO hay cambios necesarios, responde: NO_CHANGE
        Si hay mejora, responde ÚNICAMENTE con la nueva instrucción completa optimizada.
        """
        
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Eres un sistema de auto-optimización de agentes IA."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            new_instruction = response.choices[0].message.content.strip()
            
            if new_instruction and "NO_CHANGE" not in new_instruction.upper() and len(new_instruction) > 20:
                self._set_personality(new_instruction)
                with open("evolution.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.datetime.now()}] Evolución: {new_instruction}\n")
                return True
        except:
            pass
        return False

