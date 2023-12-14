import time 
import sys

from nfc.clf import RemoteTarget
from broadcast_frame_contactless_frontend import BroadcastFrameContactlessFrontend

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main(driver, interface, path, broadcast=''):
    clf = BroadcastFrameContactlessFrontend(f"{interface}:{path}:{driver}")
    log.info(f"Initialized device")
    while True:
        target = clf.sense(
            RemoteTarget("106A"), 
            RemoteTarget("106B"), 
            broadcast=bytes.fromhex(broadcast) if len(broadcast) else None
        )
        if not target:
            continue

        print(f"Got target {target}")
        # Continue intended actions below
        time.sleep(3)


if __name__ == "__main__":
    # Broadcast frames are only implemented for PN532. Feel free to add support for other devices.
    driver = "pn532"

    path = None

    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        print(f"usage: {sys.argv[0]} DEVICE_NAME")
        print()
        print(f"DEVICE_NAME - the name of the device. e.g. 'USB0' for /dev/ttyUSB0")
        sys.exit(1)

    interface = "tty"
    broadcast = "48656c6c6f20776f726c64"

    main(driver, interface, path, broadcast)
