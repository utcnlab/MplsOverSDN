#!/bin/sh

topology=${1:-simpleNet.json}

echo Topology && python2.7 Viewer.py ./topologies/${topology}