from tkinter import *
from tkinter.messagebox import *
import threading as th
from socket import socket

HOST = "localhost"
PORT = 8765

class Client:
    def __init__(self, ui):
        self.inbox = []
        self.outbox = []
        self.outbox_lock = th.Lock()
        self.my_id = 0
        self.my_alias = "Teddy"
        self.sock = socket()
        self.socket_th_stop = False
        self.socket_th = None
        self.ui = ui

    def connect(self):
        self.sock.connect((HOST, PORT))
        self.socket_th_stop = False
        self.socket_th = th.Thread(target=self.socket_thread)
        self.socket_th.start()

    def disconnect(self):
        self.sock.close()

    def socket_thread(self):
        while not self.socket_th_stop:
            data = str(self.sock.recv(1024), "utf-8")
            if data[:3] == "MSG":
                print("Client received a message: " + data[3:])
                self.ui.message_received(data[3:])
            elif data[:3] == "RTT":
                if len(self.outbox) > 0:
                    with self.outbox_lock:
                        alias = "(%s) " % self.my_alias
                        self.sock.send(bytes("MSG " + alias + self.outbox[0], "utf-8"))
                        self.outbox = []
                else:
                    self.sock.send(bytes("NOP\n", "utf-8"))

            elif data[:3] == "TRM":
                print("client socket thread received TRM signal, exiting\n")
                self.sock.close()
                break
            else:
                pass # unknown command - ignore

    def send_broadcast(self, text):
        with self.outbox_lock:
            self.outbox.append(text)

    def send_private(self, target_id):
        pass

    def close(self):
        self.sock.close()
        self.socket_th_stop = True
        self.socket_th.join()


class ClientGui(Frame):
    """
    Builds GUI (widgets and menu), runs main loop, interacts with the user,
    instantiates Client object
    """
    def __init__(self, parent, *args):
        Frame.__init__(self, parent, *args)
        self.pack(expand=True, fill=BOTH, padx=10, pady=10)
        self.client = Client(self)
        self.build_gui()

    def build_gui(self):
        alias = "(%s)" % self.client.my_alias
        self.master.title("PyTalk Client " + alias)
        self.build_menu()
        self.lb_msg = Listbox(self)
        self.lb_msg.pack(expand=True, fill=BOTH)
        fr = Frame(self)
        fr.pack(expand=True, fill=X)
        self.my_msg = Entry(fr)
        self.my_msg.pack(expand=True, fill=X, side=LEFT)
        self.btn_send = Button(fr, text="Send", command=self.on_send)
        self.btn_send.pack(side=RIGHT)
        self.label_status = Label(self, text="Status: none")
        self.label_status.pack(side=BOTTOM, expand=True, fill=X)

    def build_menu(self):
        menu_bar = Menu(self.master)
        file_menu = Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Connect", command=self.on_connect)
        file_menu.add_command(label="Disconnect", command=self.on_disconnect)
        file_menu.add_command(label="Exit", command=self.on_exit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        help_menu = Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="About...", command=self.on_menu_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.master.config(menu=menu_bar)

    def start(self):
        self.mainloop()

    def on_connect(self):
        self.update_status("Connecting to server %s on port %d" % (HOST, PORT))
        try:
            self.client.connect()
            self.update_status("Connected")
        except:
            self.update_status("Connection failed...")

    def on_disconnect(self):
        self.client.disconnect()

    def on_send(self):
        text = self.my_msg.get().strip()
        if text:
            self.client.send_broadcast(text)
        self.my_msg.delete(0, 'end')

    def on_menu_about(self):
        showinfo(title="About", message="PyTalk Messenger (c) by r47717")

    def on_exit(self):
        self.client.close()
        self.quit()

    def update_status(self, t):
        self.label_status.config(text=t)

    def message_received(self, msg):
        self.lb_msg.insert(0, msg)



if __name__ == "__main__":
    ClientGui(Tk()).start()
