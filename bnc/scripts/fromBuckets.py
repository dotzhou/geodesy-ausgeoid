import boto3
import botocore
import datetime
import logging
import logging.config
import argparse
import re
import os
from cStringIO import StringIO


################################################################################
def modify_time(filename):
    timestamp = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(timestamp)


################################################################################
def not_modified(message):
    notModified = re.compile(r'Not Modified', re.IGNORECASE)
    return re.search(notModified, message)


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
    def GetTableTag(cls):
        instance_id_file = '/var/lib/cloud/data/instance-id'

        try:
            with open(instance_id_file, 'r') as instance:
                text = instance.read()
                instance_id = text.strip()
                if len(instance_id) <= 0:
                    raise

                ec2 = boto3.resource('ec2')
                instance = ec2.Instance(instance_id)
                for tag in instance.tags:
                    if tag["Key"].lower() == 'table':
                        table = tag["Value"]
                        return table

        except:
            cls.Logger.error("Failed to get instance id from instance id file"
                             + instance_id_file)

        return ''


    @classmethod
    def NtripSource(cls, ini_file):
        url = ''
        points = ''

        try:
            casterUrl = re.compile(r'^(casterUrlList=http:)(?P<value>.*)$',
                                   re.IGNORECASE)

            mountPoints = re.compile(r'^(mountPoints=).*$',
                                     re.IGNORECASE)

            with open(ini_file, 'r') as ini:
                for line in ini:
                    ok = re.match(casterUrl, line)
                    if ok:
                        links = ok.group('value').split(',')
                        url = links[0] # reasonable, first is the general
                        next

                    ok = re.match(mountPoints, line)
                    if ok:
                        points = line.strip()
                        next

                ini.close()
            return url, points
        except:
            cls.Logger.error("Failed to open ini file: " + ini_file)
        return '', ''


    @classmethod
    def FromBuckets(cls, configFolder):

        table = cls.GetTableTag()
        print(table)
        if not table:
            # no proper tag
            return

        ini_file = os.path.join(os.sep, configFolder, 'BNC.ini')
        url, points = cls.NtripSource(ini_file)
        if not url or not points:
            # no proper ntrip source or no proper mount points
            return

        try:
            bucket_name = 'auscors-ntrip-config'
            bucket_key = 'sourcetable.dat'
            source_table = 'sourcetable.dat'
            timestamp = modify_time(ini_file)
####            timestamp = datetime.datetime(2015, 8, 18)

            client = boto3.client('s3')
            response = client.get_object(Bucket = bucket_name,
                                         IfModifiedSince = timestamp,
                                         Key = bucket_key,
                                         RequestPayer='requester')

            contents = response['Body'].read().split('\n')
            if len(contents) <= 0:
                return

            stations = {}

            backup = {}

            for line in contents:
                data = line.strip().split(';')

                if len(data) >= 19:
                    rtcm = data[3]
                    network = data[7]
                    countryCode = data[8]

                    if rtcm.upper() == 'RAW':
                        continue

                    if countryCode.upper() == 'AUS' or network.upper() == 'SPRGN' or network.upper() == 'ARGN':
                        mountpoint = data[1]
                        name = mountpoint[0:4]

                        if backup.has_key(name):
                            continue

                        records = {}
                        records['mountpoint'] = data[1]
                        records['nmea'] = 'no'
                        records['ntrip'] = '1'
                        records['format'] = data[3]
                        records['network'] = data[7]
                        records['countryCode'] = data[8]
                        records['latitude'] = data[9]
                        records['longitude'] = data[10]
                        records['misc'] = data[18]

                        stations[mountpoint] = records
                        backup[name] = mountpoint[4]

            sortedStations = sorted(stations)
            total = len(sortedStations)
            if total < 100:
                return

            reminder = total % 3
            quotient = int(total / 3.0)
            delta = int(reminder / 2.0 + 0.5)

            if table.lower() == 'first':
                lower = 0
                upper = quotient

            if table.lower() == 'second':
                lower = quotient
                upper = 2*quotient + delta

            if table.lower() == 'third':
                lower = 2*quotient + delta
                upper = 3*quotient + 2*delta # extra one is harmless

            io = StringIO()
            io.write('mountPoints=')

            count = 0
            for key in sortedStations:
                if count >= upper:
                    count += 1
                    break

                if count < lower:
                    count += 1
                    continue

                count += 1
                records = stations[key]

                io.write(url + '/')
                io.write(records['mountpoint'])
                io.write(' ' + records['format'].replace(' ', '_'))
                io.write(' ' + records['countryCode'])
                io.write(' ' + records['latitude'])
                io.write(' ' + records['longitude'])
                io.write(' ' + records['nmea'])
                io.write(' ' + records['ntrip'])
                io.write(', ')

            text = io.getvalue()
            text = text.strip(", ")

            io.close()

            if text != points:
                old = re.escape(points)
                replacement = re.escape(text)
                cmd = "sed -i 's/" + old + "/" + replacement + "/g' " + ini_file
####                cmd = "sed -i 's/" + old + "/" + replacement + "/g' " + "/tmp/Play/BNC.ini"
                os.system(cmd)

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                cls.Logger.error("The object does not exist at S3 bucket.")
            else:
                if not_modified(e.message):
                    pass # Not flood log
                else:
                    cls.Logger.error("S3 bucket error: " + e.message)
        except:
            cls.Logger.error("Failed to connect S3 or the object does not exist")


################################################################################
def parameters():
    """Design the arguments"""

    options = argparse.ArgumentParser(prog='fromBuckets',
            description="Get source table from S3 buckets")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2017 by Geodesy, Geoscience Australia')

    options.add_argument('-t', '--target',
            default='/home/ted/BNC/config',
            help='The directory, where source table and ini file reside')

    options.add_argument("-g", "--log",
            metavar='/home/ted/BNC/logs/fromBuckets.log',
            default='/home/ted/BNC/logs/fromBuckets.log',
            help='Log file (default: %(default)s)')

    options.add_argument("-v", "--verbose", help="log verbose information to file",
            action="store_true")

    return options.parse_args()


################################################################################
def main():
    """Start add files to bucket"""

    args = parameters()

    Shared.Settings(args)

    Shared.FromBuckets(args.target)


################################################################################
if __name__ == '__main__':
    main()



