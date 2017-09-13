import logging
import logging.config
import os
import psutil
import signal
import datetime
import math
import argparse


################################################################################
def instance_reboot():
    minute = datetime.datetime.now().minute
    reminder = minute % 15
    delta = int(math.fabs(15.0 / 2.0 - reminder) * 60.0)
    cmd = "(sleep " + str(delta) + "; sudo reboot ) &"
    os.system(cmd)


################################################################################
class Shared(object):
    Verbose = ""
    Logger = None

    @classmethod
    def Settings(cls, args):
        cls.Verbose = args.verbose

        if cls.Logger == None:
            cls.Logger = logging.getLogger(__name__)

        for handler in cls.Logger.handlers[:]:
            cls.Logger.removeHandler(handler)

        if cls.Verbose:
            cls.Logger.setLevel(logging.DEBUG)
        else:
            cls.Logger.setLevel(logging.ERROR)

        formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                      datefmt='%Y-%m-%d %I:%M:%S %p')

        fh = logging.handlers.RotatingFileHandler(args.log,
                                                  mode='a',
                                                  maxBytes=65535,
                                                  backupCount=7)
        fh.setFormatter(formatter)
        cls.Logger.addHandler(fh)


    @classmethod
    def memory(cls):
        """ Check instance memory usage and reboot """
        virtual = psutil.virtual_memory()
        if virtual.percent >= 75.0:
            cls.Logger.error("Reboot: Virtual memory total = " + str(virtual.total))
            cls.Logger.error("Reboot: Virtual memory available = " + str(virtual.available))
            cls.Logger.error("Reboot: Virtual memory percentage = " + str(virtual.percent))
            instance_reboot()

        swap = psutil.swap_memory()
        if swap.percent >= 65.0:
            cls.Logger.error("Reboot: Swap memory total = " + str(swap.total))
            cls.Logger.error("Reboot: Swap memory free = " + str(swap.free))
            cls.Logger.error("Reboot: Swap memory percentage = " + str(swap.percent))
            instance_reboot()


    @classmethod
    def processes(cls):
        """ Kill bncGetThread process """

        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['username', 'pid', 'name', 'cmdline'])

                if pinfo['name'] == 'bncGetThread' and '/home/ted/.local/bin/bnc' in pinfo['cmdline']:
                    cls.Logger.error("To kill " + pinfo['name'] + " from " + pinfo['cmdline'][0])
                    proc.send_signal(signal.SIGTERM)

            except psutil.NoSuchProcess:
                pass
            except:
                cls.Logger.error("Failed to kill bncGetThread proces")


################################################################################
def parameters():
    """Design the arguments"""

    options = argparse.ArgumentParser(prog='processManager',
            description="Manage processes of instance")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2017 by Geodesy, Geoscience Australia')

    options.add_argument("-g", "--log",
            metavar='/home/ted/BNC/logs/processManager.log',
            default='/home/ted/BNC/logs/processManager.log',
            help='Log file (default: %(default)s)')

    options.add_argument("-v", "--verbose", help="log verbose information to file",
            action="store_true")

    return options.parse_args()


################################################################################
def main():
    """Start add files to bucket"""

    args = parameters()

    Shared.Settings(args)

    Shared.processes()

    Shared.memory()



################################################################################
if __name__ == '__main__':
    main()

<<<<<<< HEAD
=======

>>>>>>> beae1740357e7f5a9bd9d51310656c8dc550e221
