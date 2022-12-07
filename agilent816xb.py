# -*- coding: utf-8 -*-

class Agilent816xb:
    # definitions
    remote = False
    gpib = True
    eth = False
    usb = False
    gpibAddr = 17
    ip = "192.168.1.2"
    port = 10001
    visarm = None
    visaOK = False
    dev = None
    devOK = False
    devID = ""

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
    def connect(self, isgpib=True, address=17, iseth=False, ethip="192.168.1.2", ethport=10001, isusb=False):
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
                
                self.devID = self.dev.query("*IDN?")
                if "816" in self.devID:
                    self.devOK = True
                    
                else:
                    print("Error opening device! Is it connected?")
            except:
                print("Error opening device! Is it connected?")
                pass

    def init(self):
        return 0

    def enableAll(self):
        for i in range(0, 5):
             self.setState(i, True)

    def disableAll(self):
        for i in range(0, 5):
             self.setState(i, False)

    def close(self):
        if self.devOK:
            self.devOK = False
            self.dev.close()

    def getWL(self, slot):
        if self.devOK:
            resp = self.dev.query(f":sour{slot}:wav?")
            wl = float(resp)*1e9
            return wl
        else:
            return float(0.0)

    def setWL(self, slot, wl):
        if self.devOK:
            self.dev.write(f"sour{slot}:wav {wl*1e-9}")

    def getPwr(self, slot):
        if self.devOK:
            pwr = float(self.dev.query(f":sour{slot}:pow?"))
            return pwr
        else:
            return -99.99

    def setPwr(self, slot, pwr):
        if self.devOK:
            self.dev.write(f":sour{slot}:pow {pwr}")

    def getState(self, slot):
        if self.devOK:
            resp = self.dev.query(f":sour{slot}:pow:stat?")
            if "0" in resp:
                return False
            else:
                return True
        else:
            return False

    def setState(self, slot, onoff):
        if self.devOK:
            if onoff:
                self.dev.write(f":sour{slot}:pow:stat 1")
            else:
                self.dev.write(f":sour{slot}:pow:stat 0")

    def setSweep(self, slot, mode, start, stop, step, cycles, dwell, speed):
        if self.devOK:
            if mode != "CONT" and mode != "STEP":
                mode = "CONT"
            self.dev.write(f":sour{slot}:wav:swe:mode {mode}")
            self.dev.write(f":sour{slot}:wav:swe:start {start}nm")
            self.dev.write(f":sour{slot}:wav:swe:stop {stop}nm")
            self.dev.write(f":sour{slot}:wav:swe:step {step}nm")
            self.dev.write(f":sour{slot}:wav:swe:cycl {cycles}")
            self.dev.write(f":sour{slot}:wav:swe:dwel {dwell}ms")
            self.dev.write(f":sour{slot}:wav:swe:spe {speed}nm/s")

    def setSweepState(self, slot, state):
        if self.devOK:
            options = ["Stop", "Start", "Pause (Stepped)", "Continue (Stepped)"]
            self.dev.write(f":sour{slot}:wav:swe:stat {options.index(state)}")

    def setOutputTrigger(self, slot, state, mode="SWST"):
        """
        configure the trigger

        trig:conf options:
        0 - disable
        1 - default
        2 - passthrough
        3 - loopback

        "SWST" means set the trigger for when the sweep starts
        """
        if self.devOK:
            self.dev.write(f":trig:conf {state}")
            self.dev.write(f":trig{slot}:outp {mode}")

    def SetWavelengthLocking(self, slot, state):
        """
        configure the laser external modulation

        am:stat options:
        0 - off
        1 - wavelength locking
        """
        if self.devOK:
            self.dev.write(f":sour{slot}:am:stat {state}")


