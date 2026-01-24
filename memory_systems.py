import hashlib
import chromadb
from chromadb.utils import embedding_functions
import datetime
import os
import json

import sqlite3

# --- Graph Engram Layer (SQLite Knowledge Graph - Simple-Graph Style) ---
class GraphEngram:
    def __init__(self, persistence_path="knowledge_graph.db"):
        self.path = persistence_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # Table for entities/nodes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT
                )
            """)
            # Table for relations/edges
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT,
                    relation TEXT,
                    target TEXT,
                    FOREIGN KEY(source_id) REFERENCES nodes(id)
                )
            """)
            # Table for raw dream logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dream_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    subject TEXT,
                    predicate TEXT,
                    object TEXT,
                    raw_log TEXT
                )
            """)
            conn.commit()

    def _hash(self, text):
        # Extremely robust normalization: lowercase + alphanumeric only
        clean = "".join(filter(str.isalnum, text)).lower()
        return hashlib.sha256(clean.encode()).hexdigest()

    def add_triplet(self, subject, relation, target):
        # Normalize subject for label
        norm_subject = subject.strip()
        if len(norm_subject) > 50: norm_subject = norm_subject[:47] + "..."
        
        subject_id = self._hash(norm_subject)
        target = target.strip()
        
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # 1. Ensure node exists
            cursor.execute("INSERT OR IGNORE INTO nodes (id, label) VALUES (?, ?)", (subject_id, norm_subject))
            
            # 2. Check for duplicate edge
            cursor.execute("SELECT 1 FROM edges WHERE source_id = ? AND relation = ? AND target = ?", 
                           (subject_id, relation, target))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO edges (source_id, relation, target) VALUES (?, ?, ?)", 
                               (subject_id, relation, target))
            conn.commit()

    def exists(self, subject, relation, target):
        """Checks if a triplet already exists to avoid duplication loops."""
        norm_subject = subject.strip()
        subject_id = self._hash(norm_subject)
        target = target.strip()
        
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM edges WHERE source_id = ? AND relation = ? AND target = ?", 
                           (subject_id, relation, target))
            return cursor.fetchone() is not None

    def get_context(self, text):
        """Retrieves related context for entities recognized in the text."""
        normalized_text = text.lower()
        concepts = []
        seen_ids = set()

        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            
            # 1. Token-based lookup
            words = text.split()
            for word in words:
                cleaned = "".join(filter(str.isalnum, word)).lower()
                if not cleaned: continue
                
                word_id = self._hash(cleaned)
                if word_id in seen_ids: continue
                
                cursor.execute("""
                    SELECT n.label, e.relation, e.target 
                    FROM nodes n 
                    JOIN edges e ON n.id = e.source_id 
                    WHERE n.id = ?
                """, (word_id,))
                
                rows = cursor.fetchall()
                if rows:
                    label = rows[0][0]
                    desc = ", ".join([f"{r[1]} {r[2]}" for r in rows])
                    concepts.append(f"{label}: {desc}")
                    seen_ids.add(word_id)

            # 2. Label-based contains lookup (for multi-word entities)
            if len(concepts) < 3:
                # We fetch all labels and check if they are in the text
                # For very large graphs, this might need optimization (e.g. FTS)
                cursor.execute("SELECT id, label FROM nodes")
                all_nodes = cursor.fetchall()
                for node_id, label in all_nodes:
                    if node_id in seen_ids: continue
                    if len(label) > 3 and label.lower() in normalized_text:
                        cursor.execute("SELECT relation, target FROM edges WHERE source_id = ?", (node_id,))
                        edges = cursor.fetchall()
                        if edges:
                            desc = ", ".join([f"{e[0]} {e[1]}" for e in edges])
                            concepts.append(f"{label}: {desc}")
                            seen_ids.add(node_id)
                            if len(concepts) >= 3: break

        return "\n".join(concepts) if concepts else None

    def log_dream(self, subject, predicate, object_curr):
        """Logs a dream discovery into the SQLite journal."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raw_log = f"[{timestamp}] Dream Discovery: [{subject}] --({predicate})--> [{object_curr}]"
        
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO dream_journal (timestamp, subject, predicate, object, raw_log) VALUES (?, ?, ?, ?, ?)",
                (timestamp, subject, predicate, object_curr, raw_log)
            )
            conn.commit()
        return raw_log

# --- Episodic Layer (Vector DB) ---
class EpisodicLayer:
    def __init__(self, persistence_path="./memory_db"):
        self.client = chromadb.PersistentClient(path=persistence_path)
        
        # Use a default embedding function (e.g., all-MiniLM-L6-v2) suitable for local CPU usage
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        self.collection = self.client.get_or_create_collection(
            name="episodic_memory",
            embedding_function=self.ef
        )

    def add_episode(self, user_input, agent_response, context="general"):
        """Stores an interaction 'episode'."""
        timestamp = datetime.datetime.now().isoformat()
        
        # We store the combined interaction as the document
        document = f"User: {user_input}\nAgent: {agent_response}"
        
        self.collection.add(
            documents=[document],
            metadatas=[{"timestamp": timestamp, "type": "interaction", "context": context}],
            ids=[f"ep_{timestamp}"]
        )

    def add_fact_triplet(self, subject, relation, target):
        """Stores a specific fact triplet for semantic retrieval."""
        timestamp = datetime.datetime.now().isoformat()
        fact_text = f"{subject} {relation} {target}"
        
        self.collection.add(
            documents=[fact_text],
            metadatas=[{"timestamp": timestamp, "type": "fact", "subject": subject}],
            ids=[f"fact_{timestamp}_{hashlib.md5(fact_text.encode()).hexdigest()[:8]}"]
        )

    def search_similar(self, query, n_results=2):
        """Retrieves similar past experiences."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # ChromaDB returns a dict with lists. We'll simplify this.
        if results['documents']:
            return results['documents'][0] # Return list of strings
        return []

# Simple test if run directly
if __name__ == "__main__":
    print("--- Memory System Test ---")
    engram = GraphEngram()
    
    with sqlite3.connect(engram.path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM nodes")
        size = cursor.fetchone()[0]
        print(f"Graph size: {size} nodes")
    
    # Non-destructive search test
    test_query = "sofía"
    ctx = engram.get_context(test_query)
    print(f"Context for '{test_query}':\n{ctx if ctx else 'None'}")
    
    episodic = EpisodicLayer(persistence_path="./memory_db")
    print("Episodic layer initialized.")
