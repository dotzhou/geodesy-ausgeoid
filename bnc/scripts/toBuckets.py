import boto3
import logging
import logging.config
import argparse
import os


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
    def ToBuckets(cls, dataFolder):
        old = os.getcwd()
        try:
            # Let's use Amazon S3
            s3 = boto3.resource('s3')
            os.chdir(dataFolder)
            for item in os.listdir('.'):
                if os.path.isfile(item):
                    try:
                        with open(item, 'rb') as data:
                            s3.Bucket('gnss-archive').put_object(Key='incoming/' + item, Body=data)
                            cls.Logger.info("Successfully added " + item )
                            os.remove(item)
                    except OSError:
                        cls.Logger.error("Failed to open or remove " + item )
                    except:
                        cls.Logger.error("Failed to add " + item )
                            
        except:
            cls.Logger.error("Failed to connect S3 or data folder not existing")
        finally:
            os.chdir(old)


################################################################################
def parameters():
    """Design the arguments"""

    options = argparse.ArgumentParser(prog='toBuckets',
            description="Add files to S3 buckets")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2017 by Geodesy, Geoscience Australia')

    options.add_argument('-d', '--source',
            default='/home/ted/BNC/outbound/aws',
            help='The directory, where rinex data files reside')

    options.add_argument("-g", "--log",
            metavar='/home/ted/BNC/logs/toBuckets.log',
            default='/home/ted/BNC/logs/toBuckets.log',
            help='Log file (default: %(default)s)')

    options.add_argument("-v", "--verbose", help="log verbose information to file",
            action="store_true")

    return options.parse_args()


################################################################################
def main():
    """Start add files to bucket"""

    args = parameters()

    Shared.Settings(args)
    
    Shared.ToBuckets(args.source)


################################################################################
if __name__ == '__main__':
    main()


