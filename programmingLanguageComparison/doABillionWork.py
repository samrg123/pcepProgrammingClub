def doABillionWork(val):
    for i in range(0, 1000000):
        val = (val+1) ^ val
    return val

doABillionWork(5)
