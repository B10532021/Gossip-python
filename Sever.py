import socketio
import eventlet
import eventlet.wsgi
        
# create a Socket.IO server
sio = socketio.Server()

# wrap with a WSGI application
app = socketio.WSGIApp(sio)

@sio.on('connect')
def connect(sid, environ):
    print('connect ', sid)

@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)

@sio.on('test')
def test(sid, msg):
    print(msg['msg2'])


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('localhost', 5000)), app)