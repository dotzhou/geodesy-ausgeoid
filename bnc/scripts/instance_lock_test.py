#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import time

from instance_lock import InstanceLock


################################################################################
def main():

    print(sys.argv[0])

    instance_lock = InstanceLock("/home/ted/BNC/logs/.__MY_TEST_LOCK__", sys.argv[0], 3)

    try:
        instance_lock.lock()
    except Exception as e:
        print("Failed to start: " + e.message)
        sys.exit(-1)

    print("sleeping ..")
    time.sleep(60*10)

    print("Exit ..")
    instance_lock.unlock()


################################################################################
if __name__ == '__main__':
    main()


