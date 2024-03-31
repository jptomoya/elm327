import sys
from elm327 import ELM327

DEVICE = '/dev/ttyUSB0'
BAUDRATE = 115200

# Example code reading input Voltage
# Usage: ELM327.py [device] [baudrate]
if __name__ == '__main__':
    if 2 < len(sys.argv):
        DEVICE = sys.argv[1]
        BAUDRATE = int(sys.argv[2])
    elif 1 < len(sys.argv):
        DEVICE = sys.argv[1]

    elm = ELM327(DEVICE, BAUDRATE, timeout=None)

    res = elm.sendSingleCommand("ATI")
    print(f"{'ATI':11} ->", repr(res))
    res = elm.sendSingleCommand("ATDP")
    print(f"{'ATDP':11} ->", repr(res))
    res = elm.readVoltage()
    print(f"{'readVoltage':11} -> {res} [V]")
