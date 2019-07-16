import logging
import logging.config
import os
import psutil
import signal
import argparse


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
    def processes(cls):
        """ Kill BNC process """

        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['username', 'pid', 'name', 'cmdline'])

                if pinfo['name'] == 'bnc' and '/home/ted/.local/bin/bnc' in pinfo['cmdline']:
                    cls.Logger.error("To kill " + pinfo['name'] + " from " + pinfo['cmdline'][0])
                    proc.send_signal(signal.SIGTERM)

            except psutil.NoSuchProcess:
                pass
            except:
                cls.Logger.error("Failed to kill BNC process")


################################################################################
def parameters():
    """Design the arguments"""

    options = argparse.ArgumentParser(prog='restart_bnc',
            description="Manage processes of BNC instance")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2019 by Geodesy, Geoscience Australia')

    options.add_argument("-g", "--log",
            metavar='/home/ted/BNC/logs/restart_bnc.log',
            default='/home/ted/BNC/logs/restart_bnc.log',
            help='Log file (default: %(default)s)')

    options.add_argument("-v", "--verbose", help="log verbose information to file",
            action="store_true")

    return options.parse_args()


################################################################################
def main():
    """Restart BNC"""

    args = parameters()

    Shared.Settings(args)

    Shared.processes()


################################################################################
if __name__ == '__main__':
    main()

