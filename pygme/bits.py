# Copyright 2013 Sean Kelleher. All rights reserved.
# Use of this source code is governed by a GPL
# license that can be found in the LICENSE file.

def get(val, pos, width=1):
    return (val >> (pos+1-width)) & (2**width - 1)


def set(val, pos, bits, width=1):
    offset = pos + 1 - width
    return (val & ~(_MASKS[width] << offset)) | (bits << offset)


def join(width, msb, lsb):
    """Join two `width`-bit numbers to create a 2`width`-bit number."""
    return (msb << width) | lsb


_MASKS = [2**i - 1 for i in xrange(8)]
