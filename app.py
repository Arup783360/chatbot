from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    sender = db.Column(db.String(50), nullable=False)
    receiver = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if (username == 'arup' and password == 'sarkar') or (username == 'tol' and password == 'mandal'):
        session['username'] = username
        return render_template('chat.html', username=username, messages=Message.query.filter((Message.sender == username) | (Message.receiver == username)).all())
    return 'Invalid credentials!'

@socketio.on('send_message')
def handle_send_message(data):
    message = Message(content=data['content'], sender=data['sender'], receiver=data['receiver'])
    db.session.add(message)
    db.session.commit()
    emit('receive_message', {'content': data['content'], 'sender': data['sender'], 'id': message.id}, broadcast=True)

@socketio.on('delete_message')
def handle_delete_message(data):
    message = Message.query.get(data['id'])
    if message:
        db.session.delete(message)
        db.session.commit()
        emit('delete_message', {'id': data['id']}, broadcast=True)

@socketio.on('clear_chat')
def handle_clear_chat():
    username = session['username']
    Message.query.filter((Message.sender == username) | (Message.receiver == username)).delete()
    db.session.commit()
    emit('clear_chat', broadcast=True)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():  # Ensure the application context is set up
        db.create_all()  # Create database tables
    socketio.run(app, host='0.0.0.0', port=5000)  # Ensure the app is accessible externally
