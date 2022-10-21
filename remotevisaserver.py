import socket as sck
import threading
import pyvisa as visa


class Server():
    def __init__(self):
        self.listen_addr = "0.0.0.0"
        self.listen_port = 8080
        self.conn_ip = "127.0.0.1"
        self.hostname = "host"
        self.rm = None
        self.opendevs = {}
        self.last_id = 0

        # Server functions
        self.comms_srv = {}
        self.comms_srv["visarst"] = self.ResetVisa

        # Resource manager functions
        self.comms_rm = {}
        self.comms_rm["list_resources"] = self.rm_list_resources
        self.comms_rm["open_resource"] = self.rm_open_resource

        # Resource functions
        self.comms_rc = {}
        self.comms_rc["close"] = self.rc_close
        self.comms_rc["open"] = self.rc_open
        self.comms_rc["clear"] = self.rc_clear
        self.comms_rc["write"] = self.rc_write
        self.comms_rc["read"] = self.rc_read
        self.comms_rc["query"] = self.rc_query
        self.comms_rc["timeout"] = self.rc_timeout
        self.comms_rc["read_termination"] = self.rc_read_termination
        self.comms_rc["write_termination"] = self.rc_write_termination

    
    def Start(self, listen_ip="0.0.0.0", port=8080):
        temp_s = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
        temp_s.connect(("1.1.1.1", 80))
        self.conn_ip = temp_s.getsockname()[0]
        temp_s.close()

        self.s = sck.socket(sck.AF_INET, sck.SOCK_STREAM, sck.IPPROTO_TCP)
        self.s.setsockopt(sck.SOL_SOCKET, sck.SO_REUSEADDR, 1)
        self.hostname = sck.gethostname()
        self.s.bind((listen_ip, port))
        self.s.listen(16)
        self.listen_addr = listen_ip
        self.listen_port = port
        print(f"Server initialized on host '{self.hostname}'. IP for connection is {self.conn_ip}. Listening on port {self.listen_port}...")

        return True

    def ResetVisa(self, args):
        try:
            for dev in self.opendevs.values():
                dev.close()
        except:
            pass      
        self.opendevs = None
        del self.opendevs
        self.opendevs = {}
        self.last_id = 0
        
        self.rm = None
        del self.rm

        try:
            self.rm = visa.ResourceManager()
            return True
        except:
            return "Error creating VISA resource manager"
        
    def Listen(self):
        conn, addr = self.s.accept()
        resp = "Connection accepted."
        conn.sendall(resp.encode("Latin1"))
        print(f"Connection received from {addr}")
        return conn, addr
            
    def Receive(self, conn, addr):
        data = conn.recv(1024000)
        resp = True
        if not data:
            return None
        full_comm = data.decode("Latin1")
        comm = full_comm.split(" ")
        if comm[0] == "rm":
            if comm[1] in self.comms_rm:
                print(f"Valid command received: {comm}")
                if len(comm) > 2:
                    resp = self.comms_rm[comm[1]](comm[2:])
                else:
                    resp = self.comms_rm[comm[1]]([])
                resp = f"{resp}"
                print(f"Sending response: {resp}")
                conn.sendall(resp.encode("Latin1"))
            else:
                resp = "Error: Command not understood."
        elif comm[0] == "rc":
            if comm[1] in self.comms_rc:
                print(f"Valid command received: {comm}")
                if len(comm) > 2:
                    resp = self.comms_rc[comm[1]](comm[2:])
                else:
                    resp = self.comms_rc[comm[1]]([])
                resp = f"{resp}"
                print(f"Sending response: {resp}")
                conn.sendall(resp.encode("Latin1"))
            else:
                resp = "Error: Command not understood."
        elif comm[0] == "srv":
            if comm[1] in self.comms_srv:
                print(f"Valid command received: {comm}")
                if len(comm) > 2:
                    resp = self.comms_srv[comm[1]](comm[2:])
                else:
                    resp = self.comms_srv[comm[1]]([])
                resp = f"{resp}"
                print(f"Sending response: {resp}")
                conn.sendall(resp.encode("Latin1"))
            else:
                resp = "Error: Command not understood."
        else:
            resp = "Error: Command not understood."
            print(resp)
            conn.sendall(resp.encode("Latin1"))
        return bool(resp)

    # Resource manager functions
    def rm_list_resources(self, args):
        try:
            query = args[0]
            res_tuple = self.rm.list_resources(query)
            res_string = ""
            for resource in res_tuple:
                res_string += resource
                res_string += "\n"
            return res_string [:-1]
        except:
            return "Error listing devices."

    def rm_open_resource(self, args):
        if len(args) >= 3:
            try:
                resource_name = args[0]
                access_mode = int(args[1])
                open_timeout = int(args[2])
                next_id = f"{(self.last_id + 1)}"
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[1].resource_name == resource_name:
                        print("Device already open!")
                        to = self.opendevs[dev_tuple[0]].timeout
                        rt = self.opendevs[dev_tuple[0]].read_termination
                        wt = self.opendevs[dev_tuple[0]].write_termination
                        return f"{dev_tuple[0]} {to} -{rt}- -{wt}-"
                
                self.opendevs[next_id] = self.rm.open_resource(resource_name, access_mode, open_timeout)
                self.last_id = int(next_id)
                to = self.opendevs[next_id].timeout
                rt = self.opendevs[next_id].read_termination
                wt = self.opendevs[next_id].write_termination
                return f"{next_id} {to} -{rt}- -{wt}-"
            except:
                return f"Error opening device {resource_name}"
        else:
            return "Error: Missing resource name argument (or more)."

    # Resource functions
    def rc_close(self, args):
        if len(args) > 0:
            try:
                dev_id = args[0]
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[0] == dev_id:
                        dev_tuple[1].close()
                        del self.opendevs[dev_tuple[0]]
                        return "Ok."
                return "Error: Device not found or already closed."
            except:
                return "Error closing device."
        else:
            return "Error: Missing device remote id argument"

    def rc_open(self, args):
        if len(args) > 0:
            try:
                resource_name = args[0]
                next_id = f"{(self.last_id + 1)}"
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[1].resource_name == resource_name:
                        print("Device already open!")
                        to = self.opendevs[dev_tuple[0]].timeout
                        rt = self.opendevs[dev_tuple[0]].read_termination
                        wt = self.opendevs[dev_tuple[0]].write_termination
                        return f"{dev_tuple[0]} {to} -{rt}- -{wt}-"
                
                self.opendevs[next_id] = self.rm.open_resource(resource_name)
                self.last_id = int(next_id)
                to = self.opendevs[next_id].timeout
                rt = self.opendevs[next_id].read_termination
                wt = self.opendevs[next_id].write_termination
                return f"{next_id} {to} -{rt}- -{wt}-"
            except:
                return f"Error opening device {resource_name}"
        else:
            return "Error: Missing resource name argument"

    def rc_clear(self, args):
        if len(args) > 0:
            try:
                dev_id = args[0]
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[0] == dev_id:
                        dev_tuple[1].clear()
                        return "Ok."
                return "Error: Device not found."
            except:
                return "Error clearing device."
        else:
            return "Error: Missing device remote id argument"

    def rc_write(self, args):
        if len(args) > 1:
            try:
                dev_id = args[0]
                comm = " ".join(args[1:])
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[0] == dev_id:
                        dev_tuple[1].write(comm)
                        return "Ok."
                return "Error: Device not found."
            except:
                return "Error writing to device."
        else:
            return "Error: Missing arguments"

    def rc_read(self, args):
        if len(args) > 0:
            try:
                dev_id = args[0]
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[0] == dev_id:
                        resp = dev_tuple[1].read()
                        return resp
                return "Error: Device not found."
            except:
                return "Error reading from device."
        else:
            return "Error: Missing arguments"

    def rc_query(self, args):
        if len(args) > 1:
            wresp = self.rc_write(args)
            if ("Error" in wresp) or ("error" in wresp):
                return wresp
            else:
                resp = self.rc_read(args)
                return resp

    def rc_timeout(self, args):
        if len(args) > 1:
            try:
                dev_id = args[0]
                to = args[1]
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[0] == dev_id:
                        dev_tuple[1].timeout = int(to)
                        return "Ok."
                return "Error: Device not found."
            except:
                return "Error setting device property."
        else:
            return "Error: Missing arguments"

    def rc_read_termination(self, args):
        if len(args) > 1:
            try:
                dev_id = args[0]
                term = args[1]
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[0] == dev_id:
                        dev_tuple[1].read_termination = term
                        return "Ok."
                return "Error: Device not found."
            except:
                return "Error setting device property."
        else:
            return "Error: Missing arguments"

    def rc_write_termination(self, args):
        if len(args) > 1:
            try:
                dev_id = args[0]
                term = args[1]
                for dev_tuple in self.opendevs.items():
                    if dev_tuple[0] == dev_id:
                        dev_tuple[1].write_termination = term
                        return "Ok."
                return "Error: Device not found."
            except:
                return "Error setting device property."
        else:
            return "Error: Missing arguments"


def client_loop(conn, addr):
    while True:
        try:
            resp = server.Receive(conn, addr)
            if (not resp) or (resp is None):
                break
        except:
            conn.close()
            del conn
            print(f"Error communicating with client {addr}. Connection closed.")


server = Server()
server.ResetVisa([])
server.Start()

while True:
    conn, addr = server.Listen()
    threading.Thread(target=client_loop, args=(conn, addr)).start()
    