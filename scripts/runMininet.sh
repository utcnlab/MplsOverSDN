#!/bin/sh

topology=${1:-simpleNet.json}

echo Mininet && sudo python2.7 NetRunner.py -f ./topologies/$topology -ip 127.0.0.1
