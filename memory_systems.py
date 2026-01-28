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
            # Table for entities/nodes with Importance Scoring
            # - importance: 0.0 to 1.0 (Significance of the concept)
            # - access_count: How many times it has been retrieved/used
            # - last_accessed: Timestamp
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT,
                    importance REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            """)
            
            # Migration check: If table exists but lacks importance, add it.
            cursor.execute("PRAGMA table_info(nodes)")
            columns = [info[1] for info in cursor.fetchall()]
            if "importance" not in columns:
                cursor.execute("ALTER TABLE nodes ADD COLUMN importance REAL DEFAULT 0.5")
                cursor.execute("ALTER TABLE nodes ADD COLUMN access_count INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE nodes ADD COLUMN last_accessed TEXT")
            
            # Table for relations/edges with Confidence Score
            # - confidence: 0.0 to 1.0 (How certain are we of this link?)
            # - source: Provenance (User, Web, Self-Inference)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT,
                    relation TEXT,
                    target TEXT,
                    confidence REAL DEFAULT 1.0,
                    source_type TEXT DEFAULT 'User',
                    FOREIGN KEY(source_id) REFERENCES nodes(id)
                )
            """)
            
            # Migration check for edges
            cursor.execute("PRAGMA table_info(edges)")
            edge_columns = [info[1] for info in cursor.fetchall()]
            if "confidence" not in edge_columns:
                cursor.execute("ALTER TABLE edges ADD COLUMN confidence REAL DEFAULT 1.0")
                cursor.execute("ALTER TABLE edges ADD COLUMN source_type TEXT DEFAULT 'User'")

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

            # Table for Dashboard Command Queue (Remote Control)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT,
                    status TEXT DEFAULT 'PENDING',
                    timestamp TEXT
                )
            """)
            conn.commit()

    def queue_command(self, command):
        """Adds a remote command from the Dashboard."""
        timestamp = datetime.datetime.now().isoformat()
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO command_queue (command, status, timestamp) VALUES (?, 'PENDING', ?)", (command, timestamp))
            conn.commit()

    def pop_command(self):
        """Retrieves and clears the next pending command."""
        cmd = None
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, command FROM command_queue WHERE status='PENDING' ORDER BY id ASC LIMIT 1")
            row = cursor.fetchone()
            if row:
                cid, cmd = row
                cursor.execute("UPDATE command_queue SET status='DONE' WHERE id=?", (cid,))
                conn.commit()
        return cmd

    def _hash(self, text):
        # Extremely robust normalization: lowercase + alphanumeric only
        clean = "".join(filter(str.isalnum, text)).lower()
        return hashlib.sha256(clean.encode()).hexdigest()

    def add_triplet(self, subject, relation, target, confidence=1.0, source_type="User"):
        # Normalize subject for label
        norm_subject = subject.strip()
        if len(norm_subject) > 50: norm_subject = norm_subject[:47] + "..."
        
        subject_id = self._hash(norm_subject)
        target = target.strip()
        
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # 1. Ensure node exists (Initialize with base importance 0.5)
            # If it already exists, we might want to slightly boost importance? For now, leave as is.
            cursor.execute("INSERT OR IGNORE INTO nodes (id, label, importance, access_count, last_accessed) VALUES (?, ?, 0.5, 0, ?)", 
                           (subject_id, norm_subject, datetime.datetime.now().isoformat()))
            
            # 2. Check for duplicate edge
            cursor.execute("SELECT 1 FROM edges WHERE source_id = ? AND relation = ? AND target = ?", 
                           (subject_id, relation, target))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO edges (source_id, relation, target, confidence, source_type) VALUES (?, ?, ?, ?, ?)", 
                               (subject_id, relation, target, confidence, source_type))
            else:
                # Reinforcement: If duplicated, boost confidence slightly?
                cursor.execute("UPDATE edges SET confidence = MIN(1.0, confidence + 0.1) WHERE source_id = ? AND relation = ? AND target = ?",
                               (subject_id, relation, target))
                
            conn.commit()

    def delete_triplet(self, subject, relation, target):
        """Removes a specific triplet from the graph (Self-Correction)."""
        subject_id = self._hash(subject.strip())
        target = target.strip()
        
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM edges WHERE source_id = ? AND relation = ? AND target = ?", 
                           (subject_id, relation, target))
            conn.commit()

    def punish_triplet(self, subject, relation, target):
        """Decreases confidence of a triplet based on negative feedback."""
        subject_id = self._hash(subject.strip())
        target = target.strip()
        
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # 1. Reduce confidence
            cursor.execute("""
                UPDATE edges 
                SET confidence = confidence - 0.5 
                WHERE source_id = ? AND relation = ? AND target = ?
            """, (subject_id, relation, target))
            
            # 2. Check if confidence is too low -> Delete
            cursor.execute("""
                SELECT confidence FROM edges 
                WHERE source_id = ? AND relation = ? AND target = ?
            """, (subject_id, relation, target))
            row = cursor.fetchone()
            
            if row and row[0] <= 0.0:
                print(f"[Memory] Confidence dropped to {row[0]}. Deleting triplet: {subject}->{relation}->{target}")
                self.delete_triplet(subject, relation, target)
            
            conn.commit()

    def get_isolated_nodes(self):
        """Returns list of (id, label) for nodes with very low connectivity."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # Find nodes that are source of <= 1 edge AND target of 0 edges? 
            # Simplified: Nodes with degree < 2
            cursor.execute("""
                SELECT n.id, n.label, COUNT(e.source_id) as degree
                FROM nodes n
                LEFT JOIN edges e ON n.id = e.source_id
                GROUP BY n.id
                HAVING degree <= 1
            """)
            return cursor.fetchall()

    def delete_node(self, node_id):
        """Deletes a node and its edges."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM edges WHERE source_id = ?", (node_id,))
            cursor.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            conn.commit()

    def decay_synapses(self, decay_rate=0.01, prune_threshold=0.1):
        """
        'Plasticity': Applies universal decay to node importance.
        Nodes that are not reinforced (accessed) will eventually fade away.
        """
        import sqlite3
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            
            # 1. Apply Decay to ALL nodes
            cursor.execute("UPDATE nodes SET importance = MAX(0.0, importance - ?)", (decay_rate,))
            
            # 2. Identify weak nodes to prune (Low importance AND low usage)
            # We protect nodes with high access_count (long-term memory candidates) even if importance fluctuates
            cursor.execute("SELECT id, label FROM nodes WHERE importance < ? AND access_count < 2", (prune_threshold,))
            weak_nodes = cursor.fetchall()
            
            if weak_nodes:
                print(f"📉 [Synaptic Decay] Pruning {len(weak_nodes)} weak connections...")
                ids_to_prune = [n[0] for n in weak_nodes]
                
                # Batch delete (Optimization)
                placeholders = ','.join('?' * len(ids_to_prune))
                cursor.execute(f"DELETE FROM edges WHERE source_id IN ({placeholders})", ids_to_prune)
                cursor.execute(f"DELETE FROM nodes WHERE id IN ({placeholders})", ids_to_prune)
                
            conn.commit()
            return len(weak_nodes)

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

    def get_context(self, text, depth=2, episodic_layer=None):
        """Retrieves related context for entities recognized in the text (up to depth 2)."""
        normalized_text = text.lower()
        
        # --- PHASE 0: Semantic Intersection (Vector -> Graph) ---
        # "Plasticity": Use vector search to find concepts that don't match exactly but are semantically related.
        if episodic_layer:
            # 1. Search vector DB for related memories/facts
            semantic_hits = episodic_layer.search_similar(text, n_results=3)
            # 2. Augment the text content to "awaken" those nodes in the graph
            # We simply append the found text so the token-based lookup finds them.
            if semantic_hits:
                augmented_content = " ".join(semantic_hits)
                # We interpret this as: "The user mentioned X, which reminds me of [Vector Results]..."
                # Normalized text now includes these "awakened" concepts
                normalized_text += " " + augmented_content.lower()
                text += " " + augmented_content # For token splitting below

        concepts = []
        seen_ids = set()
        
        # Nodes to expand in the next hop
        next_hop_nodes = set()

        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            
            # --- HOP 1: Direct Lookup ---
            # 1. Token-based lookup
            words = text.split()
            for word in words:
                cleaned = "".join(filter(str.isalnum, word)).lower()
                if not cleaned: continue
                
                word_id = self._hash(cleaned)
                if word_id in seen_ids: continue
                
                cursor.execute("""
                    SELECT n.label, e.relation, e.target, n2.id
                    FROM nodes n 
                    JOIN edges e ON n.id = e.source_id 
                    LEFT JOIN nodes n2 ON n2.label = e.target -- Try to map target label back to ID for Hop 2
                    WHERE n.id = ?
                """, (word_id,))
                
                rows = cursor.fetchall()
                if rows:
                    label = rows[0][0]
                    # Format: Label: relation target, relation target...
                    desc = ", ".join([f"{r[1]} {r[2]}" for r in rows])
                    concepts.append(f"[Nivel 1] {label}: {desc}")
                    seen_ids.add(word_id)
                    
                    # Collect target IDs for Hop 2
                    for r in rows:
                        if r[3]: next_hop_nodes.add(r[3])

            # 2. Label-based contains lookup (for multi-word entities)
            if len(concepts) < 5:
                cursor.execute("SELECT id, label FROM nodes")
                all_nodes = cursor.fetchall()
                for node_id, label in all_nodes:
                    if node_id in seen_ids: continue
                    
                    # Robust matching: Try to match label with spaces AND underscores
                    # "Proyecto_X" -> "proyecto x" to match user input "proyecto x"
                    clean_label = label.lower().replace("_", " ")
                    
                    if len(clean_label) > 3 and clean_label in normalized_text:
                        cursor.execute("""
                            SELECT e.relation, e.target, n2.id 
                            FROM edges e
                            LEFT JOIN nodes n2 ON n2.label = e.target
                            WHERE e.source_id = ?
                        """, (node_id,))
                        edges = cursor.fetchall()
                        if edges:
                            desc = ", ".join([f"{e[0]} {e[1]}" for e in edges])
                            concepts.append(f"[Nivel 1] {label}: {desc}")
                            seen_ids.add(node_id)
                            # Collect target IDs for Hop 2
                            for e in edges:
                                if e[2]: next_hop_nodes.add(e[2])
                            
                            if len(concepts) >= 5: break

            # --- HOP 2: Indirect Lookup (Expansion) ---
            if depth >= 2 and next_hop_nodes:
                # Limit expansion to maintain focus
                nodes_to_expand = list(next_hop_nodes)[:5] 
                
                for nid in nodes_to_expand:
                    if nid in seen_ids: continue # Avoid loops
                    
                    cursor.execute("""
                        SELECT n.label, e.relation, e.target 
                        FROM nodes n 
                        JOIN edges e ON n.id = e.source_id 
                        WHERE n.id = ?
                    """, (nid,))
                    
                    rows = cursor.fetchall()
                    if rows:
                        label = rows[0][0]
                        desc = ", ".join([f"{r[1]} {r[2]}" for r in rows])
                        concepts.append(f"  ↳ [Nivel 2] {label}: {desc}") # Indented visual cue
                        seen_ids.add(nid)
            
            # --- METRIC UPDATE: Update Usage Stats for all seen nodes ---
            if seen_ids:
                now = datetime.datetime.now().isoformat()
                # Batch update for efficiency
                for seen_id in seen_ids:
                    cursor.execute("""
                        UPDATE nodes 
                        SET access_count = access_count + 1, 
                            last_accessed = ?,
                            importance = MIN(1.0, importance + 0.01) -- Slight boost on usage
                        WHERE id = ?
                    """, (now, seen_id))
                conn.commit()

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

    # --- REASONING CACHE METHODS ---
    def cache_reasoning(self, problem, solution):
        """Caches a System 2 Reasoning result."""
        timestamp = datetime.datetime.now().isoformat()
        
        self.collection.add(
            documents=[problem],
            metadatas=[{"timestamp": timestamp, "type": "reasoning_cache", "solution": solution}],
            ids=[f"cache_{hashlib.md5(problem.encode()).hexdigest()[:12]}"]
        )

    def lookup_cache(self, problem, threshold=0.3): # Threshold indicates Distance (Lower is better in Chroma usually, but EF might vary. Default Chroma is L2 distance)
        """
        Checks if we have already solved a similar problem.
        Returns solution string or None.
        Note: ChromaDB default distance is L2 (Squared Euclidean). 0.0 = Identical.
        A threshold of ~0.3 usually implies very high semantic similarity.
        """
        results = self.collection.query(
            query_texts=[problem],
            n_results=1,
            where={"type": "reasoning_cache"} # Filter only cache entries
        )
        
        if results['documents'] and results['documents'][0] and results['distances'] and results['distances'][0]:
            dist = results['distances'][0][0]
            if dist < threshold:
                if results['metadatas'] and results['metadatas'][0]:
                    return results['metadatas'][0][0]['solution']
        return None

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
