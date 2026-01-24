from flask import Flask, render_template_string, jsonify, request
import sqlite3
import datetime
import os

app = Flask(__name__)

DB_PATH = "knowledge_graph.db"

def get_db_stats():
    stats = {}
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nodes")
            stats['nodes'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM edges")
            stats['edges'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(importance) FROM nodes")
            avg_imp = cursor.fetchone()[0]
            stats['avg_importance'] = round(avg_imp, 3) if avg_imp else 0.0

            cursor.execute("SELECT COUNT(*) FROM dream_journal")
            stats['dreams'] = cursor.fetchone()[0]

            # Social Rules / Strategy Lessons
            cursor.execute("SELECT COUNT(*) FROM edges WHERE source_type='SocialAnalysis'")
            stats['social_rules'] = cursor.fetchone()[0]
    except Exception as e:
        stats = {'nodes': 0, 'edges': 0, 'error': str(e)}
    return stats

def get_recent_logs(limit=20):
    logs = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, raw_log FROM dream_journal ORDER BY id DESC LIMIT ?", (limit,))
            logs = [{"timestamp": r[0], "msg": r[1]} for r in cursor.fetchall()]
    except:
        pass
    return logs

def send_command(cmd):
    timestamp = datetime.datetime.now().isoformat()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO command_queue (command, status, timestamp) VALUES (?, 'PENDING', ?)", (cmd, timestamp))
            conn.commit()
        return True
    except:
        return False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sofía Cognitive Dashboard</title>
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --accent: #38bdf8; --danger: #ef4444; --success: #22c55e; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { border-bottom: 2px solid var(--accent); padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: var(--card); padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .metric { font-size: 2.5rem; font-weight: bold; color: var(--accent); }
        .label { font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .log-box { background: #000; padding: 15px; border-radius: 5px; height: 400px; overflow-y: auto; font-family: monospace; font-size: 0.85rem; border: 1px solid #334155; }
        .log-entry { margin-bottom: 5px; border-bottom: 1px solid #333; padding-bottom: 2px; }
        .timestamp { color: #64748b; margin-right: 10px; }
        
        /* Control Panel */
        .controls { display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap; }
        button.btn { padding: 10px 20px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .btn-primary { background: var(--accent); color: #000; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-success { background: var(--success); color: white; }
        .btn:hover { opacity: 0.8; transform: translateY(-1px); }
        input.input-text { padding: 10px; border-radius: 5px; border: 1px solid #334155; background: #000; color: white; width: 200px; }

        .refresh-btn { position: fixed; bottom: 20px; right: 20px; background: var(--accent); color: #000; border: none; padding: 12px 24px; border-radius: 30px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 12px rgba(56, 189, 248, 0.4); }
    </style>
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                document.getElementById('nodes').innerText = data.stats.nodes;
                document.getElementById('edges').innerText = data.stats.edges;
                document.getElementById('imp').innerText = data.stats.avg_importance;
                document.getElementById('dreams').innerText = data.stats.dreams;
                document.getElementById('social').innerText = data.stats.social_rules;
                
                const logHTML = data.logs.map(l => 
                    `<div class='log-entry'><span class='timestamp'>${l.timestamp}</span> ${l.msg}</div>`
                ).join('');
                document.getElementById('logs').innerHTML = logHTML;
            } catch (e) { console.error(e); }
        }

        async function sendCommand(cmd, arg='') {
            const finalCmd = arg ? `${cmd} ${arg}` : cmd;
            if (confirm(`¿Ejecutar: ${finalCmd}?`)) {
                await fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: finalCmd})
                });
                alert('Comando enviado a la cola.');
            }
        }

        setInterval(refreshData, 3000); 
        window.onload = refreshData;
    </script>
</head>
<body>
    <div class="container">
        <h1>🧠 Sofía System 3 <span style="font-size:1rem; color:#64748b">Live Dashboard</span></h1>
        
        <!-- Control Panel -->
        <div class="card" style="margin-bottom: 20px; border-left: 4px solid var(--success);">
            <h3>🎛️ Centro de Comando (Remoto)</h3>
            <div class="controls">
                <button class="btn btn-primary" onclick="sendCommand('/synthesize')">🧬 Forzar Síntesis</button>
                <div style="display:flex; gap:0;">
                    <input type="text" id="focusInput" class="input-text" placeholder="Tema de Foco...">
                    <button class="btn btn-success" onclick="sendCommand('/focus', document.getElementById('focusInput').value)">🎯 Fijar Foco</button>
                </div>
                <!-- Future controls -->
            </div>
            <div style="margin-top:10px; font-size:0.8rem; color:#64748b;">
                * Los comandos se ejecutan en el siguiente ciclo del hilo principal.
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="label">Conceptos (Nodos)</div>
                <div class="metric" id="nodes">...</div>
            </div>
            <div class="card">
                <div class="label">Conexiones (Aristas)</div>
                <div class="metric" id="edges">...</div>
            </div>
            <div class="card">
                <div class="label">Importancia Media</div>
                <div class="metric" id="imp">...</div>
            </div>
            <div class="card">
                <div class="label">Sueños Logueados</div>
                <div class="metric" id="dreams">...</div>
            </div>
            <div class="card" style="border-top: 2px solid var(--success);">
                <div class="label">Lecciones Sociales</div>
                <div class="metric" id="social">...</div>
            </div>
        </div>

        <div class="card">
            <h3>📜 Bitácora de Sueño (Tiempo Real)</h3>
            <div class="log-box" id="logs">Cargando...</div>
        </div>
    </div>
    <button class="refresh-btn" onclick="refreshData()">⟳ Refrescar</button>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def api_data():
    return jsonify({
        'stats': get_db_stats(),
        'logs': get_recent_logs()
    })

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.json
    cmd = data.get('command')
    if cmd:
        success = send_command(cmd)
        return jsonify({'success': success})
    return jsonify({'success': False}), 400

if __name__ == '__main__':
    print("🚀 Dashboard de Sofía activo en: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
