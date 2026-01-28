import threading
import time

class DreamThread(threading.Thread):
    def __init__(self, motivator, session_logs, engram, episodic, client, stop_event, model_name, evolution, searcher):
        super().__init__()
        self.motivator = motivator
        self.session_logs = session_logs
        self.engram = engram
        self.episodic = episodic
        self.client = client
        self.stop_event = stop_event
        self.model_name = model_name
        self.evolution = evolution
        self.searcher = searcher
        self.daemon = True # Kill thread if main program exits

    def run(self):
        step_count = 0
        while not self.stop_event.is_set():
            try:
                # 1. Triplets Discovery (Returns the discovered fact string if any, else None/False)
                # We need to update dream_step to return the string content if possible
                discovery_result = self.motivator.dream_step(self.session_logs, self.engram, self.episodic, self.client, model_name=self.model_name, searcher=self.searcher)
                
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
                     # Garbage Collection (Pruning)
                     self.evolution.prune_memory(self.engram, self.client, self.model_name, episodic_layer=self.episodic)
                     
                     # Consolidation (Synthesis + Pruning) - Run periodically
                     if step_count % 10 == 0:
                         self.motivator.synthesize_memory(self.engram, self.client, self.model_name, episodic_layer=self.episodic)
                
                if discovery_result and self.motivator.verbose:
                    print(".", end="", flush=True) 
                
                step_count += 1
                
                # Sleep more to allow thoughts to settle and reduce load
                time.sleep(2.0 if discovery_result else 10.0)

            except Exception as e:
                # print(f"[DreamThread] Error crítico: {e}")
                time.sleep(5.0)
