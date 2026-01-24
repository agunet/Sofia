import os
import time
from openai import OpenAI
from memory_systems import GraphEngram, EpisodicLayer
from agents import AgentCheck, AgentLibrarian, AgentEmpathy, AgentMotivation, AgentEvolution, AgentReasoning, AgentSearch

# Configuration
VLLM_URL = "http://localhost:8085/v1"
API_KEY = "vllm"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
VALIDATE_OUTPUT = True # Inverse Flow (Pre-Validation)

import threading
import sys
from dream_engine import DreamThread

# --- Colors ---

# --- Colors ---
class C:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def main():
    print(f"{C.HEADER}--- INICIANDO SISTEMA SOFÍA (SISTEMA 3) ---{C.ENDC}")
    
    # 1. Initialize Infrastructure
    try:
        client = OpenAI(base_url=VLLM_URL, api_key=API_KEY, timeout=120.0)
        # Test connection
        print(f"{C.OKBLUE}[System] Conectando a vLLM (Local)...{C.ENDC}")
        client.models.list()
        print(f"{C.OKBLUE}[System] Conexión establecida con vLLM.{C.ENDC}")
    except Exception as e:
        print(f"{C.FAIL}[System] ERROR: No se puede conectar a vLLM.{C.ENDC}")
        print(f"{C.FAIL}Ejecuta './start_vllm.sh' en otra terminal primero.{C.ENDC}")
        return

    engram = GraphEngram()
    episodic = EpisodicLayer()
    
    # 2. Initialize Agents
    monitor = AgentCheck()
    librarian = AgentLibrarian()
    empath = AgentEmpathy()
    motivator = AgentMotivation(verbose=True) # Verbose ON by default
    searcher = AgentSearch()
    evolution = AgentEvolution()
    
    # 2.5 Genesis Check (Seed Memory if empty)
    import sqlite3
    with sqlite3.connect(engram.path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM nodes")
        count = cursor.fetchone()[0]
        if count == 0:
            print(f"{C.OKCYAN}[System] 🧠 Cerebro vacío detectado. Inyectando Memorias Génesis...{C.ENDC}")
            seeds = [
                ("Sofía", "es_una", "Inteligencia_Artificial_Avanzada"),
                ("Agustin", "es_el", "Creador_del_Sistema"),
                ("Mundo", "contiene", "Conocimiento_Infinito"),
                ("Sueño", "sirve_para", "Consolidar_Información")
            ]
            for s, r, t in seeds:
                engram.add_triplet(s, r, t, confidence=1.0, source_type="Genesis")
            print(f"{C.OKGREEN}[System] ✔ Génesis completado. Sueño habilitado.{C.ENDC}")
    
    # 3. Ingest existing dreams (Manual or Previous)
    restored_count = motivator.ingest_from_log_file("dreams.log", engram, episodic)
    if restored_count > 0:
        print(f"{C.OKBLUE}[Memory] Se han integrado {restored_count} sueños previos desde dreams.log.{C.ENDC}")

    session_logs = []
    session_history = []

    print(f"\n{C.HEADER}--- INICIO DEL BUCLE DE PENSAMIENTO ---{C.ENDC}")
    print(f"{C.OKCYAN}Escribe 'salir' para terminar.{C.ENDC}")
    print(f"{C.OKCYAN}(El sistema 'soñará' automáticamente en background y logueará en dreams.log){C.ENDC}")
    
    stop_dreaming = threading.Event()
    
    while True:
        try:
            # --- REMOTE CONTROL INTERRUPT ---
            # Check if Dashboard sent a command
            remote_cmd = engram.pop_command()
            
            # --- START DREAMING (When waiting for user) ---
            stop_dreaming.clear()
            dreamer = DreamThread(motivator, session_logs, engram, episodic, client, stop_dreaming, model_name=MODEL_NAME, evolution=evolution)
            dreamer.start()

            if remote_cmd:
                print(f"\n{C.OKCYAN}📡 [Remoto] Ejecutando comando: {remote_cmd}{C.ENDC}")
                user_input = remote_cmd
            else:
                # BLOCKS here until user hits Enter
                user_input = input(f"\n{C.OKGREEN}Usuario: {C.ENDC}")
            
            # --- STOP DREAMING (Immediately) ---
            stop_dreaming.set()
            dreamer.join(timeout=1.0) # Wait max 1s for thread to finish its current step

            if user_input.lower() in ['salir', 'exit']:
                break
            
            if user_input.lower() in ['log', 'logs']:
                motivator.verbose = not motivator.verbose
                status = "ACTIVADOS (Pantalla)" if motivator.verbose else "DESACTIVADOS (Solo Archivo)"
                print(f"{C.OKBLUE}[System] Logs de sueño {status}{C.ENDC}")
                continue

            # COMMAND: Directed Dreaming Focus
            if user_input.lower().startswith("/focus "):
                topic = user_input[7:].strip()
                motivator.set_focus(topic)
                print(f"{C.OKCYAN}🎯 [Sistema] Foco de sueño establecido en: '{topic}'{C.ENDC}")
                continue

            # COMMAND: Force Synthesis
            if user_input.lower() == "/synthesize":
                print(f"{C.OKBLUE}🧬 [Sistema] Iniciando síntesis de memoria...{C.ENDC}")
                success = motivator.synthesize_memory(engram, client, MODEL_NAME)
                if not success:
                    print("   (No se encontraron nodos densos para sintetizar)")
                continue

            # COMMAND: Mental Lab
            if user_input.lower().startswith("/simulate "):
                scenario = user_input[10:].strip()
                reasoner = AgentReasoning() # Initialize on demand
                result = reasoner.run_simulation(scenario, client, MODEL_NAME)
                print(f"\n{C.OKGREEN}🔬 [Resultado de Simulación]:{C.ENDC}")
                print(result)
                
                # Verify stability (AgentCheck isn't needed here, it's imagination)
                # Store in Episodic as "Experiment"
                episodic.add_episode(f"/simulate {scenario}", result, context="Simulation")
                continue

            # --- PHASE 1: Parsing & Hashing (Agent 1: Monitor) ---
            # Initialize context variables early to avoid UnboundLocalError
            graph_context = None
            context_memories = ""
            mood = "Neutral"
            
            # 1. Check if we need Deep Reasoning (System 2)
            decision = monitor.decision_gate(user_input, client, MODEL_NAME, history=session_history)
            
            # --- PHASE 0: Feedback Loop (Correction Detection) ---
            correction_triggers = ["incorrecto", "mentira", "te equivocas", "falso", "error", "no es cierto", "mal"]
            is_correction = any(t in user_input.lower() for t in correction_triggers)
            
            if is_correction and session_history:
                # Find last assistant message
                last_response = [x for x in session_history if x.startswith("Sofía:")]
                if last_response:
                    last_response = last_response[-1].replace("Sofía: ", "")
                    # Trigger Active Learning
                    print(f"{C.WARNING}[Feedback Loop] Detectada posible corrección. Analizando error...{C.ENDC}")
                    motivator.learn_from_correction(user_input, last_response, engram, client, MODEL_NAME)
                    # Also analyze Strategy (Item 12)
                    motivator.analyze_conversation_quality(session_history, engram, client, MODEL_NAME)

            answer = "" # Prepare variable
            
            if decision["action"] == "deep_think":
                print(f"{C.WARNING}[Monitor] Complejidad detectada. Activando Sistema 2...{C.ENDC}")
                reasoner = AgentReasoning() # Initialize on demand or keep persistent
                # Execute Voting with History Context AND Cache
                answer = reasoner.solve_with_voting(user_input, client, MODEL_NAME, episodic_layer=episodic, n_attempts=3, history=session_history)
                print(f"\n{C.OKGREEN}✔ Conclusión Alcanzada.{C.ENDC}")
                
                # Print result immediately as it is already fully formed
                print(f"{C.BOLD}Sofía (Pensamiento Profundo): {C.ENDC}{answer}")
                print(f"{C.ENDC}")
            
            elif decision["action"] == "search_web":
                print(f"{C.OKCYAN}[Monitor] Información externa necesaria. Buscando en la web...{C.ENDC}")
                try:
                    search_results = searcher.search_web(user_input)
                    print(f"{C.OKBLUE}✔ Datos encontrados.{C.ENDC}")
                    graph_context = search_results # Override graph context with fresh web data
                except Exception as e:
                    print(f"{C.FAIL}[Search] Error: {e}{C.ENDC}")

            else:
                # --- FAST PATH (System 1) ---
                
                # GraphEngram provides context, not just simple hits
                graph_context = engram.get_context(user_input)
                
                if graph_context:
                    print(f"{C.BOLD}[Graph Memory] Contexto encontrado:\n{graph_context}{C.ENDC}")
                
                # --- PHASE 2: Context Retrieval (Agent 2: Librarian) ---
                context_memories = librarian.retrieve_context(user_input, episodic)
            
            # Only run standard generation if System 2 didn't already answer
            if not answer:
                # --- PHASE 3: Empathy Analysis (Agent 3: Empathetic) ---
                mood, style = empath.analyze_sentiment(user_input, client, model_name=MODEL_NAME)
                if mood != "Neutral" or style != "Default":
                    print(f"{C.WARNING}[Internal] Estado: {mood} | Estilo Preferido: {style}{C.ENDC}")

                # --- PHASE 4: Generation (The Model) ---
                base_system_prompt = evolution.get_current_instruction()
                adjusted_system_prompt = empath.adjust_system_prompt(base_system_prompt, mood, style)
                
                full_context = ""
                if graph_context:
                    full_context += f"INFORMACIÓN GRAFO (Hechos Confirmados):\n{graph_context}\n\n"
                full_context += f"MEMORIA EPISÓDICA (Experiencias):\n{context_memories}"

                # Construir mensajes con historial
                messages = [{"role": "system", "content": adjusted_system_prompt}]
                # Agregar últimos 6 mensajes del historial (3 turnos)
                for entry in session_history[-6:]:
                    role = "user" if entry.startswith("Usuario: ") else "assistant"
                    content = entry.split(": ", 1)[1]
                    messages.append({"role": role, "content": content})
                
                # Agregar contexto y mensaje actual
                messages.append({"role": "user", "content": f"Contexto:\n{full_context}\n\nPregunta: {user_input}"})

                print(f"{C.BOLD}Sofía: ", end="", flush=True)
                
                stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=0.7,
                    stream=True
                )
            
                answer = ""
                is_thinking = False
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        
                        # Filtering <think> tags (typical in some models like DeepSeek)
                        if "<think>" in content:
                            is_thinking = True
                            content = content.replace("<think>", "")
                        
                        if "</think>" in content:
                            is_thinking = False
                            content = content.replace("</think>", "")
                            continue # Skip the line break usually associated
                        
                        if not is_thinking and content:
                            print(content, end="", flush=True)
                            answer += content
                
                print(f"{C.ENDC}") # Reset color and new line
            
            # --- PHASE 4.5: Pre-Validation (Inverse Flow) ---
            if VALIDATE_OUTPUT and answer:
                # Combine contexts for validation
                validator_context = ""
                if graph_context: validator_context += f"Hechos: {graph_context}\n"
                if context_memories: validator_context += f"Memorias: {context_memories}\n"

                is_safe, critique, score = monitor.validate_response(user_input, answer, client, MODEL_NAME, context=validator_context)
                
                # Feedback loop log
                if score < 9.0:
                    if score >= 7.0:
                         print(f"\n{C.OKGREEN}✅ [Auto-Juez] Aprobado (Score: {score}).{C.ENDC}")
                
                if not is_safe:
                    print(f"\n{C.FAIL}🛑 [Auto-Juez] Bloqueado (Score: {score}/10).{C.ENDC}")
                    print(f"{C.FAIL}Critica: {critique}{C.ENDC}")
                    print(f"{C.WARNING}⟳ Regenerando con corrección...{C.ENDC}")
                    
                    # Retry once with critique
                    retry_prompt = f"Tu respuesta anterior fue RECHAZADA por: {critique}. Responde de nuevo al usuario corrigiendo esto.\nPregunta: {user_input}"
                    
                    retry_resp = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[{"role": "user", "content": retry_prompt}]
                    )
                    answer = retry_resp.choices[0].message.content.strip()
                    print(f"{C.BOLD}Sofía (Corregida): {C.ENDC}{answer}")

            # --- Update History ---
            session_history.append(f"Usuario: {user_input}")
            session_history.append(f"Sofía: {answer}")

            # --- PHASE 5: Storage (Episodic Memory) ---
            episodic.add_episode(user_input, answer, context=mood)
            
            # Inline Fact Extraction (Analyze now!)
            did_extract = motivator.quick_analyze(user_input, answer, engram, episodic, client, MODEL_NAME)
            if did_extract and motivator.verbose:
                print(f"{C.OKBLUE}[Memory] Hecho extraído e integrado.{C.ENDC}")

            # Log for the Motivation Agent (Background dreaming)
            # Log for the Motivation Agent (Background dreaming)
            # Determine log type based on who answered
            log_type = "reasoning" if decision["action"] == "deep_think" else "interaction"
            
            session_logs.append({
                "input": user_input,
                "output": answer,
                "timestamp": time.time(),
                "type": log_type
            })

        except KeyboardInterrupt:
            stop_dreaming.set()
            break
        except Exception as e:
            msg = str(e)
            if "No models loaded" in msg:
                print(f"{C.FAIL}\n[System] ERROR: No hay modelos cargados en LM Studio. Por favor, carga uno.{C.ENDC}")
            else:
                print(f"{C.FAIL}\nError en el bucle: {e}{C.ENDC}")
            stop_dreaming.set()

    print("Sistema detenido.")

if __name__ == "__main__":
    main()
