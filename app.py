import os
import time
import pymysql
pymysql.install_as_MySQLdb() # <--- THIS IS THE MAGIC LINE
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# Railway will provide a DATABASE_URL. 
# If not found, it falls back to the local Docker Compose URL.
db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root@db/tododb')

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELS ---
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "content": self.content}

# --- HELPERS ---
def wait_for_db():
    with app.app_context():
        # Retry loop to wait for MySQL to start
        for _ in range(15):
            try:
                db.create_all()
                print("✅ Database connected!")
                return
            except Exception as e:
                print(f"⏳ Waiting for Database... ({str(e)})")
                time.sleep(3)
        print("❌ Could not connect to Database.")

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "healthy", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/todos', methods=['GET'])
def get_todos():
    todos = Todo.query.all()
    return jsonify([t.to_dict() for t in todos])

@app.route('/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    new_todo = Todo(content=data.get('item'))
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({"message": "Added", "item": new_todo.to_dict()}), 201

@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    task = Todo.query.get(id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task deleted"}), 200
    else:
        return jsonify({"error": "Task not found"}), 404

if __name__ == '__main__':
    wait_for_db()
    app.run(host='0.0.0.0', port=5000)