#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import logging.config
import argparse
import re
import os
import sys

from ConfigParser import ConfigParser
from StringIO import StringIO 
from ftplib import FTP

from instance_lock import InstanceLock


################################################################################
class Shared(object):
    Verbose = ""
    Logger = None
    User = ""
    Password = ""
    Host = ""
    Base = ""
    Struct = ""

    @classmethod
    def Configure(cls, config):
        try:
            parser = ConfigParser()
            with open(config, 'r') as text:
                stream = StringIO("[Client]\n" + text.read()) 
                parser.readfp(stream)
                cls.User = parser.get('Client', 'USER')
                cls.Password = parser.get('Client', 'PASS')
                cls.Host = parser.get('Client', 'HOST')
                cls.Base = parser.get('Client', 'BASE')
                cls.Struct = parser.get('Client', 'STRUCT')
                return True
        except:
            cls.Logger.error("Failed to config file")
            return False

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
    def ToDataCenter(cls, dataFolder):
        old = os.getcwd()
        try:
            ftp = FTP(cls.Host)
            ftp.login(cls.User, cls.Password)
            ftp.cwd(cls.Base)

            os.chdir(dataFolder)
            RINEX2_DATA = re.compile(r'^\w{4}(?P<doy>\d{3})\w{1}\d{2}\.(?P<yy>\d{2})d\.Z$', re.IGNORECASE)
            for item in os.listdir('.'):
                if os.path.isfile(item):
                    try:
                        ok = re.match(RINEX2_DATA, item)
                        if ok:
                            with open(item, 'rb') as data:
                                ftp.storbinary('STOR ' + item, data)
                                cls.Logger.info("Successfully added " + item)
                                os.remove(item)
                    except OSError:
                        cls.Logger.error("Failed to open or remove " + item)
                    except:
                        cls.Logger.error("Failed to add " + item)

        except:
            cls.Logger.error("Failed to put file through FTP " + Host)
        finally:
            ftp.quit()
            os.chdir(old)


################################################################################
def parameters():
    """Design the arguments"""

    options = argparse.ArgumentParser(prog='toDataCenter',
            description="Put files to data center")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2017 by Geodesy, Geoscience Australia')

    options.add_argument('-d', '--source',
            default='/home/ted/BNC/outbound/extnas',
            help='The directory, where rinex data files reside')

    options.add_argument("-g", "--log",
            metavar='/home/ted/BNC/logs/toDataCenter.log',
            default='/home/ted/BNC/logs/toDataCenter.log',
            help='Log file (default: %(default)s)')

    options.add_argument("-v", "--verbose", help="log verbose information to file",
            action="store_true")

    return options.parse_args()


################################################################################
def main():
    """Put files to data center"""

    args = parameters()

    Shared.Settings(args)

    instance_lock = InstanceLock("/home/ted/BNC/logs/.__TO_DATA_CENTER_LOCK__", sys.argv[0], 30)
    try:
        instance_lock.lock()
    except Exception as e:
        Shared.Logger.error("Failed to start: " + e.message)
        sys.exit(-1)

    configFile = os.path.join(args.source, "config");

    if Shared.Configure(configFile):
        Shared.ToDataCenter(args.source)

    instance_lock.unlock()


################################################################################
if __name__ == '__main__':
    main()

