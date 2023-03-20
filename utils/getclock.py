from pylogix import PLC
with PLC("192.168.11.1") as comm:
    time = comm.GetPLCTime()
    print("PLC Time:", time.Value)

    raw_time = comm.GetPLCTime(True)
    print("Raw Time:", raw_time.Value)

    