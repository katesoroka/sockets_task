import socket
import selectors
import types
import json
import time


class SockServer():
    """
    Server socket class
    """
    def __init__(self, host, port):
        self.sel = selectors.DefaultSelector()
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        try:
            self.lsock.bind((host, port))
            self.lsock.listen()
            print("listening on", (host, port))
            self.lsock.setblocking(False)    # set block to false, to make
            self.sel.register(self.lsock, selectors.EVENT_READ, data=None)  # EVENT_READ - make the socket listening
        except Exception as e:
            print(e)
            exit(1)
        # event loop
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:    # if the connection was not established, accept it
                        self._accept(key.fileobj)
                    else:                   # if connection already exists, process them
                        self._service_connection(key, mask)
        except Exception as e:
            print(e)
        finally:
            self.sel.close()

    def _accept(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("Accepted connection from", addr)
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def _service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ: # if the connection is ready to read
            recv_data = sock.recv(1024)
            if recv_data:      # if there is received message, parse i, print and send back a new one
                msg = json.loads(recv_data.decode())
                print("Received message:", msg, ", responding to: ", msg['id'], data.addr)
                msg = json.dumps({'id': msg['id'], 'tmstmp': time.time()})
                sent = sock.send(msg.encode())
            else:               # if there are no more received data, client connection was closed, unregister it here and close as well
                print("closing connection to", data.addr)
                self.sel.unregister(sock)
                sock.close()


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 55555
    ser = SockServer(host, port)
    ser.run()

