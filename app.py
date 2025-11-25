import os
import time
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

# 1. Initialize Flask
app = Flask(__name__)

# 2. Configure Database
# Get the URL from the environment
db_url = os.getenv('DATABASE_URL')

# FIX: Render provides 'postgres://' but SQLAlchemy needs 'postgresql://'
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Fallback for local testing (Docker Compose) if no env var exists
if not db_url:
    db_url = 'mysql+pymysql://root:root@db/tododb'

# Apply the config
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. Initialize Database
db = SQLAlchemy(app)

# --- MODELS ---
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "content": self.content}

# --- HELPER FUNCTIONS ---
def wait_for_db():
    with app.app_context():
        # Optimization: Don't wait if we are on Render (Postgres is usually ready)
        if 'postgres' in str(app.config['SQLALCHEMY_DATABASE_URI']):
            try:
                db.create_all()
                print("✅ Database connected (Render)")
                return
            except Exception as e:
                print(f"❌ Error connecting to Render DB: {e}")
                return

        # Loop for Local MySQL
        for _ in range(10):
            try:
                db.create_all()
                print("✅ Database connected and tables created!")
                return
            except OperationalError:
                print("⏳ Database not ready yet, waiting...")
                time.sleep(3)
        print("❌ Could not connect to Database.")

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    try:
        # Simple query to check connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "healthy", "db": "connected"}), 200
    except Exception as e:
        # Print error to logs so we can see it in Render Dashboard
        print(f"Health Check Failed: {e}")
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