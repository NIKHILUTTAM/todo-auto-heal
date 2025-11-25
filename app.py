from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# --- IN-MEMORY STORAGE (No Database) ---
# This list acts as our temporary database.
# WARNING: Data will be lost when Vercel restarts the serverless function.
todos = [
    {"id": 1, "content": "This is a temporary task"},
    {"id": 2, "content": "Data will reset on reload"}
]

# Helper to generate unique IDs
def get_next_id():
    if not todos:
        return 1
    return max(task["id"] for task in todos) + 1

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "storage": "in-memory"}), 200

@app.route('/todos', methods=['GET'])
def get_todos():
    return jsonify(todos)

@app.route('/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    item_content = data.get('item')
    
    new_task = {
        "id": get_next_id(),
        "content": item_content
    }
    
    todos.append(new_task)
    return jsonify({"message": "Added", "item": new_task}), 201

@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    global todos
    # Keep only tasks that DO NOT match the ID to delete
    initial_count = len(todos)
    todos = [task for task in todos if task["id"] != id]
    
    if len(todos) < initial_count:
        return jsonify({"message": "Task deleted"}), 200
    else:
        return jsonify({"error": "Task not found"}), 404

# Vercel handles the run command, so we don't strictly need 'if name == main'