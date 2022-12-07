import socket as sck
import pyvisa.constants
import pyvisa.util


commsMan = None

class CommsManager():
    def __init__(self):
        self.remhost_addr = "127.0.0.1"
        self.remhost_port = 8080
        self.s = sck.socket(sck.AF_INET, sck.SOCK_STREAM, sck.IPPROTO_TCP)
        self.commsOK = False

    def __del__(self):
        self.CloseCommunications()

    def StartCommunications(self, ip, port):   
        self.commsOK = False
        self.remhost_addr = ip
        self.remhost_port = port
        try:
            self.s.connect((ip, port))
            resp = self.s.recv(1024)
            if resp:
                print(resp.decode("Latin1"))
                self.commsOK = True
        except:
            print("Error connecting to the selected server! Check if it is running on the remote machine, and if IP address and port are correct.")

        return self.commsOK

    def CloseCommunications(self):
        try:
            self.s.close()
            self.commsOK = False
        except:
            print("Error closing the connection. Maybe it was already down?")

    def RestartCommunications(self, ip, port):
        self.CloseCommunications()
        return self.StartCommunications(ip, port)

    def ResetVisa(self):
        self.remote_write("srv visarst")

    def remote_write(self, command):
        if self.commsOK:
            try:
                self.s.sendall(command.encode('Latin1'))
                resp = self.s.recv(1024).decode("Latin1")
                if resp:
                    if ("Error" in resp) or ("error" in resp): print(resp)
                    return True
                else:
                    return False
            except:
                print("Error communicating with the server. Try restarting the connection and/or the server.")
                return False
        else:
            print("Communications are down. Try (re)starting the communications and/or the server.")
            return False

    def remote_read_binary_values(self, command, length=1048576):
        if self.commsOK:
            try:
                self.s.sendall(command.encode('Latin1'))
                resp = self.s.recv(length)
                if resp:
                    resp_l1 = resp.decode("Latin1")
                    if ("Error" in resp_l1) or ("error" in resp_l1): print(resp_l1)
                    return resp
                else:
                    return False
            except:
                print("Error communicating with the server. Try restarting the connection and/or the server.")
                return False
        else:
            print("Communications are down. Try (re)starting the communications and/or the server.")
            return False

    def remote_query(self, command, length=1048576):
        if self.commsOK:
            try:
                self.s.sendall(command.encode('Latin1'))
                resp = self.s.recv(length).decode("Latin1").rstrip()
                if resp:
                    if ("Error" in resp) or ("error" in resp): print(resp)
                    return resp
                else:
                    return False
            except:
                print("Error communicating with the server. Try restarting the connection and/or the server.")
                return False
        else:
            print("Communications are down. Try (re)starting the communications and/or the server.")
            return False

class ResourceManager():
    def __init__(self):
        pass

    def list_resources(self, query="?*::INSTR"):
        rem_list = commsMan.remote_query(f"rm list_resources {query}")
        if rem_list:
            return rem_list.split("\n")

    def open_resource(self, resource_name, access_mode=pyvisa.constants.AccessModes.no_lock, open_timeout=pyvisa.constants.VI_TMO_IMMEDIATE, **kwargs):
        reply = commsMan.remote_query(f"rm open_resource {resource_name} {access_mode} {open_timeout}")
        try:
            reply_list = reply.split(" ")
            dev_id = int(reply_list[0])
            new_dev = Resource()
            new_dev.rem_id = dev_id
            new_dev._timeout = reply_list[1]
            new_dev._read_termination = reply_list[2][1:-1]
            new_dev._write_termination = reply_list[3][1:-1]
            new_dev.resource_name = resource_name
            return new_dev
        except:
            print(f"Error received: {reply}")
            return Resource()

    ## TODO: implement all properties/methods

class Resource():
    def __init__(self):
        self._timeout = 0
        self._read_termination = ""
        self._write_termination = ""
        self.resource_name = ""
        self.rem_id = 0
    
    @property
    def timeout(self):
      return self._timeout

    @property
    def read_termination(self):
      return self._read_termination

    @property
    def write_termination(self):
      return self._write_termination

    @timeout.setter
    def timeout(self, new_timeout):
        self._timeout = new_timeout
        commsMan.remote_write(f"rc timeout {self.rem_id} {new_timeout}")

    @read_termination.setter
    def read_termination(self, new_read_termination):
        self._read_termination = new_read_termination
        commsMan.remote_write(f"rc read_termination {self.rem_id} {new_read_termination}")

    @write_termination.setter
    def write_termination(self, new_write_termination):
        self._write_termination = new_write_termination
        commsMan.remote_write(f"rc write_termination {self.rem_id} {new_write_termination}")

    def close(self):
        commsMan.remote_write(f"rc close {self.rem_id}")

    def open(self):
        self.rem_id = int(commsMan.remote_query(f"rc open {self.resource_name}"))

    def clear(self):
        commsMan.remote_write(f"rc clear {self.rem_id}")

    def write(self, command):
        commsMan.remote_write(f"rc write {self.rem_id} {command}")
    
    def read(self, length=1048576):
        return commsMan.remote_query(f"rc read {self.rem_id}", length)

    def read_binary_values(self, datatype='f', is_big_endian=False, header_fmt='ieee', expect_termination=True, data_points=-1, chunk_size=None):
        command = f"rc read_binary_values {self.rem_id} {datatype} {is_big_endian} {header_fmt} {expect_termination} {data_points} {chunk_size}"
        return commsMan.remote_read_binary_values(command)

    def query(self, command, length=1048576):
        return commsMan.remote_query(f"rc query {self.rem_id} {command}", length)

    def query_binary_values(self, command, datatype='f', is_big_endian=False, header_fmt='ieee', expect_termination=True, data_points=-1, chunk_size=None):
        commsMan.remote_write(f"rc write {self.rem_id} {command}")
        read_command = f"rcb read_binary_values {self.rem_id} {datatype} {is_big_endian} {header_fmt} {expect_termination} {data_points} {chunk_size}"
        binary_resp = commsMan.remote_read_binary_values(read_command)
        resp = pyvisa.util.from_binary_block(binary_resp, offset=0, datatype=datatype, is_big_endian=is_big_endian)
        return resp
    
    ## Serial support ##
    # TODO

    ## TODO: implement all properties/methods