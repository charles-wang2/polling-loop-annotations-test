import time 
import sys
from broadcast_frame_contactless_frontend import BroadcastFrameContactlessFrontend

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main(driver, interface, path, test_name, broadcast=''):
    
    clf = BroadcastFrameContactlessFrontend(f"{interface}:{path}:{driver}")

    default_targets = ['106A']
    targets = default_targets
    if test_name == 'polling_a':
        targets = ['106A']
    elif test_name == 'polling_b':
        targets = ['106B']
    elif test_name == 'polling_a_b':
        targets = ['106A', '106B']
    while True:
        #Polls for appropriate targets based on test name
        rdwr_options = {
            'targets': targets,
            'on-connect': lambda Tag: False
        }
        tag = clf.connect(rdwr=rdwr_options)
        if not tag:
            continue

        cla = 0x00
        ins = 0xA4
        p1 = 0x04
        p2 = 0x00
        response = tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex('F005060708'), check_status=False)
        second_response = tag.transceive(bytearray.fromhex('80CA01F000'), timeout = None)
        log.info("first_response: " + response.hex() + ", second_response: " + second_response.hex())
        time.sleep(3)


if __name__ == "__main__":
    # Broadcast frames are only implemented for PN532. Feel free to add support for other devices.
    driver = "pn532"

    path = None

    if len(sys.argv) >= 2:
        path = sys.argv[1]
    else:
        print(f"usage: {sys.argv[0]} DEVICE_NAME")
        print()
        print(f"DEVICE_NAME - the name of the device. e.g. 'USB0' for /dev/ttyUSB0")
        sys.exit(1)
    
    if len(sys.argv) == 3:
        test_name = sys.argv[2]

    interface = "tty"
    broadcast = "48656c6c6f20776f726c64"

    main(driver, interface, path, test_name, broadcast)
