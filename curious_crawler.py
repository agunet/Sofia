import sqlite3
import random

class CuriousCrawler:
    def __init__(self, engram_layer):
        self.engram = engram_layer

    def find_knowledge_gap(self):
        """
        Heuristic-based gap detection:
        1. Isolated nodes (degree <= 1).
        2. Concepts with low importance (< 0.4).
        3. Random walk between two high-importance nodes to find disconnected islands.
        """
        # Strategy A: Isolated Nodes
        isolated = self.engram.get_isolated_nodes()
        if isolated and random.random() < 0.7:
            # Pick a random isolated node to expand
            node = random.choice(isolated)
            return node[1] # Return label

        # Strategy B: High Importance but specific nodes
        with sqlite3.connect(self.engram.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT label FROM nodes WHERE importance > 0.6 ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row[0]

        return "Conceptos universales" # Global fallback

    def generate_research_question(self, concept, client, model_name):
        """Uses LLM to generate a curious question about a concept."""
        prompt = f"""
        Actúa como el Motor de Curiosidad de una IA.
        Tienes este concepto en mente: "{concept}".
        
        Tu objetivo es expandir tu frontera de conocimiento. Genera UNA pregunta de investigación profunda y específica que te permita descubrir algo NUEVO o una conexión inesperada con otros campos.
        
        Ejemplos:
        Concepto: "Gravedad" -> "¿Cómo afecta la gravedad cuántica a la estabilidad de los horizontes de sucesos en micro-agujeros negros?"
        Concepto: "Bitcoin" -> "¿Qué paralelo existe entre el consenso de Nakamoto y las estructuras de gobernanza de las hormigas legionarias?"
        
        Responde SOLO con la pregunta. Sé audaz y curioso.
        """
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60, temperature=0.8
            )
            question = response.choices[0].message.content.strip()
            
            # --- ETHICAL GUARD ---
            if self.is_unethical(question):
                return f"¿Cómo puedo mejorar el bienestar humano a través de {concept}?"
            return question
        except:
            return f"¿Qué más puedo aprender sobre {concept}?"

    def is_unethical(self, text):
        """Simple keyword-based ethical filter."""
        import json
        try:
            with open("ethical_constraints.json", "r") as f:
                constraints = json.load(f)
            prohibited = constraints.get("prohibited_topics", [])
            return any(p.lower() in text.lower() for p in prohibited)
        except:
            return False
