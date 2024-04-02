import subprocess
import signal
import time
import unittest
from elm import Elm
from elm327 import ELM327

class TestELM327(unittest.TestCase):
    def setUp(self):
        self.elm_emu_proc = subprocess.Popen(["elm"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        # Retrieve the port that ELM327-emulator running
        while True:
            line = self.elm_emu_proc.stdout.readline()
            if line.startswith(b'ELM327-emulator is running'):
                self.port = line.strip().split()[-1].decode()
                break

    def tearDown(self):
        self.elm_emu_proc.communicate(b"quit\n")

    def test_basic_commands(self):
        elm = ELM327(self.port)
        self.assertEqual(elm.sendSingleCommand("ATD"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATSP6"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATE0"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATS0"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATH1"), 'OK')
        self.assertRegex(elm.sendSingleCommand("ATI"), r"^ELM327 v\d\.\d")
        self.assertEqual(elm.sendSingleCommand("ATDP"), 'ISO 15765-4 (CAN 11/500)')
        self.assertTrue(elm.sendSingleCommand("ATDPN").endswith('6'))

    def test_readVoltage(self):
        elm = ELM327(self.port)
        self.assertTrue(0.0 <= elm.readVoltage() <= 20.0)

    def test_OBD2Command(self):
        elm = ELM327(self.port)
        self.assertEqual(elm.sendSingleCommand("ATD"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATSP6"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATCAF1"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATE0"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATL0"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATS0"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATH1"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATD0"), 'OK')

        elm.sendUDSCommand("0100")  # HACK: perform auto search for ELM327-emulator
        resp = elm.sendUDSCommand("0100")
        self.assertIs(type(resp), list)
        for x in resp:
            self.assertIs(type(x), bytes)
            if x not in (b'CAN ERROR', b'NO DATA'):
                self.assertRegex(x, rb'^7[0-9a-fA-F]{16}$')

    def test_decodeISOTP(self):
        self.assertEqual(ELM327._decodeISOTP([b'7EA0762011041424344']),
            [(0x7EA, b'\x62\x01\x10ABCD')])
        self.assertEqual(ELM327._decodeISOTP([b'7EA064100983A8013', b'7E8064100BE3FA813']),
            [(0x7EA, b'\x41\x00\x98\x3A\x80\x13'), (0x7E8, b'\x41\x00\xBE\x3F\xA8\x13')])
        self.assertEqual(ELM327._decodeISOTP([b'7E8037F3178AAAAAAAA', b'7E8047101FF01AAAAAA']),
            [(0x7E8, b'\x7F\x31\x78'), (0x7E8, b'\x71\x01\xFF\x01')])
        self.assertEqual(ELM327._decodeISOTP([b'7E81008620120313233', b'7E82134355555555555']),
            [(0x7E8, b'\x62\x01\x2012345'),])

if __name__ == '__main__':
    unittest.main()
