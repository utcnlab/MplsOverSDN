#!/bin/sh

sudo apt update && \
sudo apt-get install libffi-dev python-dev build-essential
sudo apt-get install mininet
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
sudo pip install networkx ryu
sudo pip install matplotlib
sudo apt-get install python-tk
