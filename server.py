from socket import *
import threading as th
from time import sleep

'''
Server functionality:
1) Main server listens to a port
2) When a connection is established it starts a new thread to host this client (the client gets unique id
3) Thread function executes until connection is done
4) Thread function first checks for any messages to be sent to the client and sends it if any,
the it suggests the client to send any messages (so the client is mostly waiting for data and handles either
messages or a request for its own message (client responds to the second request only)
5) Commends:
REG <alias><eol> (client-to-server. server responds with <id> or 0 if failed)
MSG <text><eol> (both directions)
RTT<eol> (server-to-client, request to talk)
TRM (client-to-server, client disconnects)
'''

'''
Message format:
{"from": from_alias, "to": to_alias, "from_id": from_id, "to_id": to_id, "message": "test message"}
'''


def debug(s): print(s + "\n")


class Server:
    HOST = "localhost"
    PORT = 8765
    MAX_CLIENTS = 5

    def __init__(self):
        self.client_pool = {}
        self.client_pool_lock = th.Lock()
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((Server.HOST, Server.PORT))
        self.server_stop = False

    def thread_proc(self, connection, my_id):
        debug("client handle thread started with id %d" % my_id)

        with self.client_pool_lock:
            data = self.client_pool[my_id]

        while not self.server_stop:
            ''' first of all check for messages to send to the client '''
            if len(data["messages"]) > 0:
                with data["lock"]:
                    for m in data["messages"]:
                        self.send_message(connection, {"message": m})
                    data["messages"] = []
            ''' then check if the client has a message '''

            self.request_for_message(connection)
            msg = self.wait_for_message(connection)
            if msg:
                self.broadcast(my_id, {"message": msg})
            else:
                sleep(0.1)
                continue

    def broadcast(self, src_id, msg):
        with self.client_pool_lock:
            for dst_id, data in self.client_pool.items():
                data["messages"].append(msg["message"])

    def private(self, src_id, dst_id, msg):
        with self.client_pool_lock:
            self.client_pool[dst_id]["messages"].append(msg)

    def send_message(self, conn, msg):
        conn.send(bytes("MSG " + msg["message"] + "\n", "utf-8"))

    def request_for_message(self, conn):
        conn.send(bytes("RTT\n", "utf-8"))

    def wait_for_message(self, conn):
        data = str(conn.recv(1024), "utf-8")
        if not data:
            pass # connection is broken?
            return ""
        elif data[:3] == "NOP":
            return ""
        elif data[:3] == "MSG":
            return data[4:]
        else:
            pass # incorrect command

    def terminate(self, conn):
        conn.send(bytes("TRM\n", "utf-8"))

    def start(self):
        self.socket.listen(Server.MAX_CLIENTS)
        debug("server is listening on port %d" % Server.PORT)
        self.latest_id = 0
        self.server_stop = False
        while not self.server_stop:
            connection, address = self.socket.accept()
            self.latest_id += 1
            thread = th.Thread(target=self.thread_proc, args=(connection, self.latest_id))
            data = {"thread": thread, "id": self.latest_id, "address": address, "messages": [], "lock": th.Lock()}
            self.client_pool[self.latest_id] = data
            thread.start()

    def stop(self):
        self.server_stop = True
        for c in self.client_pool:
            c["thread"].join()





if __name__ == "__main__":
    Server().start()


"""
https://docs.python.org/3.5/library/socketserver.html?highlight=socketserver#module-socketserver
http://stackoverflow.com/questions/8627986/how-to-keep-a-socket-open-until-client-closes-it
"""