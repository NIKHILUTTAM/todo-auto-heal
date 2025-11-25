import os
import time
import pymysql
pymysql.install_as_MySQLdb() # Required for Railway MySQL connection

from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
db_url = os.getenv('DATABASE_URL')

# FIX: Railway sends 'mysql://' but Python needs 'mysql+pymysql://'
if db_url and db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

# Fallback for local Docker Compose
if not db_url:
    db_url = 'mysql+pymysql://root:root@db/tododb'

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODEL ---
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "content": self.content}

# --- CRITICAL FIX: AUTO-CREATE TABLES ---
# This runs immediately when Gunicorn loads the app (Fixes missing tables on Cloud)
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables checked/created successfully!")
    except Exception as e:
        print(f"⚠️ Warning during table creation: {e}")

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    try:
        # Simple query to verify connection
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
    # This block only runs locally when you type 'python app.py'
    # Gunicorn ignores this, which is why we moved db.create_all() up above.
    app.run(host='0.0.0.0', port=5000)