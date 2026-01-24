import os
import time
from openai import OpenAI
from memory_systems import GraphEngram, EpisodicLayer
from agents import AgentCheck, AgentLibrarian, AgentEmpathy, AgentMotivation, AgentEvolution, AgentReasoning, AgentSearch

# Configuration
VLLM_URL = "http://localhost:8085/v1"
API_KEY = "vllm"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

import threading
import sys

# --- Threading Logic ---
class DreamThread(threading.Thread):
    def __init__(self, motivator, session_logs, engram, episodic, client, stop_event, model_name, evolution):
        super().__init__()
        self.motivator = motivator
        self.session_logs = session_logs
        self.engram = engram
        self.episodic = episodic
        self.client = client
        self.stop_event = stop_event
        self.model_name = model_name
        self.evolution = evolution
        self.daemon = True # Kill thread if main program exits

    def run(self):
        step_count = 0
        while not self.stop_event.is_set():
            try:
                # 1. Triplets Discovery (Returns the discovered fact string if any, else None/False)
                # We need to update dream_step to return the string content if possible
                discovery_result = self.motivator.dream_step(self.session_logs, self.engram, self.episodic, self.client, model_name=self.model_name)
                
                # 2. Immediate Evolution if something was learned
                if discovery_result:
                     # discovery_result is currently True/False. 
                     # Ideally we'd pass the actual string, but for now we pass None or rely on logs check.
                     # Let's assume for this step we just trigger it.
                     evolved = self.evolution.evolve_step(self.session_logs, self.client, model_name=self.model_name, recent_discovery="Hechos nuevos integrados en memoria.")
                     if evolved and self.motivator.verbose:
                        print(f"\n[System] 🌱 Sofía ha evolucionado basada en aprendizaje reciente.")
                
                # 3. Periodic Evolution (Maintenance)
                elif step_count % 5 == 0:
                     evolved = self.evolution.evolve_step(self.session_logs, self.client, model_name=self.model_name)
                
                if discovery_result and self.motivator.verbose:
                    print(".", end="", flush=True) 
                
                step_count += 1
                
                # Sleep more to allow thoughts to settle and reduce load
                time.sleep(2.0 if discovery_result else 10.0)

            except Exception as e:
                # print(f"[DreamThread] Error crítico: {e}")
                time.sleep(5.0)

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
    motivator = AgentMotivation(verbose=False) # Silent by default
    searcher = AgentSearch()
    evolution = AgentEvolution()
    
    # 3. Ingest existing dreams (Manual or Previous)
    restored_count = motivator.ingest_from_log_file("dreams.log", engram, episodic)
    if restored_count > 0:
        print(f"{C.OKBLUE}[Memory] Se han integrado {restored_count} sueños previos desde dreams.log.{C.ENDC}")

    session_logs = []

    print(f"\n{C.HEADER}--- INICIO DEL BUCLE DE PENSAMIENTO ---{C.ENDC}")
    print(f"{C.OKCYAN}Escribe 'salir' para terminar.{C.ENDC}")
    print(f"{C.OKCYAN}(El sistema 'soñará' automáticamente en background y logueará en dreams.log){C.ENDC}")
    
    stop_dreaming = threading.Event()
    
    while True:
        try:
            # --- START DREAMING (When waiting for user) ---
            stop_dreaming.clear()
            dreamer = DreamThread(motivator, session_logs, engram, episodic, client, stop_dreaming, model_name=MODEL_NAME, evolution=evolution)
            dreamer.start()

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

            # --- PHASE 1: Parsing & Hashing (Agent 1: Monitor) ---
            # Initialize context variables early to avoid UnboundLocalError
            graph_context = None
            context_memories = ""
            mood = "Neutral"
            
            # 1. Check if we need Deep Reasoning (System 2)
            decision = monitor.decision_gate(user_input, client, MODEL_NAME)
            
            answer = "" # Prepare variable
            
            if decision["action"] == "deep_think":
                print(f"{C.WARNING}[Monitor] Complejidad detectada. Activando Sistema 2...{C.ENDC}")
                reasoner = AgentReasoning() # Initialize on demand or keep persistent
                # Execute Voting
                answer = reasoner.solve_with_voting(user_input, client, MODEL_NAME, n_attempts=3)
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
                mood = empath.analyze_sentiment(user_input, client, model_name=MODEL_NAME)
                if mood != "Neutral":
                    print(f"{C.WARNING}[Internal] Usuario parece: {mood}{C.ENDC}")

                # --- PHASE 4: Generation (The Model) ---
                base_system_prompt = evolution.get_current_instruction()
                adjusted_system_prompt = empath.adjust_system_prompt(base_system_prompt, mood)
                
                full_context = ""
                if graph_context:
                    full_context += f"INFORMACIÓN GRAFO (Hechos Confirmados):\n{graph_context}\n\n"
                full_context += f"MEMORIA EPISÓDICA (Experiencias):\n{context_memories}"

                print(f"{C.BOLD}Sofía: ", end="", flush=True)
                
                stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": adjusted_system_prompt},
                        {"role": "user", "content": f"Contexto:\n{full_context}\n\nPregunta: {user_input}"}
                    ],
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
