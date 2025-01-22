#!/bin/bash

sudo apt update
sudo apt install python3-pip -y
python3 -m pip install customtkinter
sudo apt install python3-tk -y
python3 -m pip install numpy
python3 -m pip install websocket-client
sudo apt install -y build-essential qt5-default qttools5-dev-tools
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install testresources
python3 -m pip install PyQt5
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install ta