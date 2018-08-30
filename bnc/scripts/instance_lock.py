from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import datetime
import psutil
import signal

################################################################################
class InstanceLock(object):

    def __init__(self, filename, process_name, lock_duration=30):
        self.filename = filename
        self.process_name = process_name
        self.duration = datetime.timedelta(minutes=lock_duration)

    def lock(self):
        if os.path.exists(self.filename):
            if self.is_old():
                InstanceLock.kill_processes(self.process_name)
                os.utime(self.filename, None)
            else:
                raise Exception("Lock file exists.")
        else:
            with open(self.filename, "w") as dummy:
                pass
            os.utime(self.filename, None)

    def unlock(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def is_old(self):
        timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(self.filename))
        now = datetime.datetime.now()
        return now > (self.duration + timestamp)

    @classmethod
    def kill_processes(cls, process_name):
        pid = os.getpid()

        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['username', 'pid', 'name', 'cmdline'])

                if process_name in pinfo['cmdline'] and pinfo['pid'] != pid:
                    proc.send_signal(signal.SIGTERM)

            except psutil.NoSuchProcess:
                pass
            except:
                pass

