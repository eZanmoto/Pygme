# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

class RegFlag:

    def __init__(self, name):
        self._name = name
        self.reset()

    def name(self):
        return self._name

    def val(self):
        return self._val

    def set(self):
        self._val = True

    def reset(self):
        self._val = False

    def setTo(self, val):
        if val == True:
            self.set()
        elif val == False:
            self.reset()
        else:
            raise ValueError("Cannot assign %d to flag register '%s'" %
                    (val, self.name()))
