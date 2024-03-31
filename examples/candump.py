# dump all CAN-bus traffic in the can-utils `candump` format, not limited to just diagnostic messages.

import serial
import sys
import time
import re
from elm327 import ELM327

DEVICE = '/dev/ttyUSB0'
BAUDRATE = 115200

READ_BUF_SIZE = 32

IF_NAME = 'elmcan0'

def parseATMALine(data: bytes) -> tuple[int, int, bytes]:
    can_id = int(data[:3], 16)
    dlc = int(chr(data[3]), 16)
    data = bytes.fromhex(data[4:].decode())

    if len(data) != dlc:
        raise ValueError

    return can_id, dlc, data

if __name__ == '__main__':
    msg_filter = None
    msg_mask = '7FF'

    if len(sys.argv) > 1:
        DEVICE = sys.argv[1]
    if len(sys.argv) > 2:
        BAUDRATE = int(sys.argv[2])
    if len(sys.argv) > 3:
        msg_filter = sys.argv[3]
    if len(sys.argv) > 4:
        msg_mask = sys.argv[4]

    elm = ELM327(DEVICE, BAUDRATE, timeout=None)

    assert elm.sendSingleCommand('ATD') == 'OK'
    assert elm.sendSingleCommand('ATE0') == 'OK' # echo off
    assert elm.sendSingleCommand('ATS0') == 'OK' # space off
    assert elm.sendSingleCommand('ATAL') == 'OK' # allow long message
    assert elm.sendSingleCommand('ATH1') == 'OK' # header on
    assert elm.sendSingleCommand('ATCAF0') == 'OK' # CAN auto formatting off
    assert elm.sendSingleCommand('ATD1') == 'OK' # DLC on

    if not msg_filter is None:
        elm.sendSingleCommand('ATCF' + msg_filter)
        elm.sendSingleCommand('ATCM' + msg_mask)

    assert elm.sendSingleCommand('ATDP') == 'ISO 15765-4 (CAN 11/500)'

    elm._ser.timeout = 0.0  # HACK: directly modifying a variable
    elm._ser.write(b'ATMA\r')
    carry = b''
    break_flag = False
    hex_pat = re.compile(rb'^[0-9A-F]+$')
    while not break_flag:
        try:
            buf = (carry + elm._ser.read(READ_BUF_SIZE)).split(b'\r')
            t = time.time()
            carry = buf.pop()
            for line in buf:
                if not hex_pat.match(line.upper()):
                    # Break on 'BUFFER FULL', 'CAN ERROR' and etc.
                    print(line.decode(), file=sys.stderr)
                    break_flag = True
                    break
                try:
                    can_id, dlc, rx_data = parseATMALine(line)
                except (ValueError, IndexError):
                    continue
                # TODO: Adopt the timestamp 't' at the moment the data is first received
                print(f'({t:.06f}) {IF_NAME} {can_id:03X}#' + rx_data.hex().upper())
            sys.stdout.flush()
        except KeyboardInterrupt:
            elm._ser.write(b'\r')    # Stop ATMA
            break
