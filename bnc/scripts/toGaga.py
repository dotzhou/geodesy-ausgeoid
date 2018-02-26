import logging
import logging.config
import argparse
import re
import os
from multiprocessing import Pool
import subprocess
import copy

################################################################################
class Argument(object):
    def __init__(self, filename, environment):
        self.filename = filename
        self.environment = environment


################################################################################
def serial(argument):
    pattern = re.compile(r'HTTP\/1\.1 200 OK', re.IGNORECASE)
    command = "/home/ted/BNC/scripts/upload2aws.sh -f " + argument.filename + " -e " + argument.environment
    output = subprocess.check_output(['bash','-c', command])
    for line in output.splitlines():
        if re.search(pattern, line):
            os.remove(argument.filename)
            return True

    return False


################################################################################
def batch(bunch, environment):
    if len(bunch) <= 0:
        return

    arguments = []
    for filename in bunch:
        arguments.append(Argument(filename, environment))

    processPool = Pool(len(arguments))
    processPool.map(serial, arguments)
    return

################################################################################
class Shared(object):
    Verbose = ""
    Logger = None
    Environment = "test"

    @classmethod
    def Settings(cls, args):
        cls.Verbose = args.verbose
        cls.Environment = args.environment

        if cls.Logger == None:
            cls.Logger = logging.getLogger(__name__)

        for handler in cls.Logger.handlers[:]:
            cls.Logger.removeHandler(handler)

        if cls.Verbose:
            cls.Logger.setLevel(logging.DEBUG)
        else:
            cls.Logger.setLevel(logging.ERROR)

        formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %I:%M:%S %p')

        fh = logging.handlers.RotatingFileHandler(args.log, mode='a', maxBytes=65535, backupCount=7)
        fh.setFormatter(formatter)
        cls.Logger.addHandler(fh)


    @classmethod
    def ToAws(cls, dataFolder):
        old = os.getcwd()
        try:
            os.chdir(dataFolder)
            RINEX2_DATA = re.compile(r'^\w{4}\d{3}\w{1}\d{2}\.\d{2}d\.Z$', re.IGNORECASE)
            bunch = []
            for item in os.listdir('.'):
                if os.path.isfile(item):
                    try:
                        ok = re.match(RINEX2_DATA, item)
                        if ok:
                            bunch.append(item)
                            if len(bunch) > 9:
                                another = copy.deepcopy(bunch)
                                bunch = []
                                batch(another, cls.Environment)
                    except OSError:
                        cls.Logger.error("Failed to open or remove " + item)
                    except:
                        cls.Logger.error("Failed to add " + item)

            if len(bunch) > 0:
                batch(bunch, cls.Environment)

        except:
            cls.Logger.error("Failed to put file to AWS ")
        finally:
            os.chdir(old)


################################################################################
def parameters():
    """Design the arguments"""

    options = argparse.ArgumentParser(prog='toGaga',
            description="Put files to AWS data center")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2017 by Geodesy, Geoscience Australia')

    options.add_argument('-d', '--source',
            default='/home/ted/BNC/outbound/aws',
            help='The directory, where rinex data files reside')

    options.add_argument("-g", "--log",
            metavar='/home/ted/BNC/logs/toGaga.log',
            default='/home/ted/BNC/logs/toGaga.log',
            help='Log file (default: %(default)s)')

    options.add_argument("-e", "--environment",
            metavar='test',
            default='test',
            help='environment: test | dev (default: %(default)s)')

    options.add_argument("-v", "--verbose", help="log verbose information to file",
            action="store_true")

    return options.parse_args()


################################################################################
def main():
    """Put files to data center"""

    args = parameters()

    Shared.Settings(args)

    Shared.ToAws(args.source)


################################################################################
if __name__ == '__main__':
    main()



