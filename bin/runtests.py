#!/usr/bin/env python

from unittest import defaultTestLoader, runner

if __name__ == '__main__':
    test = defaultTestLoader.discover('.', 'test*.py', None)
    runner.TextTestRunner().run(test)
