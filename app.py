import os
import time
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

app = Flask(__name__)

# Configure Database Connection
# format: mysql+pymysql://user:password@hostname/databasename
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root@db/tododb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Table Structure
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "content": self.content}

# Retry logic to wait for MySQL to be ready
def wait_for_db():
    with app.app_context():
        for _ in range(10):
            try:
                db.create_all() # Create tables if they don't exist
                print("✅ Database connected and tables created!")
                return
            except OperationalError:
                print("⏳ Database not ready yet, waiting...")
                time.sleep(3)
        print("❌ Could not connect to Database.")

@app.route('/')
def home():
    return jsonify({"message": "To-Do App with MySQL is Running!", "version": "v2.0"})

@app.route('/health')
def health():
    # Check if DB is actually reachable
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

if __name__ == '__main__':
    wait_for_db() # Wait for MySQL before starting
    app.run(host='0.0.0.0', port=5000)