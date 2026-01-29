import threading
import time
import json
import random
from reward_system import RewardSystem
from curious_crawler import CuriousCrawler

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
        self.reward_system = RewardSystem()
        self.crawler = CuriousCrawler(engram)
        self.daemon = True

    def run(self):
        step_count = 0
        while not self.stop_event.is_set():
            try:
                # 0. Evaluate Drives & Objectives
                drives = {}
                objectives = {}
                try:
                    with open("drives.json", "r") as f:
                        drives = json.load(f)
                    with open("objectives.json", "r") as f:
                        objectives = json.load(f)
                except:
                    drives = {"curiosity": 0.5, "depth_over_breadth": 0.5}
                    objectives = {"exploration_boundaries": [], "avoid_topics": []}

                curiosity = drives.get("curiosity", 0.5)
                depth_drive = drives.get("depth_over_breadth", 0.5)
                
                # 1. Decide: Process Logs OR Autonomous Action?
                unprocessed = [l for l in self.session_logs if l['timestamp'] not in self.motivator.processed_logs]
                
                # If curiosity is high (> 0.7) and no critical logs, maybe go into Autonomous Mode
                autonomous_mode = (curiosity > 0.6 and random.random() < 0.4) or (not unprocessed and curiosity > 0.3)
                
                discovery_status = False

                if autonomous_mode and self.searcher:
                    # --- PROJECT GENESIS: AUTONOMOUS RESEARCH ---
                    gap_concept = self.crawler.find_knowledge_gap()
                    
                    boundaries = objectives.get("exploration_boundaries", [])
                    avoid = objectives.get("avoid_topics", [])
                    
                    # --- [FILTER DEBUG] ---
                    has_match = any(b.lower() in gap_concept.lower() for b in boundaries)
                    if self.motivator.verbose:
                        print(f"   [FILTER DEBUG] Investigating: '{gap_concept}' | Boundaries: {len(boundaries)} keywords")
                        if has_match:
                            print(f"   [FILTER DEBUG] Match found: {[b for b in boundaries if b.lower() in gap_concept.lower()]}")
                    
                    if boundaries and not has_match:
                        # STOCHASTIC FILTERING: 20% chance to jump outside bounds (Creative Leap)
                        if random.random() > 0.2:
                            if self.motivator.verbose:
                                print(f"   🚫 [Génesis] Concepto '{gap_concept}' fuera de límites. Buscando otro...")
                            gap_concept = self.crawler.find_knowledge_gap()
                        else:
                            if self.motivator.verbose:
                                print(f"   ✨ [Génesis] ¡Salto creativo! Investigando tema fuera de límites: '{gap_concept}'")

                    question = self.crawler.generate_research_question(gap_concept, self.client, self.model_name)
                    
                    if self.motivator.verbose:
                        print(f"\n🧠 [Génesis] Impulso de Curiosidad ({curiosity:.2f}). Investigando: '{question}'")
                    
                    # Perform search and internal integration
                    synthetic_log = {
                        "input": f"Internal Curiosity: {question}",
                        "output": f"Thinking about {gap_concept}...",
                        "timestamp": time.time(),
                        "type": "reasoning"
                    }
                    
                    self.motivator.set_focus(gap_concept)
                    discovery_status = self.motivator.dream_step([synthetic_log], self.engram, self.episodic, self.client, model_name=self.model_name, searcher=self.searcher)
                    self.motivator.set_focus(None) # Clear focus

                    # Calculate reward with Novelty and Depth
                    # For now, we "mock" depth if the topic relates to previous focus
                    novelty = 0.8 if discovery_status else 0.2
                    depth = 0.7 if depth_drive > 0.6 and discovery_status else 0.4
                    
                    reward = self.reward_system.calculate_reward(1 if discovery_status else 0, novelty, 0.75, depth_score=depth)
                    self.reward_system.update_drives(reward, action_type="research", depth_reached=(depth > 0.6))
                    
                    if self.motivator.verbose:
                        print(f"   ↳ [Génesis] Recompensa interna: {reward}")

                    # Achievements Log
                    if reward > objectives.get("achievements_threshold", 0.85):
                        with open("achievements.log", "a", encoding="utf-8") as f:
                            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🌟 BREAKTHROUGH: {gap_concept} -> {question} (Reward: {reward})\n")
                        if self.motivator.verbose:
                            print(f"   🌟 [Logro] ¡Sofía ha alcanzado un hito importante en su investigación!")

                else:
                    # Standard Triplets Discovery
                    discovery_status = self.motivator.dream_step(self.session_logs, self.engram, self.episodic, self.client, model_name=self.model_name, searcher=self.searcher)
                
                # 2. Immediate Evolution if something was learned
                if discovery_status:
                     self.evolution.evolve_step(self.session_logs, self.client, model_name=self.model_name, recent_discovery="Hechos nuevos integrados en memoria.")
                
                # 3. Periodic Evolution (Maintenance)
                elif step_count % 5 == 0:
                     self.evolution.evolve_step(self.session_logs, self.client, model_name=self.model_name)
                     self.evolution.prune_memory(self.engram, self.client, self.model_name, episodic_layer=self.episodic)
                     
                     if step_count % 10 == 0:
                         self.motivator.synthesize_memory(self.engram, self.client, self.model_name, episodic_layer=self.episodic)
                
                step_count += 1
                
                # Adaptive Sleeping
                if discovery_status:
                    sleep_time = 3.0
                else:
                    sleep_time = min(60.0, 10.0 + (step_count % 5) * 5.0)
                
                time.sleep(sleep_time)

            except Exception as e:
                if self.motivator.verbose:
                    print(f"⚠️ [DreamThread] Error: {e}")
                time.sleep(5.0)
