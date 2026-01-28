import sqlite3

DB_PATH = "knowledge_graph.db"

def fix_identity():
    print("🔧 Fixing Identity Crisis (Agustin vs San Agustin)...")
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Get/Create 'San_Agustin' node
        cursor.execute("INSERT OR IGNORE INTO nodes (label, importance) VALUES (?, ?)", ("San_Agustin", 0.8))
        cursor.execute("SELECT id FROM nodes WHERE label = 'San_Agustin'")
        saint_id = cursor.fetchone()[0]
        
        # 2. Get 'Agustin' (User) node
        cursor.execute("SELECT id FROM nodes WHERE label = 'Agustín'")
        # Note: In logs it appears as 'Agustín' (with accent) or 'Agustin' (without).
        # We need to check both or standardize.
        # User input in main.py genesis was 'Agustin' (no accent) in the diff provided by user.
        # But Dream Logs show 'Agustín' (with accent) or 'Augustine' (English).
        
        # Let's handle 'Agustin' (User)
        cursor.execute("SELECT id FROM nodes WHERE label = 'Agustin'")
        user_row = cursor.fetchone()
        
        if not user_row:
            print("❌ User node 'Agustin' not found. Checking 'Agustín'...")
            cursor.execute("SELECT id FROM nodes WHERE label = 'Agustín'")
            user_row = cursor.fetchone()
            
        if not user_row:
             print("❌ No 'Agustin' node found at all.")
             return

        user_id = user_row[0]
        print(f"Found User Node ID: {user_id}")
        
        # 3. Move Philosophical/Historical edges to San_Agustin
        # We identify them by Keywords in Relation or Target
        philosophical_keywords = [
            "scholar", "prolífico", "Dualismo", "mente-cuerpo", "Confessions", 
            "Astrology", "Legitimidad", "contemporaries"
        ]
        
        cursor.execute("SELECT rowid, relation, target FROM edges WHERE source_id = ?", (user_id,))
        edges = cursor.fetchall()
        
        count = 0
        for edge_row in edges:
            rowid, rel, target = edge_row
            
            # Check if this edge smells like St. Augustine
            is_saintly = False
            text_to_check = (rel + " " + target).lower()
            
            for kw in philosophical_keywords:
                if kw.lower() in text_to_check:
                    is_saintly = True
                    break
            
            if is_saintly:
                print(f"Moving Edge: Agustin --[{rel}]--> {target}  >>>  San_Agustin")
                cursor.execute("UPDATE edges SET source_id = ? WHERE rowid = ?", (saint_id, rowid))
                count += 1
                
        print(f"✅ Moved {count} edges to 'San_Agustin'.")
        conn.commit()

if __name__ == "__main__":
    fix_identity()
