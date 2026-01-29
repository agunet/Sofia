import sqlite3
import json
import datetime
import os
import hashlib
import warnings
import heapq
from collections import OrderedDict

import sqlite3
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
            
            if "category" not in columns:
                cursor.execute("ALTER TABLE nodes ADD COLUMN category TEXT")
            
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

    def add_triplet(self, subject, relation, target, confidence=1.0, source_type="User", category="General"):
        # Normalize subject for label
        norm_subject = subject.strip()
        if len(norm_subject) > 50: norm_subject = norm_subject[:47] + "..."
        
        subject_id = self._hash(norm_subject)
        target = target.strip()
        
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # 1. Ensure node exists (Initialize with base importance 0.5)
            # We use INSERT OR IGNORE, but if it exists, we might want to update the category if it was NULL?
            cursor.execute("INSERT OR IGNORE INTO nodes (id, label, importance, access_count, last_accessed, category) VALUES (?, ?, 0.5, 0, ?, ?)", 
                           (subject_id, norm_subject, datetime.datetime.now().isoformat(), category))
            
            # Update category if it was previously NULL or "General" and we have a better one
            if category and category != "General":
                 cursor.execute("UPDATE nodes SET category = ? WHERE id = ? AND (category IS NULL OR category = 'General')", (category, subject_id))

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
            # Enforce threshold to prevent "Semantic Flooding"
            semantic_hits = episodic_layer.search_similar(text, n_results=5, threshold=1.2)
            
            # Debug Log (Visible in console to confirm filtering works)
            if semantic_hits:
                print(f"   ↳ [Memoria] {len(semantic_hits)} recuerdos relevantes inyectados.")
            
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
        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError:
            print("⚠️ [EpisodicLayer] ChromaDB not installed. Semantic memory disabled.")
            self.client = None
            self.collection = None
            return

        self.client = chromadb.PersistentClient(path=persistence_path)
        
        # Use a default embedding function (e.g., all-MiniLM-L6-v2) suitable for local CPU usage
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        self.collection = self.client.get_or_create_collection(
            name="episodic_memory",
            embedding_function=self.ef
        )

    def add_episode(self, user_input, agent_response, context="general"):
        """Stores an interaction 'episode'."""
        if self.collection is None: return
        
        timestamp = datetime.datetime.now().isoformat()
        
        # We store the combined interaction as the document
        document = f"User: {user_input}\nAgent: {agent_response}"
        
        self.collection.add(
            documents=[document],
            metadatas=[{"timestamp": timestamp, "type": "interaction", "context": context, "usage_count": 0}],
            ids=[f"ep_{timestamp}"]
        )

    def add_fact_triplet(self, subject, relation, target):
        """Stores a specific fact triplet for semantic retrieval."""
        if self.collection is None: return

        timestamp = datetime.datetime.now().isoformat()
        fact_text = f"{subject} {relation} {target}"
        
        self.collection.add(
            documents=[fact_text],
            metadatas=[{"timestamp": timestamp, "type": "fact", "subject": subject, "usage_count": 0}],
            ids=[f"fact_{timestamp}_{hashlib.md5(fact_text.encode()).hexdigest()[:8]}"]
        )

    def search_similar(self, query, n_results=3, threshold=1.2):
        """
        Retrieves similar past experiences.
        Args:
            query: The search text.
            n_results: Max hits to return.
            threshold: Max L2 distance (Lower is better). 
                       < 0.5: Very close match.
                       < 1.0: Semantically related.
                       > 1.4: Likely unrelated noise.
        """
        if self.collection is None:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        filtered_docs = []
        if results['documents'] and results['distances']:
            docs = results['documents'][0]
            dists = results['distances'][0]
            ids = results['ids'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(docs)
            
            for doc, dist, doc_id, meta in zip(docs, dists, ids, metadatas):
                if dist < threshold:
                    filtered_docs.append(doc)
                    
                    # --- USAGE TRACKING ---
                    # Increment usage count (Synaptic Reinforcement)
                    # Note: To avoid excessive writes, real systems might batch this.
                    try:
                        current_usage = meta.get("usage_count", 0)
                        new_meta = meta.copy()
                        new_meta["usage_count"] = current_usage + 1
                        self.collection.update(ids=[doc_id], metadatas=[new_meta])
                    except Exception as e:
                        pass # Ignore update errors during inference
                else:
                    # Optional: Log pruning if verbose
                    # print(f"[Episodic] Pruned: '{doc[:20]}...' (Dist: {dist:.2f} > {threshold})")
                    pass
                    
        return filtered_docs

    def prune_synapses(self, core_concepts, usage_threshold=5, distance_threshold=0.8):
        """
        [Synaptic Pruning Module]
        Removes memories that are rarely used AND unrelated to core concepts.
        protection_list: List of 'Sacred' strings (e.g. "Agustín", "Poliladron").
        """
        # 1. Query candidates with low usage
        # ChromaDB where filter: usage_count < usage_threshold
        # Note: If usage_count is missing (backward compatibility), it treats it as ? (Usually ignored or use logic)
        # We fetch items where usage_count < usage_threshold OR usage_count is None (implicitly handled if we fetch all and filter in python if where fails, but let's try 'where')
        
        try:
            # We assume usage_count is integer.
            targets = self.collection.get(
                where={"usage_count": {"$lt": usage_threshold}}
            )
        except:
            # Fallback if metadata schema is inconsistent or missing
            return 0

        if not targets['ids']:
            return 0

        ids_to_delete = []
        
        # 2. Check Affinity to Core Concepts
        # We need to embed the core concepts to compare.
        # Ideally we compare embedding of candidate vs embedding of core concepts.
        # Chroma doesn't support "distance to X" in 'get'. We must use 'query' or manual calc.
        # Manual calc is expensive for many items.
        # Heuristic: We query the collection using the CORE CONCEPTS as query texts.
        # Any document returned as a "close match" to a core concept is PROTECTED.
        
        # 2a. Identify Protected IDs (The "White List")
        protected_ids = set()
        
        if self.collection is None: return 0

        for concept in core_concepts:
            results = self.collection.query(
                query_texts=[concept],
                n_results=10, # Protect top 10 matches for each core concept
                include=["ids", "distances"]
            )
            if results['ids']:
                for i, dist in zip(results['ids'][0], results['distances'][0]):
                    if dist < distance_threshold: # If it's close enough to the Core
                        protected_ids.add(i)

        # 3. Intersect: Candidates (Low Usage) - Protected (Core Affinity)
        for doc_id in targets['ids']:
            if doc_id not in protected_ids:
                ids_to_delete.append(doc_id)
                
        # 4. Delete the "Noise"
        if ids_to_delete:
            print(f"✂️ [Synaptic Pruning] Eliminando {len(ids_to_delete)} recuerdos débiles (Low usage + Low affinity).")
            # Batch delete
            # self.collection.delete(ids=ids_to_delete) # Commented out for safety until verified, user asked to implement logic.
            # Real implementation:
            self.collection.delete(ids=ids_to_delete)
            
        return len(ids_to_delete)

    def delete_by_text(self, texts):
        """
        [Consolidation Module]
        Deletes specific text memories after they have been synthesized into the Graph.
        """
        if not texts: return 0
        if self.collection is None: return 0
        
        # We need to find the IDs for these texts.
        # Strategy: Query by text to find IDs.
        
        ids_to_delete = []
        for text in texts:
            # We assume exact match or very close match.
            results = self.collection.get(
                where_document={"$eq": text}
            )
            if results['ids']:
                ids_to_delete.extend(results['ids'])
        
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
            # print(f"🧹 [Consolidated] Deleted {len(ids_to_delete)} raw fact vectors.")
            return len(ids_to_delete)
        return 0

    # --- REASONING CACHE METHODS ---
    def cache_reasoning(self, problem, solution):
        """Caches a System 2 Reasoning result."""
        if self.collection is None: return

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
        if self.collection is None: return None

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

# --- Memory Manager (Short-Term Scarcity Layer) ---
class MemoryManager:
    def __init__(self, max_size=5, db_path="knowledge_graph.db", verbose=False, client=None, model_name="Qwen/Qwen2.5-7B-Instruct"): 
        self.max_size = max_size
        self.db_path = db_path
        self.verbose = verbose
        self.client = client
        self.model_name = model_name
        self.kv_cache = OrderedDict()
        self.ghost_cache = {} # [New] Stores "Ghost Anchors" (Summaries) of evicted nodes
        self.importance_heap = [] 

    def _summarize_node(self, key, content):
        """Generates a Ghost Anchor (Summary) using LLM if available, else truncates."""
        if not self.client:
            return content[:100] + "..." # Fallback
            
        try:
            prompt = f"Resume el siguiente concepto/hecho en UNA sola frase corta y densa para mantenerla en memoria RAM:\n\n'{key}: {content}'"
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except:
            return content[:100] + "..."

    def _archive_to_db(self, data, priority_flag="Baja Prioridad", category="General"):
        """Archives evicted data to the knowledge graph with a priority flag."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure table exists with correct schema
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_graph'")
                if not cursor.fetchone():
                    cursor.execute('''CREATE TABLE knowledge_graph
                                      (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, priority_flag TEXT, category TEXT)''')
                else:
                    # Check if category column exists, add if not (Migration)
                    cursor.execute("PRAGMA table_info(knowledge_graph)")
                    columns = [info[1] for info in cursor.fetchall()]
                    if "category" not in columns:
                        cursor.execute("ALTER TABLE knowledge_graph ADD COLUMN category TEXT")

                cursor.execute("INSERT INTO knowledge_graph (data, priority_flag, category) VALUES (?, ?, ?)", 
                               (str(data), priority_flag, category))
                conn.commit()
            if self.verbose:
                print(f"   💾 [MemoryManager] Archived to DB: '{str(data)[:30]}...' ({priority_flag}, {category})")
        except Exception as e:
            print(f"   ❌ [MemoryManager] Archiving Failed: {e}")


    def store_data(self, key, value, importance, category="General"):
        """
        Stores data with 'Ricardo's Scarcity'.
        If cache is full, evicts the LEAST important item.
        """
        timestamp = datetime.datetime.now().isoformat()
        
        # 1. Update/Insert
        self.kv_cache[key] = {
            "value": value,
            "importance": importance,
            "timestamp": timestamp,
            "category": category
        }
        
        # 2. Push to heap (Python heapq is a min-heap)
        # We push a tuple. If importances are equal, it compares keys (strings).
        heapq.heappush(self.importance_heap, (importance, key))
        
        # 3. Check Scarcity
        if len(self.kv_cache) > self.max_size:
            self.compact_kvcache()

    def compact_kvcache(self):
        """
        Logic: 'Ricardo's Scarcity' + 'Ghost Anchors'.
        When resources (Context/VRAM) are full, valid but less important concepts are summarized (Ghosting)
        instead of being fully forgotten.
        """
        if self.verbose:
            print(f"🧹 [MemoryManager] KV Cache Full (> {self.max_size}). Initiating Ghost Protocol...")
        
        while len(self.kv_cache) > self.max_size:
            # Pop the smallest item (Lowest importance)
            lowest_importance, key_to_evict = heapq.heappop(self.importance_heap)
            
            if key_to_evict in self.kv_cache:
                current_data = self.kv_cache[key_to_evict]
                if current_data["importance"] > lowest_importance:
                    continue # Stale heap entry
                
                # 1. Archive full content to DB (Long Term Storage)
                self._archive_to_db(current_data, "Condensed/Ghosted", category=current_data.get("category", "General"))
                
                # 2. Generate Ghost Anchor (Summary)
                original_content = current_data["value"]
                ghost_summary = self._summarize_node(key_to_evict, original_content)
                
                # 3. Store Ghost
                self.ghost_cache[key_to_evict] = f"👻 [GHOST] {ghost_summary}"
                if len(self.ghost_cache) > self.max_size * 2: # Limit ghosts too
                    # Simple FIFO for ghosts if too many
                    oldest_ghost = next(iter(self.ghost_cache))
                    del self.ghost_cache[oldest_ghost]

                # 4. Evict from Active Cache
                del self.kv_cache[key_to_evict]
                
                if self.verbose:
                    print(f"   👻 [MemoryManager] Ghosted: '{key_to_evict}' -> '{ghost_summary}'")

    def get_context_string(self):
        """Returns a string representation of Active Memory + Ghost Anchors."""
        context = []
        
        # Active Memories
        if self.kv_cache:
            context.append("--- MEMORIA ACTIVA (Alta Resolución) ---")
            for k, v in self.kv_cache.items():
                context.append(f"• {k}: {v['value']} (Imp: {v['importance']})")
        
        # Ghost Anchors
        if self.ghost_cache:
            context.append("\n--- FANTASMAS (Baja Resolución / Contexto Periférico) ---")
            for k, v in self.ghost_cache.items():
                context.append(f"• {k}: {v}")
                
        return "\n".join(context)
    
    def get_state(self):
        return {k: v['importance'] for k, v in self.kv_cache.items()}


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
