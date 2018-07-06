from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

################################################################################
class InstanceLock(object):

    def __init__(self, filename):
        self.filename = filename

    def lock(self):
        if os.path.exists(self.filename):
            raise Exception("Lock file exists.")
        else:
            with open(self.filename, "w") as dummy:
                pass
            os.utime(self.filename, None)

    def unlock(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

