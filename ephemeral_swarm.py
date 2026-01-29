from agent_factory import AgentFactory
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from memory_systems import GraphEngram

# --- CONFIG ---
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
API_BASE = "http://localhost:8085/v1"
API_KEY = "EMPTY"

def main():
    print("✨ [Ephemeral Swarm] System Online (Transient Mode)")
    print("   Every request spawns a fresh agent. Nothing is saved.")
    
    # 1. Initialize Factory (Stateless)
    factory = AgentFactory()
    
    # 2. Connect to Memory (Read-Only Context)
    engram = GraphEngram()
    
    # 3. LLM for Execution
    executor_llm = ChatOpenAI(model=MODEL_NAME, openai_api_base=API_BASE, openai_api_key=API_KEY, temperature=0.7)
    
    while True:
        user_input = input("\nUsuario: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        print("⚡ [Swarm] Generating tailored agent...")
        
        # A. SPAWN (Just-In-Time)
        agent_config = factory.spawn_agent(user_input)
        
        if not agent_config:
            print("❌ Failed to spawn agent. Using General fallabck.")
            agent_config = {"name": "General", "system_prompt": "You are a helpful AI."}
            
        print(f"   ↳ Active Persona: {agent_config.get('name')}")
        
        # B. CONTEXT INJECTION
        context_str = ""
        try:
            ctx = engram.get_context(user_input, depth=1)
            if ctx:
                context_str = f"\n[MEMORIA COMPARTIDA]:\n{ctx}\n"
        except Exception:
            pass # Ignore memory errors for now
            
        # C. EXECUTION
        final_system_prompt = agent_config["system_prompt"] + "\n" + context_str
        
        messages = [
            SystemMessage(content=final_system_prompt),
            HumanMessage(content=user_input)
        ]
        
        try:
            print("   ↳ Executing...")
            response = executor_llm.invoke(messages)
            print(f"\n[{agent_config.get('name')}]: {response.content}")
        except Exception as e:
            print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    main()
