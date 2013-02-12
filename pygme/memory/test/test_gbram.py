# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

import unittest

from pygme.memory import gbram

class TestGBRAM(unittest.TestCase):

    numTests = 10

    def setUp(self):
        self._mem = gbram.GBRAM()

    def tearDown(self):
        self.mem = None


if __name__ == '__main__':
    unittest.main()
