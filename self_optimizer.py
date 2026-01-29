import sqlite3
import datetime

class SelfOptimizer:
    def __init__(self, engram_layer):
        self.engram = engram_layer

    def prune_weak_connections(self, threshold=0.2):
        """Removes edges with confidence below threshold."""
        with sqlite3.connect(self.engram.path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM edges WHERE confidence < ?", (threshold,))
            changes = conn.total_changes
            conn.commit()
            return changes

    def create_abstractions(self, client, model_name):
        """Finds groups of related nodes and creates a 'Parent' concept."""
        # This is a complex logic that usually requires finding cliques or high-density clusters.
        # For MVP, we look for nodes sharing the same category.
        with sqlite3.connect(self.engram.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, COUNT(*) as count FROM nodes GROUP BY category HAVING count > 8")
            to_abstract = cursor.fetchall()
            
            abstractions_created = []
            for category, count in to_abstract:
                if category == "General" or not category: continue
                
                # Ask LLM for a refined abstraction label
                prompt = f"Tengo {count} conceptos en la categoría '{category}'. Sugiere un nombre único y técnico para un 'Nodo Padre' que los englobe a todos (ej: Felidae para gatos, tigres, etc). Responde solo con el nombre."
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=20
                    )
                    parent_label = response.choices[0].message.content.strip()
                    
                    # Create the parent node
                    self.engram.add_triplet(parent_label, "es_abstraccion_de", category, source_type="Self-Optimization")
                    abstractions_created.append(parent_label)
                except:
                    continue
            return abstractions_created

    def log_growth(self, filename="growth_log.md", event_type="Optimization", description=""):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"- [{timestamp}] **{event_type}**: {description}\n")
