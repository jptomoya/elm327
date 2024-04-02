import serial
import sys

class ELM327():
    def __init__(self, port=None, baudrate=38400, timeout=None):
        self._ser = None

        # Stop remaining command of ELM327
        with serial.Serial(port, baudrate, timeout=0.1) as ser:
            if ser.read(1):
                ser.write(b'\r')

        self._ser = serial.Serial(port, baudrate, timeout=timeout)

        assert self.sendSingleCommand("ATD") == 'OK'
        assert self.sendSingleCommand("ATE0") == 'OK'
        assert self.sendSingleCommand("ATL0") == 'OK'
        assert self.sendSingleCommand("ATS0") == 'OK'
        assert self.sendSingleCommand("ATH1") == 'OK'

    def __del__(self):
        if self._ser:
            self._ser.close()

    @staticmethod
    def _decodeISOTP(data: list[bytes]) -> list[tuple[int, bytes]]:
        canid_focused = None
        result = []

        for raw_message in data:
            canid = int(raw_message[:3], 16)
            d = bytes.fromhex(raw_message[3:].decode())
            if 0 <= d[0] <= 7:
                len_data = d[0] & 0xF
                result.append((canid, d[1:1+len_data]))
            elif d[0] & 0xF0 == 0x10:
                canid_focused = canid
                len_data = ((d[0] & 0xF)<<8) | d[1]
                buf = d[2:]
            elif d[0] & 0x20 == 0x20:
                assert canid == canid_focused
                buf += d[1:]
                if len_data <= len(buf):
                    canid_focused = None
                    result.append((canid, buf[:len_data]))
            else:
                raise VelueError

        return result

    def sendSingleCommand(self, cmd: str) -> str:
        if not cmd.upper().startswith("AT"):
            raise ValueError("This function requires an AT command.")

        self._ser.write(cmd.replace(' ', '').encode() + b'\r')
        res = self._ser.read_until(b'>')

        buf = res.replace(b'\r\n', b'\r').split(b'\r')
        return buf[-3].decode()

    def sendUDSCommand(self, cmd: str) -> list[bytes]:
        payload = cmd.replace(' ', '').encode() + b'\r'
        self._ser.write(payload)
        res = self._ser.read_until(b'>')

        buf = res.replace(b'\r\n', b'\r').split(b'\r')
        if payload[:-1] == buf[0]:
            buf = buf[1:]   # remove echo
        return buf[:-2]

    def sendKWPCommand(self, cmd: str) -> list[bytes]:
        # TODO: Implement the function
        return self.sendUDSCommand(cmd)

    def readVoltage(self) -> float:
        res = self.sendSingleCommand("ATRV")
        assert res.endswith('V')
        return float(res[:-1])

    def changeBaud(self, target: int) -> bool:
        LF_on: bool # whether CRLF is used as line break in received data

        self._ser.write(b"ATI\r")
        res = self._ser.read_until(b">")
        LF_on = (b'\r\n' in res)
        ati_res = res.replace(b'\r\n', b'\r').split(b'\r')[-3]
        self._ser.write(b'ATBRD%02X\r' % int(4000/(target/1000.0)+0.5))
        self._ser.read_until(b'OK' + (b'\r\n' if LF_on else b'\r'))
        self._ser.baudrate = target

        buf = self._ser.read(len(ati_res))
        if buf != ati_res:
            return False

        self._ser.write(b'\r')
        return b'OK\r' in self._ser.read_until(b'>')

