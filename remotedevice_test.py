import agilent816xb 

agilent816xb.visa.commsMan.StartCommunications("143.106.153.67", 8080)  # This line starts the communications. That's it!
agilent816xb.visa.commsMan.ResetVisa()

dev = agilent816xb.Agilent816xb()
dev.connectlaser(True, 20, False)

print(dev.laserID)
print(dev.getState(0))
print(dev.getWL(0))
print(dev.getPwr(0))
print()

dev.setWL(0, 1554.23)
dev.setPwr(0, 5)
dev.setState(0, True)

print(dev.getState(0))
print(dev.getWL(0))
print(dev.getPwr(0))

dev.setState(0, False)
dev.closelaser()
agilent816xb.visa.commsMan.CloseCommunications()