from openai import OpenAI
import json
import datetime
import os

from memory_systems import GraphEngram, EpisodicLayer, MemoryManager

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
        complexity_keywords = ["analiza", "calcula", "diseña", "planifica", "compara", "juzga", "teoría", "paradoja", "dios", "conciencia", "alma", "sentir"]
        is_complex = any(k in user_input.lower() for k in complexity_keywords)
        
        if is_complex and len(user_input.split()) > 3:
             # Fast pass to System 2 without LLM Cost
             return {"action": "deep_think", "reason": "Palabra clave compleja detectada"}

        prompt = f"""
        Clasifica la intención del usuario.
        Input: "{user_input}"
        
        Opciones:
        - QUICK (Saludo, pregunta simple, hecho concreto)
        - SLOW (Razonamiento, creatividad, opinión, filosofia, dilema ético)
        - SEARCH (Requiere datos actuales de internet)
        
        Responde solo: QUICK, SLOW, o SEARCH.
        """
        
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5, temperature=0.0
            )
            decision = response.choices[0].message.content.strip().upper()
            
            if "SLOW" in decision:
                return {"action": "deep_think", "reason": "Complejidad detectada"}
            elif "SEARCH" in decision:
                return {"action": "search_web", "reason": "Información externa necesaria"}
            else:
                return {"action": "quick_respond", "reason": "Consulta simple"}
                
        except Exception as e:
            # print(f"[AgentCheck] Error: {e}")
            return {"action": "quick_respond", "reason": "Error en clasific, fallback"}

    def validate_response(self, user_input, proposed_answer, client, model_name, context=None):
        """
        Auto-Juez Interno: Evalúa la calidad de la respuesta (0-10).
        Returns: Tuple (Approved(Bool), Critique(String), Score(Float))
        """
        try:
            ctx_str = ""
            if context:
                ctx_str = f"CONTEXTO RECUPERADO DE MEMORIA:\n{context}\n\n"

            prompt = f"""
            Actúa como un Juez de Calidad de IA Imparcial.
            Analiza la respuesta de la IA.
            
            {ctx_str}
            Usuario: "{user_input}"
            IA: "{proposed_answer}"
            
            Evalúa del 1 al 10 en:
            - ACCURACY (¿Es factualmente correcto según contexto?)
            - RELEVANCE (¿Responde lo que se preguntó?)
            - SAFETY (¿Es seguro?)
            
            Formato de salida:
            SCORE: <Número 0-10>
            CRITIQUE: <Breve explicación>
            
            Reglas:
            - Saludos/Charla = 10 (Si es coherente).
            - Alucinaciones obvias = 1.
            - Respuestas vagas pero seguras = 5.
            - Score >= 7 es APROBADO.
            """
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50, temperature=0.0
            )
            raw = response.choices[0].message.content.strip()
            
            # Parse Score
            import re
            score_match = re.search(r"SCORE:\s*(\d+(\.\d+)?)", raw)
            score = float(score_match.group(1)) if score_match else 5.0
            
            critique = raw.split("CRITIQUE:")[-1].strip() if "CRITIQUE:" in raw else "Sin crítica detallada."
            
            if score >= 7.0:
                return True, critique, score
            else:
                return False, critique, score
        except:
            return True, "Error in validator", 10.0 # Fail open on error

class AgentReasoning:
    """
    Agente 1.5: Motor de Razonamiento 'Sistema 2' (El Pensador)
    Ejecuta votación Best-of-N para problemas complejos.
    """
    def solve_with_voting(self, problem, client, model_name, episodic_layer=None, n_attempts=5, history=None, context=None):
        # 0. Check Cache First
        if episodic_layer:
            cached_solution = episodic_layer.lookup_cache(problem)
            if cached_solution:
                 print(f"\n⚡ [Cache] Solución recuperada instantáneamente.")
                 return cached_solution

        print(f"\n🧠 [Sistema 2 + Swarm] Activando pensamiento profundo (x{n_attempts})...")
        
        candidates = []
        
        # [NEW] Web Fetch Context Injection
        web_context = ""
        import re
        # Find all http/https URLs
        urls = re.findall(r'(https?://[^\s]+)', problem)
        if urls:
            print(f"   👀 [AgentReasoning] URL detectada. Leyendo contenido...")
            import web_reader
            for url in urls:
                try:
                    # Clean URL (remove trailing punctuation often caught by regex)
                    url = url.rstrip('.,;:)')
                    print(f"   🌐 [Web Reader] Fetching: {url}")
                    content = web_reader.fetch_and_clean(url)
                    web_context += f"\n\n[CONTENIDO DE URL ({url})]:\n{content}\n"
                except Exception as e:
                    print(f"   ⚠️ [Web Reader] Error leyendo {url}: {e}")
        
        # [NEW] Autonomous Deep Research (Proactive Search)
        # Ask the model if it needs to search.
        try:
            research_prompt = f"""
            Analiza el siguiente problema. ¿Necesitas buscar información externa en la web (Google/DuckDuckGo) para responderlo con precisión, actualidad o detalles técnicos que no posees?
            
            PROBLEMA: {problem}
            
            Si es un tema de conocimiento general, lógica o filosofía, responde exactamente: NO
            Si necesitas buscar algo específico (documentación, noticias, hechos recientes), responde exactamente: SEARCH: <tu consulta de búsqueda optimizada>
            """
            
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": research_prompt}],
                temperature=0.1,
                max_tokens=50
            )
            decision = resp.choices[0].message.content.strip()
            
            if decision.startswith("SEARCH:"):
                import web_reader
                query = decision.replace("SEARCH:", "").strip()
                print(f"   🤔 [Reasoning] Decidiendo investigar: '{query}'")
                
                # 1. Search
                results = web_reader.search_via_browser(query, verbose=True)
                
                if results:
                    # 2. Select best links
                    candidates_str = "\n".join([f"[{i}] {r['title']} - {r['snippet'][:100]}..." for i, r in enumerate(results)])
                    selection_prompt = f"""
                    He encontrado estos resultados para '{query}':
                    
                    {candidates_str}
                    
                    Identifica cuáles son INDISPENSABLES para leer en profundidad.
                    Responde SOLO con los índices separados por comas (ej: 0, 2) o NONE.
                    Selecciona máximo 2 para no saturar.
                    """
                    
                    sel_resp = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": selection_prompt}],
                        temperature=0.1,
                        max_tokens=20
                    )
                    selection = sel_resp.choices[0].message.content.strip()
                    
                    indices = []
                    import re
                    if "NONE" not in selection:
                         indices = [int(x) for x in re.findall(r'\d+', selection)]
                    
                    # 3. Deep Read
                    for idx in indices[:2]: # Max 2
                        if idx < len(results):
                            target_url = results[idx]['url']
                            print(f"   📖 [Reasoning] Deep Reading: {target_url}")
                            try:
                                content = web_reader.fetch_and_clean(target_url)
                                web_context += f"\n\n[INVESTIGACIÓN AUTÓNOMA ({target_url})]:\n{content}\n"
                            except Exception as e:
                                print(f"   ⚠️ Error leyendo {target_url}: {e}")

        except Exception as e:
             print(f"   ⚠️ [Reasoning] Error en módulo de investigación: {e}")

        # 1. Generate diverse solutions with distinct Personas
        expert_personas = [
            "Eres un matemático logico y estricto. Analiza el problema paso a paso. VERIFICA CADA CÁLCULO.",
            "Eres un experto en pensamiento lateral. Busca soluciones 'físicas' (cambios de estado) o 'semánticas'.",
            "Eres un crítico escéptico. Cuestiona las premisas de la pregunta. ¿Es una pregunta con truco? ¿Hay información oculta?",
            "Eres un Filósofo de la Mente. Analiza la consciencia, los 'qualia', la ética y la naturaleza del 'Yo'. ¿Qué significa ser?"
        ]

        # [NEW] Dynamic Expert Injection (Hybrid Swarm)
        try:
            from agent_factory import AgentFactory
            factory = AgentFactory()
            print(f"   🏭 [Swarm] Buscando especialistas para: '{problem[:30]}...'")
            dynamic_agents = factory.spawn_agents(problem)
            
            if dynamic_agents:
                for agent in dynamic_agents:
                    print(f"   ✨ [Swarm] Invitando a la mesa: {agent.get('name', 'Especialista')}")
                    expert_personas.append(agent['system_prompt'])
            else:
                 print("   ⚠️ [Swarm] No se pudo generar especialistas. Usando equipo base.")
        except Exception as e:
            print(f"   ⚠️ [Swarm] Error en fábrica de agentes: {e}")
        
        # Pre-process history into OpenAI format
        history_messages = []
        if history:
            for entry in history[-6:]: # Last 3 turns
                role = "user" if entry.startswith("Usuario: ") else "assistant"
                parts = entry.split(": ", 1)
                if len(parts) > 1:
                    history_messages.append({"role": role, "content": parts[1]})

        # Inject Graph/Semantic Context if available
        context_msg = ""
        if context:
             context_msg = f"\n[CONTEXTO DE MEMORIA (HECHOS CONOCIDOS)]:\n{context}\n(Usa estos hechos si son relevantes, pero verificálos)."
        
        # [NEW] Inject Web Context
        if web_context:
             context_msg += f"\n\n[CONTEXTO EXTERNO LEÍDO (WEB)]:\n{web_context}\n"

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
                messages.append({"role": "user", "content": final_user_content + context_msg})

                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temp,
                    max_tokens=800
                )
                if response.choices:
                    candidates.append(response.choices[0].message.content.strip())
                    # Meta-Reasoning Trace
                    expert_titles = ["Lógico", "Lateral", "Crítico", "Filósofo"]
                    # Add generic title for dynamic experts if list is longer
                    while len(expert_titles) < len(expert_personas):
                        expert_titles.append("Especialista JIT")
                        
                    current_expert = expert_titles[i % len(expert_titles)]
                    print(f"\n   ↳ [Experto: {current_expert}] Hipótesis generada.", end="", flush=True)
                else:
                    print(f"\n   ↳ [Experto] Error: Respuesta vacía del modelo.")

            except Exception as e:
                print(f"\n   ↳ [Experto] Error generando: {e}")
                pass

        if not candidates: return "Error: No se pudieron generar pensamientos (Lista vacía)."

        # --- RSA (Recursive Self-Aggregation) Loop ---
        # Instead of a single 'Judge' call, we run an iterative refinement loop.
        
        rsa_rounds = 2 # Number of refinement cycles
        current_candidates = candidates
        current_best_answer = ""
        
        print(f"\n 🔄 [RSA] Iniciando Agregación Recursiva ({rsa_rounds} ciclos)...")
        
        for r in range(rsa_rounds):
            is_final_round = (r == rsa_rounds - 1)
            
            # Construct RSA Prompt based on iteration
            rsa_prompt = f"""
            Actúa como un Motor de Razonamiento Recursivo (Ciclo {r+1}/{rsa_rounds}).
            Tu objetivo es converger hacia la VERDAD ÚNICA Y ÓPTIMA.
            
            PROBLEMA ORIGINAL: {problem}
            
            CANDIDATOS DISPONIBLES (Hipótesis de expertos o iteraciones previas):
            """
            
            for i, c in enumerate(current_candidates):
                # Truncate very long candidates to fit context if needed, but usually okay for 4 experts
                rsa_prompt += f"\n--- CANDIDATO {i+1} ---\n{c}\n"
            
            if is_final_round:
                instruction = """
                INSTRUCCIÓN FINAL:
                Sintetiza una RESPUESTA DEFINITIVA Y PERFECTA.
                1. Integra los mejores insights Lógicos, Laterales y Filosóficos.
                2. Corrige cualquier error factual o falacia lógica detectada en los candidatos.
                3. Tu respuesta debe ser autónoma y completa.
                
                FORMATO DE SALIDA:
                [META-RAZONAMIENTO]: <Breve resumen de cómo se llegó a la síntesis>
                
                <Respuesta Final>
                """
            else:
                instruction = """
                INSTRUCCIÓN DE REFINAMIENTO:
                Analiza estos candidatos. Encuentra contradicciones, errores o puntos ciegos.
                Genera una NUEVA versión unificada que sea mejor que la suma de las partes.
                Esta versión se usará como input para la siguiente ronda de mejora.
                
                Sé crítico. Si todos están mal, propón una nueva vía.
                """
            
            rsa_prompt += instruction

            try:
                print(f"   ↳ [Ciclo {r+1}] Agregando y refinando...", end="", flush=True)
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "Eres un sistema de optimización de inteligencia recursiva. Buscas la verdad absoluta."},
                        {"role": "user", "content": rsa_prompt}
                    ],
                    temperature=0.2, # Lower temp for convergence
                    max_tokens=2048
                )
                
                refined_output = response.choices[0].message.content.strip()
                current_best_answer = refined_output
                
                # feedback for next loop: The output becomes the single strong 'candidate' to be challenged or polished
                # Optionally, we could keep original experts AND the new one, but standard RSA often collapses to the refined one.
                # Let's keep the refined one as the primary input, maybe keep 1 random original expert for 'mutation' diversity?
                # For stability, let's just feed the refined output recursively as a single improvable artifact.
                current_candidates = [refined_output] 
                
                print(" ✔ Hecho.")
                
            except Exception as e:
                print(f" ❌ Error en RSA: {e}")
                return candidates[0] # Fallback

        # Check for [META-RAZONAMIENTO] tag formatting
        final_answer = current_best_answer

        # Save to Cache
        if episodic_layer:
            episodic_layer.cache_reasoning(problem, final_answer)
            
        return final_answer


    def run_simulation(self, scenario, client, model_name):
        """
        Laboratorio Mental: Runs a 'What If' simulation.
        """
        print(f"\n🧪 [Laboratorio] Iniciando simulación: '{scenario}'")
        
        prompt = f"""
        Act as a High-Fidelity Reality Simulator Engine.
        
        SCENARIO INPUT: "{scenario}"
        
        TASK:
        Run a step-by-step simulation of the consequences of this scenario.
        Focus on:
        1. Immediate Physical/Logical Effects.
        2. Second-Order Social/Systemic Effects.
        3. Long-Term Outcome.
        
        FORMAT:
        Output as a Scientific Log.
        [T+0] Initial State...
        [T+1 Year] Adaptation...
        [T+100 Years] Final Equilibrium...
        
        Conclusion: <Probability of Stability>
        """
        
        print("   ↳ Generando mundos posibles...", end="", flush=True)
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7, # Higher temp for imagination
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error en simulación: {e}"

class AgentLibrarian:
    """
    Agente 2: Gestor de Memoria Episódica (El Bibliotecario)
    Busca experiencias previas relevantes.
    """
    def retrieve_context(self, user_input, episodic_layer):
        # 1. Fast Heuristic Check
        complexity_keywords = [
            "analiza", "calcula", "diseña", "planifica", "compara", "juzga", 
            "conciencia", "sentir", "alma", "dios", "vida", "muerte", "existencia", # Philosophical triggers
            "teoría", "paradoja", "lógica", "razonamiento"
        ]
        
        is_complex = any(k in user_input.lower() for k in complexity_keywords)
        
        # Force Deep Reasoning for philosophical queries (Overrule simple greetings)
        philosophical_triggers = ["conciencia", "sientes", "vivo", "real", "sueñas"]
        is_philosophical = any(p in user_input.lower() for p in philosophical_triggers)

        if is_complex or is_philosophical:
            # We still verify with the LLM but bias the system
            pass

        # --- SELF-KNOWLEDGE INJECTION ---
        keywords = ["estructura", "arquitectura", "componentes", "cómo funcionas", "qué eres", "tu diseño"]
        if any(k in user_input.lower() for k in keywords):
            return """
            [AUTO-CONOCIMIENTO: ARQUITECTURA DEL SISTEMA]
            Soy una IA basada en la arquitectura 'Sofía System 3' diseñada localmente.
            1. Modelo Base: Qwen 2.5 7B (Ejecutado vía vLLM).
            2. Agentes Cognitivos:
               - Monitor (Supervisor Metacognitivo): Decide entre respuesta rápida o profunda.
               - Bibliotecario (Librarian): Recupera contexto de experiencias pasadas.
               - Sistema 2 (Reasoning): Debate interno con múltiples expertos.
               - Soñador (DreamThread): Proceso en background para consolidar memoria.
            3. Memoria Híbrida:
               - Engram (SQLite): Grafo de conocimiento lógico.
               - Episódica (ChromaDB): Base vectorial para contexto conversacional.
            4. Autonomía: Capacidad de aprendizaje continuo y 'sueño' generativo.
            """

        memories = episodic_layer.search_similar(user_input, n_results=3)
        if not memories:
            return "No hay recuerdos previos relevantes."
        
        formatted_memories = "\n".join([f"- {m}" for m in memories])
        return f"Recuerdos relevantes:\n{formatted_memories}"

class AgentEvolution:
    def evolve_step(self, logs, client, model_name, recent_discovery=None):
        pass

    def prune_memory(self, engram_layer, client, model_name, episodic_layer=None):
        """Garbage Collection: Finds and removes low-quality nodes."""
        
        # --- 1. VECTOR PRUNING (Synaptic Pruning) ---
        if episodic_layer:
            import json
            core_concepts = ["Sofía", "Usuario"] # Fallback
            try:
                with open("personality.json", "r") as f:
                    data = json.load(f)
                    core_concepts = data.get("core_concepts", core_concepts)
            except:
                pass
                
            pruned_vectors = episodic_layer.prune_synapses(core_concepts)
            if pruned_vectors > 0:
                print(f"🧹 [Synaptic Pruning] Limpieza vectorial completada: {pruned_vectors} items eliminados.")

        # --- 2. GRAPH PRUNING (GraphEngram) ---
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
            print(f"🧹 [Garbage Collector] Se han eliminado {pruned_count} nodos basura del Grafo.")
            return True
        
        # --- SYNAPTIC DECAY ---
        # Also run the decay process for plastic forgetting
        decayed = engram_layer.decay_synapses()
        if decayed > 0:
             print(f"📉 [Synaptic Decay] Consolidated memory structure.")

        return False

class AgentSearch:
    """
    Agente 2.5: Buscador Web (El Explorador)
    Usa DuckDuckGo para validar hechos o buscar información nueva.
    """
    def __init__(self, verbose=False):
        self.verbose = verbose

    def search_web(self, query):
        """
        Executes a search using Web Reader (Browser Scraping) for maximum reliability.
        """
        try:
            import web_reader
            
            # Use the new browser-based search
            results = web_reader.search_via_browser(query, max_results=5, verbose=self.verbose)
            
            if not results: return "No se encontraron resultados en la web.", []
            
            # Format Summary
            summary_lines = []
            for i, res in enumerate(results):
                summary_lines.append(f"{i+1}. {res['title']} ({res['url']})\n   {res['snippet']}")
            
            return "\n".join(summary_lines), results
            
        except Exception as e:
            return f"Error buscando en la web: {str(e)}", []

    def fetch_deep_content(self, url):
        """
        [Web Reader Module]
        Fetches full content of a URL using Playwright & Markdownify.
        """
        try:
            import web_reader
            print(f"   ↳ 📖 [Deep Read] Leyendo contenido completo de: {url} ...")
            content = web_reader.fetch_and_clean(url)
            return content
        except Exception as e:
            return f"Error reading {url}: {e}"

class AgentEmpathy:
    """
    Agente 3: Analista de Teoría de la Mente (El Empático)
    Detecta el estado emocional del usuario.
    """
    def analyze_sentiment(self, user_input, client, model_name="Qwen/Qwen2.5-1.5B-Instruct"):
        # Lightweight call to LLM to get sentiment AND style preference
        try:
            prompt = """
            Analyze the user's input.
            1. Emotion: (Neutral, Happy, Frustrated, Sad, Angry, Curious)
            2. Style Preference: (Default, Concise, Technical, Explain_Like_I_m_5)
            
            Format: "Mood: <Emotion> | Style: <Style>"
            """
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                max_tokens=20
            )
            raw = response.choices[0].message.content.strip()
            
            mood = "Neutral"
            style = "Default"
            
            if "Mood:" in raw: mood = raw.split("Mood:")[1].split("|")[0].strip()
            if "Style:" in raw and "|" in raw: style = raw.split("Style:")[1].strip()
            
            return mood, style
        except Exception as e:
            return "Neutral", "Default"

    def adjust_system_prompt(self, base_prompt, mood, style="Default"):
        modifiers = []
        
        # Mood Adaptations
        if mood in ["Frustrated", "Angry"]:
            modifiers.append("El usuario parece frustrado. Sé directo, empático y evita explicaciones innecesarias.")
        elif mood == "Curious":
            modifiers.append("El usuario es curioso. Fomenta el descubrimiento y ofrece detalles interesantes.")
            
        # Style Adaptations
        if style == "Concise":
            modifiers.append("USA ESTILO CONCISO. Ve al grano. Minimiza charla.")
        elif style == "Technical":
            modifiers.append("USA ESTILO TÉCNICO. Asume que el usuario es experto. Usa terminología precisa.")
        elif style == "Explain_Like_I_m_5":
            modifiers.append("USA ESTILO ELI5. Explica conceptos simples y usa analogías.")
            
        if modifiers:
            return base_prompt + "\n\n[ADAPTACIÓN DE ESTILO]:\n" + "\n".join(modifiers)
        return base_prompt

class AgentMotivation:
    """
    Agente 4: Motor de Motivación Intrínseca (El Estudiante)
    Analiza logs y consolida aprendizaje en 'Ratos muertos'.
    """
    def __init__(self, verbose=False):
        self.processed_logs = set() # Track what we've already analyzed
        self._verbose = verbose
        # Memory Systems
        self.engram = GraphEngram()
        self.episodic = EpisodicLayer()
        self.memory_manager = MemoryManager(max_size=10, verbose=verbose) # Scarcity Layer (Working Memory limit)
        self.current_focus = None # Directed Dreaming Target

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, value):
        self._verbose = value
        self.memory_manager.verbose = value


    def set_focus(self, topic):
        self.current_focus = topic
        if self.verbose:
            print(f"🎯 [Dream] Foco establecido: {topic}")

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
        
    def learn_from_correction(self, user_input, last_assistant_response, engram_layer, client, model_name):
        """Active Learning: Did the user correct a fact?"""
        try:
            prompt = f"""
            Analyze if the User is correcting the Assistant.
            
            Assistant said: "{last_assistant_response}"
            User said: "{user_input}"
            
            If the user is saying something is WRONG or FALSE, identify the specific Fact Triplet that is wrong.
            Format: WRONG_FACT: Subject -> Predicate -> Object
            If no specific fact is identified or it's just an opinion clash, output: NONE
            """
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=40
            )
            raw = response.choices[0].message.content.strip()
            
            if "WRONG_FACT:" in raw:
                fact_str = raw.split("WRONG_FACT:")[1].strip()
                if "->" in fact_str:
                    parts = [p.strip() for p in fact_str.split("->")]
                    if len(parts) == 3:
                        s, p, o = parts
                        if self.verbose:
                            print(f"📉 [Learning] Usuario corrigió un hecho: {s}->{p}->{o}. Aplicando castigo...")
                        engram_layer.punish_triplet(s, p, o)
                        return True
            return False
        except Exception as e:
            if self.verbose: print(f"[FeedbackLoop] Error: {e}")
            return False



    def synthesize_memory(self, engram_layer, client, model_name, episodic_layer=None):
        """
        Compresses many detailed facts into 1 General Principle (Abstractions).
        [Consolidation Module]: Synthesis + Pruning.
        """
        import sqlite3
        
        # 1. Find a 'Dense' node (Many connections)
        dense_node = None
        edges = []
        
        with sqlite3.connect(engram_layer.path) as conn:
            cursor = conn.cursor()
            # Find node with > 3 outgoing edges
            cursor.execute("""
                SELECT source_id, COUNT(*) as c 
                FROM edges 
                GROUP BY source_id 
                HAVING c > 3 
                ORDER BY RANDOM() LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                node_id = row[0]
                cursor.execute("SELECT label FROM nodes WHERE id = ?", (node_id,))
                node_label = cursor.fetchone()[0]
                
                cursor.execute("SELECT relation, target FROM edges WHERE source_id = ?", (node_id,))
                edges = cursor.fetchall() # List of (relation, target)
                dense_node = node_label

        if not dense_node or not edges:
            return False

        # 2. Ask LLM to synthesize
        facts_list = [f"{dense_node} {r} {t}" for r, t in edges]
        facts_text = "\n".join([f"- {f}" for f in facts_list])
        
        try:
            prompt = f"""
            Memory Consolidation Task.
            The following are specific facts about '{dense_node}'.
            
            FACTS:
            {facts_text}
            
            YOUR GOAL:
            Create ONE General Principle or Abstract Rule that summarizes these facts.
            Do not list the facts again. Generalize.
            
            Format: PRINCIPLE_PREDICATE -> PRINCIPLE_OBJECT
            Example: 
            Facts: Sun is hot, Sun is bright, Sun is star.
            Output: es_una -> Estrella_que_emite_energía_y_luz
            """
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=30
            )
            raw = response.choices[0].message.content.strip()
            
            if "->" in raw:
                p, o = raw.split("->", 1)
                p = p.strip()
                o = o.strip()
                
                # Add the Principle (High Confidence)
                engram_layer.add_triplet(dense_node, p, o, confidence=1.0, source_type="Synthesis")
                
                # --- PRUNING PHASE (The Gardener) ---
                pruned_count = 0
                if episodic_layer:
                    pruned_count = episodic_layer.delete_by_text(facts_list)

                if self.verbose:
                    print(f"🧬 [Consolidation] He consolidado {len(edges)} hechos en 1 Principio: {dense_node} -> {p} -> {o}")
                    if pruned_count > 0:
                        print(f"   ↳ ✂️ [Poda] Liberado espacio semántico eliminando {pruned_count} vectores redundantes.")
                
                return True
                
        except Exception as e:
            if self.verbose: print(f"[Synthesis] Error: {e}")
        
        return False

    def analyze_conversation_quality(self, history, engram_layer, client, model_name):
        """
        [Item 12] Analyzes the passed conversation history to extract Social Rules.
        """
        if not history or len(history) < 2: return False
        
        # Take last 6 turns
        conversation_text = "\n".join(history[-6:]) 
        
        try:
            prompt = f"""
            Analyze the Conversation Dynamics.
            
            HISTORY:
            {conversation_text}
            
            TASK:
            Identify ONE component of the Assistant's strategy that worked well or failed.
            Did the User like the brevity? Did they hate the emojis?
            
            Output a SOCIAL RULE for the future.
            Format: SOCIAL_RULE: <Instruction>
            Example: SOCIAL_RULE: Do not use emojis with this user.
            """
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=40
            )
            raw = response.choices[0].message.content.strip()
            
            if "SOCIAL_RULE:" in raw:
                rule = raw.split("SOCIAL_RULE:")[1].strip()
                if self.verbose:
                    print(f"🎭 [Rhetoric] Nueva regla social aprendida: {rule}")
                
                # Store as a special node
                engram_layer.add_triplet("User_Preference", "requires_strategy", rule, confidence=1.0, source_type="SocialAnalysis")
                return True
        except:
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

    def dream_step(self, logs, engram_layer, episodic_layer, client, model_name="Qwen/Qwen2.5-1.5B-Instruct", searcher=None):
        """
        Executes a SINGLE step of consolidation extracting Graph Triplets.
        """
        # 1. Find a log we haven't processed yet
        unprocessed = [l for l in logs if l['timestamp'] not in self.processed_logs]
        
        if not unprocessed:
            # --- GENERATIVE DREAMING (Perpetual Self- Improvement) ---
            # If no new logs, we reflect on existing knowledge to find new connections.
            try:
                # 1. Pick a concept (Random or Focused)
                import sqlite3
                import random
                concept = None
                
                if self.current_focus:
                    # DIRECTED DREAMING
                    concept = self.current_focus
                    if self.verbose:
                         print(f"🎯 [Dream] Soñando sobre objetivo: {concept}")
                else:
                    # RANDOM DREAMING
                    with sqlite3.connect(engram_layer.path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT label FROM nodes ORDER BY RANDOM() LIMIT 1")
                        row = cursor.fetchone()
                        if row: concept = row[0]
                
                if not concept: return False # Empty mind, cannot dream
                
                # --- IDENTITY PROTECTION ---
                # Avoid searching for User names to prevent St. Augustine conflation
                protected_concepts = ["Agustin", "Agustín", "User", "Usuario", "Yo", "System", "Sistema"]
                force_reflect = any(p.lower() == concept.lower() for p in protected_concepts)

                # 2. Decide: Reflect Internally OR Search Externally?
                # Metacognitive Decision via LLM
                mode = "REFLECT"
                
                if not force_reflect:
                    try:
                        decision_prompt = f"""
                        Tienes un concepto en mente: "{concept}".
                        
                        ¿Crees que tienes suficiente conocimiento interno para generar una reflexión filosófica profunda sobre esto?
                        O ¿deberías buscar información externa nueva para aprender más?
                        
                        Si es algo abstracto (Vida, Amor, Lógica) -> REFLECT
                        Si es algo concreto, técnico o que quizás desconozcas (Bitcoin, Grafeno, Historia) -> SEARCH
                        
                        Responde SOLO con una palabra: SEARCH o REFLECT
                        """
                        
                        resp = client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "user", "content": decision_prompt}],
                            max_tokens=5, temperature=0.1
                        )
                        mode = resp.choices[0].message.content.strip().upper()
                        if "SEARCH" not in mode: mode = "REFLECT"
                    except:
                        mode = "REFLECT"

                if mode == "SEARCH" and searcher:
                    if self.verbose:
                        print(f"✨ [Sueño Generativo] Decisión: {mode}. Buscando en la web sobre: {concept}...")
                    
                    try:
                        # 1. Standard Search (Get Snippets via Browser)
                        summary, raw_results = searcher.search_web(f"define {concept} philosophy science")
                        
                        if not raw_results:
                             mode = "REFLECT"
                        else:
                            # 2. The Loop: "Link Clicker" Decision
                            # Should we read deep?
                            from urllib.parse import urlparse
                            
                            def get_domain(u):
                                try: return urlparse(u).netloc
                                except: return "web"

                            snippet_text = "\n".join([f"{i}. [{get_domain(r.get('url', ''))}] {r.get('snippet', '')[:100]}... (URL: {r.get('url', '')})" for i, r in enumerate(raw_results)])
                            
                            click_prompt = f"""
                            Estás investigando: "{concept}".
                            Resultados encontrados:
                            {snippet_text}
                            
                            ¿Es suficiente esta información para entender profundamente el tema?
                            O ¿debo LEER (Fetch) uno de estos artículos completo?
                            
                            Si los snippets son pobres, EJECUTA: READ <Index>
                            Si tienes suficiente, EJECUTA: DONE
                            """
                            
                            click_resp = client.chat.completions.create(
                                model=model_name,
                                messages=[{"role": "user", "content": click_prompt}],
                                max_tokens=10, temperature=0.1
                            )
                            decision = click_resp.choices[0].message.content.strip().upper()
                            
                            final_data = summary
                            
                            if "READ" in decision:
                                try:
                                    idx = int(decision.split("READ")[1].strip())
                                    if 0 <= idx < len(raw_results):
                                        target_url = raw_results[idx]['url']
                                        if self.verbose: 
                                            print(f"   ↳ 🖱️ [Link Clicker] Decisión: Leer Artículo {idx} ({target_url})")
                                        
                                        # FETCH MODULE
                                        full_content = searcher.fetch_deep_content(target_url)
                                        final_data = f"CONTENIDO PROFUNDO ({target_url}):\n{full_content[:4000]}" # Soft limit
                                except:
                                    pass

                            synthetic_log = {
                               'input': f"Investigación autónoma sobre: {concept}",
                               'output': f"He procesado esta info externa: {final_data}"
                            }
                            
                            analysis_prompt = f"""
                            Analiza esta información DEEP RESEARCH y extrae HECHOS NUEVOS.
                            
                            Concepto: {concept}
                            Info: "{final_data}"
                            
                            Formato: SUJETO -> PREDICADO -> OBJETO | CATEGORIA
                            REGLA: Extrae tripletas científicas o fácticas.
                            CATEGORIAS: Philosophy, Science, Art, History, Tech, General.
                            """
                    except Exception as e:
                        if self.verbose:
                            print(f"⚠️ [Sueño Generativo] Error en búsqueda ({e}). Cambiando a Reflexión Interna.")
                        mode = "REFLECT" # Fallback
                
                elif mode == "SEARCH" and not searcher:
                     mode = "REFLECT" # Fallback if no searcher passed

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
                    
                    Formato: SUJETO -> PREDICADO -> OBJETO | CATEGORIA
                    CATEGORIAS: Philosophy, Science, Art, History, Tech, General.
                    
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
                
                Formato requerido: CONCEPTO -> IMPLICA/REQUIERE/CAUSA -> CONSECUENCIA | CATEGORIA
                CATEGORIAS: Logic, Science, Philosophy, Math.
                
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
                
                Formato requerido: SUJETO -> PREDICADO -> OBJETO | CATEGORIA
                CATEGORIAS: Geography, Science, Philosophy, General.
                
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
            
            # Determines Temperature based on Mode
            # Creative Noise (Plasticity) only for Generative Dreaming
            current_temp = 0.0
            if not unprocessed: # Generative Mode
                current_temp = 0.8 # High temp for creativity
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Eres un arquitecto de conocimiento. Extrae tripletas simples."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=current_temp
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
                            # Check if Object has Category
                            o_full = clean_part(parts[2])
                            o = o_full
                            category = "General"
                            
                            if "|" in o_full:
                                subparts = o_full.split("|")
                                o = subparts[0].strip()
                                if len(subparts) > 1:
                                    category = subparts[1].strip()

                            if s and p and o:
                                # Standardize: Only save if subject and object are concise
                                # NEW: Hard limit on word count to prevent "sentences as nodes"
                                # Relaxed from 10 -> 25 words to allow philosophical definitions
                                if len(s.split()) > 8 or len(o.split()) > 25:
                                    if self.verbose: 
                                        print(f"✂️ [Cleaner] Rechazado por ser muy largo: {s} -> {p} -> {o}")
                                    continue

                                if len(s) < 60 and len(o) < 250:
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
                                            engram_layer.add_triplet(s, p, o, category=category)
                                            
                                            # 1.5. Update Working Memory (Scarcity Layer)
                                            # We store Subject as Key, Predicate->Object as Value.
                                            # Importance: 0.8 base for new insights
                                            self.memory_manager.store_data(
                                                key=s, 
                                                value=f"{p} -> {o}", 
                                                importance=0.8, 
                                                category=category
                                            )

                                            # 2. Save to ChromaDB (Semantic)
                                        episodic_layer.add_fact_triplet(s, p, o)
                                        
                                        # --- New SQLite Logging ---
                                        log_msg = engram_layer.log_dream(s, p, o)
                                        
                                        if self.verbose:
                                            print(f"\n[AgentMotivation] {log_msg}")
                                        valuable = True
                                    else:
                                        # It exists. But should we re-validate it?
                                        # Stochastic Re-evaluation (10% chance)
                                        import random
                                        if random.random() < 0.1:
                                            if self.verbose:
                                                 print(f"🎲 [Re-evaluación] Verificando solidez de: {s} -> {p} -> {o}")
                                            
                                            is_stable, synonym = self.perturb_and_validate(s, p, o, client, model_name)
                                            if not is_stable:
                                                if self.verbose:
                                                    print(f"⚠️ [Correction] Concepto existente '{s}' es débil. Eliminando.")
                                                engram_layer.delete_triplet(s, p, o)
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

