#!/usr/bin/env python3

"""Stream two float64 values to Simulink over UDP, no timestamps."""

 

import socket
import struct
import random
import time

 

HOST, PORT = "127.0.0.1", 5005   # same device → loopback

INTERVAL = 0.05                  # 20 Hz; go faster if you like

 

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

 

while True:

    a = random.random() * 1.9 + 0.2

    b = random.random() * 0.8 + 0.2

    sock.sendto(struct.pack("<dd", a, b), (HOST, PORT))  # 16 bytes, 2 little-endian doubles

    time.sleep(INTERVAL)
    #print('Working')

"""
import:
import socket
import struct

define:
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

loop:
sock.sendto(struct.pack("<dd", a, b), ("127.0.0.1", 5005))

"""