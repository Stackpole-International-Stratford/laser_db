from pylogix import PLC
with PLC("192.168.10.1") as comm:
    ret = comm.SetPLCTime()
    print(ret.Value, ret.Status)