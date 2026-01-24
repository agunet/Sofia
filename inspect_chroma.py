import chromadb
import os

try:
    client = chromadb.PersistentClient(path="./memory_db")
    coll = client.get_collection("episodic_memory")
    count = coll.count()
    print(f"--- ChromaDB Status ---")
    print(f"Total Memories: {count}")
    
    if count > 0:
        print("\n--- Last 3 Memories ---")
        # Peek returns a dict
        peek = coll.peek(limit=3) 
        # peek['documents'] is a list of strings
        # peek['metadatas'] is a list of dicts
        for i in range(len(peek['documents'])):
            meta = peek['metadatas'][i]
            doc = peek['documents'][i]
            print(f"[{meta.get('timestamp', '?')}] Type: {meta.get('type', '?')} | Content: {doc[:100]}...")
    else:
        print("Warning: Collection is empty.")

except Exception as e:
    print(f"Error inspecting Chroma: {e}")
