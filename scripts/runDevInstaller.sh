#!/bin/sh

sudo apt-get install mininet
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
sudo pip install networkx ryu
sudo pip install matplotlib
sudo apt-get install python-tk
