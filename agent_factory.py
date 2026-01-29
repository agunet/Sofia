import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# --- CONFIG ---
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct" 
API_BASE = "http://localhost:8085/v1"
API_KEY = "EMPTY"

class AgentFactory:
    def __init__(self):
        self.llm = ChatOpenAI(model=MODEL_NAME, openai_api_base=API_BASE, openai_api_key=API_KEY, temperature=0.8)

    def spawn_agents(self, user_query, max_agents=3):
        """
        Generates a list of new agents specialized for the user's query.
        Returns a list of agent dicts.
        """
        architect_prompt = f"""
        You are the Architect of the Swarm. Analyze the User Request and decide which specialized personas are needed to solve it perfectly.
        
        CRITICAL: Each agent must represent a DISTINCT School of Thought, Paradigm, or Perspective (e.g. Scientific vs Ethical, Analytic vs Continental, Pragmatic vs Theoretical). Avoid duplicates.
        
        User Request: "{user_query}"
        
        Create 1 to {max_agents} agents.
        Return ONLY a JSON list of objects with this format:
        [
            {{
                "id": "unique_id_1",
                "name": "Agent Name 1",
                "system_prompt": "You are [Role]. Your personality is [Adjective]. You focus on [Topic]..."
            }},
            ...
        ]
        """
        
        try:
            response = self.llm.invoke([SystemMessage(content="You are a JSON factory."), HumanMessage(content=architect_prompt)])
            raw_json = response.content.strip()
            
            import re
            # Extract JSON list (find first [ and last ])
            match = re.search(r'\[.*\]', raw_json, re.DOTALL)
            if match:
                raw_json = match.group(0)
                
            new_agents = json.loads(raw_json)
            
            if isinstance(new_agents, list):
                print(f"   ↳ Created {len(new_agents)} agents: {[a.get('name') for a in new_agents]}")
                return new_agents
            else:
                # Fallback if single object returned
                return [new_agents]

        except Exception as e:
            print(f"❌ [Factory] Error spawning agents: {e}")
            return []

if __name__ == "__main__":
    # Test
    factory = AgentFactory()
    print(factory.spawn_agents("I need a recipe for vegan lasagna"))
