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

    def spawn_agent(self, user_query):
        """
        Generates a new agent specialized for the user's query.
        Returns the agent dict directly (Ephemeral).
        """
        print(f"✨ [Factory] Spawning ephemeral agent for: '{user_query}'...")
        
        architect_prompt = f"""
        You are the Architect of the Swarm. Create a specialized persona to answer the user's request.
        
        User Request: "{user_query}"
        
        Return ONLY a JSON object with this format:
        {{
            "id": "short_unique_id",
            "name": "Agent Name",
            "system_prompt": "You are [Role]. Your personality is [Adjective]. You focus on [Topic]..."
        }}
        """
        
        try:
            response = self.llm.invoke([SystemMessage(content="You are a JSON factory."), HumanMessage(content=architect_prompt)])
            raw_json = response.content.strip()
            
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:-3]
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:-3]
                
            new_agent = json.loads(raw_json)
            
            if "system_prompt" in new_agent:
                print(f"   ↳ Created: {new_agent.get('name', 'Unknown Agent')}")
                return new_agent
            return None

        except Exception as e:
            print(f"❌ [Factory] Error spawning agent: {e}")
            return None

if __name__ == "__main__":
    # Test
    factory = AgentFactory()
    print(factory.spawn_agent("I need a recipe for vegan lasagna"))
