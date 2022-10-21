import remotevisa

remotevisa.commsMan.StartCommunications("143.106.153.67", 8080)
# remotevisa.commsMan.ResetVisa()

rm = remotevisa.ResourceManager()
res_list = rm.list_resources()
dev_id = res_list[0]
dev = rm.open_resource(dev_id)
# dev = rm.open_resource("GPIB0::20::INSTR")

print(dev.query("*IDN?"))

dev.close()


remotevisa.commsMan.CloseCommunications()