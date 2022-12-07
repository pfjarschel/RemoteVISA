import agilent816xb
import keysightDSOX1200
import time

# Import this for remote support
from remotevisa import CommsManager

# And start communications
commsMan = CommsManager()
commsMan.StartCommunications("143.106.153.67", 8080)

# These arguments enable remote communications. That's it!
dev1 = agilent816xb.Agilent816xb(True, commsMan) 
dev1.connect(True, 20, False)

dev2 = keysightDSOX1200.KeysightDSOX1200(True, commsMan)
dev2.connect()

print(dev1.devID)
print(dev1.getState(0))
print(dev1.getWL(0))
print(dev1.getPwr(0))
print()

dev1.setWL(0, 1554.23)
dev1.setPwr(0, 5)
dev1.setState(0, True)

print(dev1.getState(0))
print(dev1.getWL(0))
print(dev1.getPwr(0))
dev1.setState(0, False)

print()
print(dev2.devID)
print(dev2.getPoints(2))

dev1.close()
dev2.close()
commsMan.CloseCommunications()