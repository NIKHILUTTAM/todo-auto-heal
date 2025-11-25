import os
import pymysql
pymysql.install_as_MySQLdb() # Required for Vercel to talk to MySQL

from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- DATABASE CONFIG ---
# Vercel needs the Public URL from Railway
db_url = os.getenv('DATABASE_URL')

# Fix URL format for SQLAlchemy (Railway gives 'mysql://', we need 'mysql+pymysql://')
if db_url and db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Serverless Optimization: Recycle connections to prevent "Lost Connection" errors
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 280,
    "pool_pre_ping": True
}

db = SQLAlchemy(app)

# --- MODEL ---
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "content": self.content}

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    try:
        # Simple query to check connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "healthy", "platform": "Vercel Serverless"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/todos', methods=['GET'])
def get_todos():
    # Serverless Trick: Create tables on the fly if they don't exist yet
    # (Because we don't have a startup script in Serverless)
    with app.app_context():
        db.create_all()
        
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

# Note: We removed "if __name__ == '__main__': app.run()" because Vercel controls the startup.