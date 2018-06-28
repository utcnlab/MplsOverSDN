#!/bin/sh

topology=${1:-simpleNet.json}

echo MPLS controller && echo python2.7 MPLS.py --netfile ./topologies/${topology} && python2.7 MPLS.py --netfile ./topologies/${topology}