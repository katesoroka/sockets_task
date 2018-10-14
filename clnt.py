#!/usr/bin/env python3

import socket
import selectors
import json
import time

sel = selectors.DefaultSelector()                       # selector for multiplexing client connections
events = selectors.EVENT_READ | selectors.EVENT_WRITE   # expected events to be handled in client socket

class SockClient():
    """
    Client socket class
    """
    def __init__(self, host, port, id):
        self.host = host
        self.port = port
        self.id = id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)


    def register_sel(self, selector):
        """
        connects socket to remote address, registers socket in selector
        :param selector:  the outer selectors list of client objects
        :type selector: selectors.DefaultSelector
        :return:
        """
        try:
            self.sock.connect_ex((self.host, self.port))
            print ('registering client connection, id=', self.id)
            data = json.dumps({'id':self.id, 'tmstmp':time.time()})
            selector.register(self.sock, events, data=data)
        except Exception as e:
            print('Error occured while connecting to server:', e)


def send(key):
    """
    sends data to server
    :param key: connection key in selector objects list
    :return:
    """
    try:
        sock = key.fileobj
        data = key.data
        print("sending", repr(data), "to connection", json.loads(data)['id'])
        data = json.dumps({'id': json.loads(data)['id'], 'tmstmp': time.time()})
        sent = sock.send(data.encode())
        time.sleep(1)
    except ConnectionRefusedError:
        print('Connection to server refused')
        exit(1)


def receive(key):
    """
    receives data from server socket
    :param key: connection key in selector objects list
    :return:
    """
    sock = key.fileobj
    recv_data = sock.recv(1024)   #receiving data
    if recv_data:
        msg = json.loads(recv_data.decode())
        print("received response", msg, "from server")


if __name__ == '__main__':
    host, port = '0.0.0.0', 55555 # host and port to connect
    nclients = 5                  # num of clients to create
    timeout = 10                  # sec
    for i in range(0, nclients):
        clnt = SockClient(host, port, i)
        clnt.register_sel(sel)
    try:
        t_end = time.time() + timeout
        while time.time() < t_end:
            events = sel.select(timeout=1) # wait for registered connection to be ready
            for key, _ in events:
                send(key)               # send the message from client-socket
                receive(key)            # receive message from server socket
        for key, _ in events:           # after loop has ended, properly unregister connections from selector and close the sockets
            print ('Closing connection, id=', json.loads(key.data)['id'])
            sock = key.fileobj
            sel.unregister(sock)
            sock.close()
    except Exception as e:
        print(e)
    finally:
        sel.close()  # closing the selector. should be not opened again
