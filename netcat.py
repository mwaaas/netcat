#!/usr/bin/python
"""
Simple script to check whether or not a host is able to connect to one or multiple other hosts.

Command reference:

netcat.py [parameters] <ip>

Parameters:

ip                 IP address of endpoint to be checked
-p, --port         Port of endpoint to be checked. (Defaults to 80)
-gw, --gateway     IP Address of the VPN gateway to be checked
-d, --description  Alarm description

Example usage: python netcat.py -d "Example connection" -p 8310 -gw 10.99.132.110 10.206.70.213

"""#
import argparse
from time import sleep

import argparse_actions
import socket
import logging
import os
import subprocess

class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if not default and envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

class IpAndHostAction(argparse_actions.ProperIpFormatAction):
    def __call__(self, parser, namespace, values, option_string=None):
        values = socket.gethostbyname(values)
        parent = super(IpAndHostAction, self)
        parent.__call__(parser, namespace, values, option_string)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This is a connectivity checker that logs exceptions to Sumo Logic.')
    parser.add_argument('ip', help='IP address of endpoint to be checked', action=IpAndHostAction)
    parser.add_argument('-p','--port', help='Port of endpoint to be checked. (Defaults to 80)', required=False, default=80, type=int)
    parser.add_argument('-gw','--gateway', help='IP Address of the VPN gateway to be checked', required=False, action=argparse_actions.ProperIpFormatAction)
    parser.add_argument(
        "-d", "--description", dest="description",
        help="Alarm description", required=False)
    parser.add_argument('-t', '--time',
                        help="This is the time to sleep before making another call",
                        required=False, default=3, type=int)

    args=parser.parse_args()

    if args.description == None:
        description = ""
    else:
        description = " name=" + args.description

logging.basicConfig(level=logging.DEBUG)

def ping(host):
    result = subprocess.call(["ping","-c","1",host],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result == 0:
        logging.warning("CANARY: Gateway to=%s%s status=1" % (args.gateway, description))
        return True
    elif result == 1:
        logging.error("CANARY: Gateway to=%s%s status=0 exception='Host not found'" % (args.gateway, description))
    elif result == 2:
        logging.error("CANARY: Gateway to=%s%s status=0 exception='Ping timed out'" % (args.gateway, description))

while True:
    s = socket.socket()
    s.settimeout(10)
    try:
        s.connect((args.ip, args.port))
    except Exception as e:
        alerttext = "CANARY: Endpoint to=%s:%s%s status=0 exception='%s'" % (args.ip, args.port, description, str(e))

    if not args.gateway == None:
        try:
            ping(args.gateway)
        except Exception as e:
            if args.description == None:
                description = " name=VPN"
            alerttext = "CANARY: Endpoint to=%s%s status=0 exception='%s'" % (args.gateway, description, e)


    if 'alerttext' in locals():
        print(alerttext)
        logging.error(alerttext)
    else:
        infotext = "CANARY: Endpoint to=%s:%s%s status=1" % (args.ip, args.port, description)
        print(infotext)
        logging.warning(infotext)

    logging.info('sleep {}'.format(args.time))
    sleep(args.time)



