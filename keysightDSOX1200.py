# -*- coding: utf-8 -*-

visa = None

class KeysightDSOX1200:
    # definitions
    remote = False
    gpib = False
    eth = False
    usb = True
    gpibAddr = 17
    ip = "192.168.1.2"
    port = 10001
    visarm = None
    visaOK = False
    dev = None
    devOK = False
    devID = ""
    usbid_hex = "0x2A8D::0x0396"
    usbid_dec = "10893::918"

    # main functions
    def __init__(self, remote=False, rem_comm_man=None):
        # This block is the only change needed to implement remote VISA support!
        self.remote = remote
        if self.remote:
            import remotevisa as visa
            visa.commsMan = rem_comm_man
            if rem_comm_man == None:
                print("Error: Remote is set to True, but no communication manager given! Create and start communications" + 
                      "with commsMan = remotevisa.CommsManager() and initialize communications." + 
                      "Then, create this object with it as argument.")
        else:
            import pyvisa as visa

        try:
            self.visarm = visa.ResourceManager()
            self.visaOK = True
        except:
            print("Error creating VISA Resource Manager! Are the VISA libraries installed?")

        if not self.visaOK:
            try:
                self.visarm = visa.ResourceManager('@py')
                self.visaOK = True
            except:
                print("Error creating VISA Resource Manager! Are the VISA libraries installed?")

    def __del__(self):
        self.close()
        return 0

    # laser functions
    def connect(self, isgpib=False, address=17, iseth=False, ethip="192.168.1.1", ethport=10001, isusb=True):
        if self.visaOK:
            self.gpib = isgpib
            self.gpibAddr = address
            self.eth = iseth
            self.ip = ethip
            self.port = ethport
            self.usb = isusb
            try:
                if self.gpib:
                    name = "GPIB0::" + str(self.gpibAddr) + "::INSTR"
                    self.dev = self.visarm.open_resource(name)
                elif self.eth:
                    name = "TCPIP0::" + self.ip + "::INSTR"
                    self.dev = self.visarm.open_resource(name, read_termination="\r\n", timeout=5000)
                elif self.usb:
                    devs_list = self.visarm.list_resources()
                    for dev_name in devs_list:
                        if (self.usbid_hex in dev_name) or (self.usbid_dec in dev_name):
                            self.dev = self.visarm.open_resource(dev_name)
                            break

                self.devID = self.dev.query("*IDN?")
                if "DSOX" in self.devID:
                    self.devOK = True
                else:
                    print("Error opening device! Is it connected?")
            except:
                print("Error opening device! Is it connected?")
                pass

    def init(self):
        return 0

    def close(self):
        if self.devOK:
            self.devOK = False
            self.dev.close()

    def getPoints(self, chan):
        if self.devOK:
            curr_chan = self.dev.query("WAV:SOUR?")
            self.dev.write(f"WAV:SOUR CHAN{chan}")
            resp = self.dev.query(f"WAV:POIN?")
            self.dev.write(f"WAV:SOUR {curr_chan}")
            points = int(resp)
            return points
        else:
            return 0



