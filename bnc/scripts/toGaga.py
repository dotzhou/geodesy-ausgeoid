#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import logging.config
import argparse
import re
import datetime
import os
import multiprocessing
import subprocess
import copy
import sys

from instance_lock import InstanceLock


################################################################################
class Argument(object):

    def __init__(self, filename, environment):
        self.filename = filename
        self.environment = environment


################################################################################
def upload(arg, **kwarg):
    return Shared.serial(*arg, **kwarg)


################################################################################
class Shared(object):
    Verbose = ""
    Logger = None
    Environment = "test"

    Delta = datetime.timedelta(minutes=20)
    LastEpoch = datetime.datetime.now() - Delta

    Lock = multiprocessing.Lock()
    Token = ""

    Rinex2DataPattern = re.compile(r'^\w{4}\d{3}\w{1}\d{2}\.\d{2}d\.Z$', re.IGNORECASE)
    
    """ for both 200 ok and 202 accepted """
    StatusPattern = re.compile(r'HTTP\/1\.1 20', re.IGNORECASE)

    @classmethod
    def settings(cls, args):
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

    def batch(self, bunch, environment):
        if len(bunch) <= 0:
            return

        arguments = []
        for filename in bunch:
            arguments.append(Argument(filename, environment))

        processPool = multiprocessing.Pool(len(arguments))
        processPool.map(upload, zip([self]*len(arguments), arguments))
        return

    def serial(self, argument):
        token = self.get_token() 
        command = "/home/ted/BNC/scripts/upload_to_aws.sh -f " + argument.filename + " -e " + argument.environment + " -k " + token
        output = subprocess.check_output(['bash','-c', command])
        for line in output.splitlines():
            if re.search(Shared.StatusPattern, line):
                os.remove(argument.filename)
                return True

        Shared.Logger.error("[" + argument.filename + "] Failed to upload to AWS")
        return False

    def to_aws(self, dataFolder):
        old = os.getcwd()
        try:
            os.chdir(dataFolder)
            bunch = []
            for item in os.listdir('.'):
                if os.path.isfile(item):
                    try:
                        ok = re.match(Shared.Rinex2DataPattern, item)
                        if ok:
                            bunch.append(item)
                            if len(bunch) > 9:
                                another = copy.deepcopy(bunch)
                                bunch = []
                                self.batch(another, Shared.Environment)
                    except OSError:
                        Shared.Logger.error("[" + item + "]" + " failed to open or remove")
                    except:
                        Shared.Logger.error("[" + item + "]" + " failed to append")

            if len(bunch) > 0:
                self.batch(bunch, Shared.Environment)

        except:
            Shared.Logger.error("Failed to put files onto AWS")

        finally:
            os.chdir(old)

    def get_token(self):
        try:
            Shared.Lock.acquire()
            token = ""
            now = datetime.datetime.now()
            if now < (Shared.LastEpoch + Shared.Delta):
                token = Shared.Token
            else: 
                command = "/home/ted/BNC/scripts/get_token.sh -e " + Shared.Environment
                token = subprocess.check_output(['bash','-c', command])
                Shared.LastEpoch = now
                if len(token) < 100:
                    raise Exception("Failed to get token from OpenAM")
        except:
            Shared.Logger.error("Failed to get token from OpenAM")
        finally:
            Shared.Lock.release()
        return token


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

    Shared.settings(args)
 
    instance_lock = InstanceLock("/home/ted/BNC/logs/.__TO_GAGA_LOCK__")
    try:
        instance_lock.lock()
    except Exception as e:
        Shared.Logger.error("Failed to start: " + e.message)
        sys.exit(-1)

    Shared().to_aws(args.source)
    instance_lock.unlock()


################################################################################
if __name__ == '__main__':
    main()

