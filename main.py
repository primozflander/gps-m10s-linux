#! /usr/bin/python
import time
from smbus2 import SMBus
import signal
import sys
import pynmea2

BUS = None
gpsAddress = 0x42


def connectBus():
    global BUS
    BUS = SMBus(2)


def parseResponse(gpsLine):
    if gpsLine.count(36) == 1:  # Check #1, make sure '$' doesnt appear twice
        if len(gpsLine) < 84:  # Check #2, 83 is maximun NMEA sentenace length.
            charError = 0
            for (
                c
            ) in (
                gpsLine
            ):  # Check #3, Make sure that only readiable ASCII charaters and Carriage Return are seen.
                if (c < 32 or c > 122) and c != 13:
                    charError += 1
            if charError == 0:  #    Only proceed if there are no errors.
                gpsChars = "".join(chr(c) for c in gpsLine)
                if (
                    gpsChars.find("txbuf") == -1
                ):  # Check #4, skip txbuff allocation error
                    gpsStr, chkSum = gpsChars.split(
                        "*", 2
                    )  # Check #5 only split twice to avoid unpack error
                    gpsComponents = gpsStr.split(",")
                    chkVal = 0
                    for ch in gpsStr[
                        1:
                    ]:  # Remove the $ and do a manual checksum on the rest of the NMEA sentence
                        chkVal ^= ord(ch)
                    if chkVal == int(
                        chkSum, 16
                    ):  # Compare the calculated checksum with the one in the NMEA sentence
                        # print(gpsChars)
                        if gpsChars.startswith("$GNGGA"):
                            msg = pynmea2.parse(gpsChars)
                            # print(msg)
                            # breakpoint()
                            printGGA2readableFormat(msg)


def handleCtrlC(signal, frame):
    sys.exit(130)


# This will capture exit when using Ctrl-C
signal.signal(signal.SIGINT, handleCtrlC)


def printGGA2readableFormat(msg):
    print("timestamp:", msg.timestamp)
    print("lat:", msg.latitude)
    # print("lat dir:", msg.lat_dir)
    print("lon:", msg.longitude)
    # print("lon dir:", msg.lon_dir)
    print("quality:", msg.gps_qual)
    print("num sats:", msg.num_sats)
    # print(msg.horizontal_dil)
    print("alt:", msg.altitude)
    # print(msg.altitude_units)
    # print(msg.geo_sep)
    # print(msg.geo_sep_units)
    # print(msg.age_gps_data)
    # print(msg.ref_station_id)
    print("-------------------------")
    time.sleep(1)


def readGPS():
    c = None
    response = []
    try:
        while True:  # Newline, or bad char.
            c = BUS.read_byte(gpsAddress)
            if c == 255:
                return False
            elif c == 10:
                break
            else:
                response.append(c)
        parseResponse(response)
    except IOError:
        connectBus()
    except Exception as e:
        print(e)


connectBus()

while True:
    readGPS()
