#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import logging.config
import argparse
import os
import re
import shutil
import sys

from instance_lock import InstanceLock


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
    
        formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %I:%M:%S %p')

        fh = logging.handlers.RotatingFileHandler(args.log, mode='a', maxBytes=65535, backupCount=7)
        fh.setFormatter(formatter)
        cls.Logger.addHandler(fh)


    @classmethod
    def ToArchive(cls, args):
        old = os.getcwd()
        try:
            dataFolder = args.source
            outbound = args.outbound
            target = args.target

            if os.path.isdir(dataFolder) and os.path.isdir(target) and os.path.isdir(outbound):
                os.chdir(dataFolder)
                pattern = re.compile(r'^\w{4}(?P<doy>\d{3})\w{1}\d{2}\.(?P<yy>\d{2})o$', re.IGNORECASE)

                for item in os.listdir('.'):
                    if os.path.isfile(item):
                        ok = re.match(pattern, item)
                        if ok:
                            yy = ok.group('yy').strip()
                            if yy:
                                yr = int(yy)
                                if yr < 80:
                                    year = 2000 + yr
                                else: 
                                    year = 1900 + yr

                            doy = ok.group('doy').strip()
                            if yy and doy:
                                dirname = os.path.join(target, str(year), yy + doy, "")
                                if not os.path.isdir(dirname):
                                    os.makedirs(dirname, 0755)

                                command = "RNX2CRX -f " + item  
                                os.system(command)
                                crxFile = item[:len(item)-1] + "d"

                                command = "compress -f " + crxFile  
                                os.system(command)
 
                                crxFile += ".Z"

                                dest = os.path.join(dirname, crxFile)
                                link = os.path.join(outbound, crxFile)
                                aws = os.path.join(args.product, crxFile)
                                test = None
                                if args.test:
                                    test = os.path.join(args.test, crxFile)
                                
                                if os.path.isfile(crxFile):
                                    shutil.move(crxFile, dest)
                                    os.symlink(dest, link)
                                    os.symlink(dest, aws)
                                    if test:
                                        os.symlink(dest, test)
                                    
                                    os.remove(item)
        except:
            cls.Logger.error("Failed to archive files")
        finally:
            os.chdir(old)


################################################################################
def parameters():
    """Design the arguments"""

    options = argparse.ArgumentParser(prog='toArchive',
            description="Archive files")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2017 by Geodesy, Geoscience Australia')

    options.add_argument('-t', '--target',
            default='/home/ted/BNC/archive',
            help='The directory, where rinex data files will be archived')

    options.add_argument('-d', '--source',
            default='/home/ted/BNC/convert',
            help='The directory, where rinex data files will be converted')

    options.add_argument('-o', '--outbound',
            default='/home/ted/BNC/outbound/extnas',
            help='The directory, where rinex data files will be disseminated')

    options.add_argument('-p', '--product',
            default='/home/ted/BNC/outbound/aws',
            help='The aws directory, where rinex data files will be disseminated')

    options.add_argument('-q', '--test',
            metavar='/home/ted/BNC/outbound/test',
            help='The test directory, where rinex data files will be disseminated')

    options.add_argument("-g", "--log",
            metavar='/home/ted/BNC/logs/toArchive.log',
            default='/home/ted/BNC/logs/toArchive.log',
            help='Log file (default: %(default)s)')

    options.add_argument("-v", "--verbose", help="log verbose information to file",
            action="store_true")

    return options.parse_args()


################################################################################
def main():
    """Start add files to bucket"""

    args = parameters()

    Shared.Settings(args)

    instance_lock = InstanceLock("/home/ted/BNC/logs/.__TO_ARCHIVE_LOCK__", sys.argv[0], 30)
    try:
        instance_lock.lock()
    except Exception as e:
        Shared.Logger.error("Failed to start: " + e.message)
        sys.exit(-1)
    
    Shared.ToArchive(args)

    instance_lock.unlock()


################################################################################
if __name__ == '__main__':
    main()


