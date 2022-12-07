import remotevisa

remotevisa.commsMan = remotevisa.CommsManager()
remotevisa.commsMan.StartCommunications("143.106.153.67", 8080)
# remotevisa.commsMan.ResetVisa()

rm = remotevisa.ResourceManager()
res_list = rm.list_resources()
print(res_list)
dev0_id = res_list[0]
dev0 = rm.open_resource(dev0_id)
dev1_id = res_list[1]
dev1 = rm.open_resource(dev1_id)
# dev = rm.open_resource("GPIB0::20::INSTR")

print(dev0.query("*IDN?"))
print(dev1.query("*IDN?"))

dev0.close()
dev1.close()

remotevisa.commsMan.CloseCommunications()