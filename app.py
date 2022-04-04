
from gevent import monkey
monkey.patch_all()
from requests.exceptions import Timeout

from threading import Lock
from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import requests

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = 'gevent'

app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

url = 'https://api.coinstats.app/public/v1/coins/bitcoin?currency=BTC'

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(3)
        count += 1
        print('request '+url)
        try:
            req = requests.get(url,verify=False, timeout=(2,5))
        except Timeout:
            print('Timeout has been raised.')
        print('wait...')
        req.raise_for_status()
        price = ((req).json())['coin']['price']
        print(price)
        socketio.emit('my_response',
                      {'data': 'Bitcoin current price (USD): ' + str(price),'count':count})

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})

# Receive the test request from client and send back a test response
@socketio.on('test_message')
def handle_message(data):
    print('received message: ' + str(data))
    emit('test_response', {'data': 'Test response sent'})

# Broadcast a message to all clients
@socketio.on('broadcast_message')
def handle_broadcast(data):
    print('received: ' + str(data))
    emit('broadcast_response', {'data': 'Broadcast sent'}, broadcast=True)

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

if __name__ == '__main__':
    
    socketio.run(app)