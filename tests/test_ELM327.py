import unittest
import subprocess
import signal
import time
from elm import Elm
from elm327 import ELM327

class TestELM327(unittest.TestCase):
    def setUp(self):
        self.elm_proc = subprocess.Popen(["elm"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        # Retrieve the port that ELM327-emulator running
        while True:
            line = self.elm_proc.stdout.readline()
            if line.startswith(b'ELM327-emulator is running'):
                self.port = line.strip().split()[-1].decode()
                break

    def tearDown(self):
        self.elm_proc.communicate(b"quit\n")

    def test_basicc_commands(self):
        elm = ELM327(self.port)
        self.assertEqual(elm.sendSingleCommand("ATD"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATSP6"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATE0"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATS0"), 'OK')
        self.assertEqual(elm.sendSingleCommand("ATH1"), 'OK')
        self.assertRegex(elm.sendSingleCommand("ATI"), r"ELM327 v\d\.")
        elm.sendSingleCommand("ATSP6")
        self.assertEqual(elm.sendSingleCommand("ATDP"), 'ISO 15765-4 (CAN 11/500)')
        self.assertTrue(elm.sendSingleCommand("ATDPN").endswith('6'))

    def test_readVoltage(self):
        elm = ELM327(self.port)
        self.assertTrue(0.0 < elm.readVoltage() < 20.0)

if __name__ == '__main__':
    unittest.main()
