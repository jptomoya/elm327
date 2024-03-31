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

if __name__ == '__main__':
    unittest.main()
