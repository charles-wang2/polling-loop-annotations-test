import time 
import sys
from broadcast_frame_contactless_frontend import BroadcastFrameContactlessFrontend
from nfc.clf import ContactlessFrontend
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def on_connected(tag):
    log.info("tag connected: " + str(tag))
    return False
def on_release(tag):
    log.info("Released")
    return tag

def main(driver, interface, path, test_name, broadcast=''):
    log.setLevel('DEBUG')

    #Sets targets appropriately for polling loop
    default_targets = ['106A']
    targets = default_targets
    if test_name == 'polling_a':
        targets = ['106A']
    elif test_name == 'polling_b':
        targets = ['106B']
    elif test_name == 'polling_a_b':
        targets = ['106A', '106B']
    tag = None
    second_loop = False
    while True:
        clf = BroadcastFrameContactlessFrontend(f"{interface}:{path}:{driver}")
        log.info("top of loop")
        rdwr_options = {
            'targets': targets,    
            'on-connect': on_connected,
            'on-release': on_release
        }
        log.info("targets" + str(targets))
        tag = clf.connect(rdwr=rdwr_options)
        if not tag:
            continue

        wallet_role = True


        #expected responses - first response: "123456789000", second response: "1481148114819000"
        cla = 0x00
        ins = 0xA4
        p1 = 0x04
        p2 = 0x00
        #basic command apdu
        command_apdu = '80CA01F000'
        ppse_aid = '325041592E5359532E4444463031'
        mc_aid = 'A0000000041010'
        transport_aid = 'F001020304'
        transport_apdu_1 = '80CA01E000'
        access_aid = 'F005060708'
        transport_apdu_2 = '80CA01E100'
        visa_aid = 'A0000000030000'

        select_transport_apdu = '00A4040005F001020304'

        select_offhost_aid_1 = 'A000000151000000'
        offhost_command_apdu = '80CA9F7F00'
        responses = []
        #if tests passed: return failure vs succcess
        apdu_response_expected_sequence = []

        #payment service 1 - used for single payment emulator and when wallet role is available.
        #build select apdu
        if (test_name == 'payment_service_1'):
            apdu_response_expected_sequence = ['FFFF9000', 'FFEF9000', 'FFDFFFAABB9000']
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(ppse_aid)))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(mc_aid)))
            responses.append(tag.transceive(bytearray.fromhex(command_apdu), timeout = 5000))
        elif test_name == 'payment_service_2':
            apdu_response_expected_sequence = ['1234900', '5678900']
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(ppse_aid)))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(mc_aid)))
        elif test_name == 'transport_service_1':
            apdu_response_expected_sequence = ['80CA9000', '83947102829000']
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(transport_aid)))
            responses.append(tag.transceive(bytearray.fromhex(transport_apdu_1), timeout = 5000))
            continue
        elif test_name == 'fifty_taps':
            apdu_response_expected_sequence = ['80CA9000', '83947102829000']
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(transport_aid)))
            responses.append(tag.transceive(bytearray.fromhex(transport_apdu_1), timeout = 5000))
            tag = None
            clf.close()
            time.sleep(1)
            continue
        #polling loop + observe mode tests    
        elif test_name == 'two_non_payment_services':
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(transport_aid)))
            responses.append(tag.transceive(bytearray.fromhex(transport_apdu_2), timeout = 5000))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(access_aid)))
            responses.append(tag.transceive(bytearray.fromhex('80CA01F000'), timeout = None))


        elif test_name == 'conflicting_non_payment_emulator_activity':
            if not second_loop:
                try:
                    tag.transceive(bytearray.fromhex(select_transport_apdu), timeout = 1)
                except Exception as error:
                    print("exception expected")
                    print(error)
                    second_loop = True
                    # time.sleep(1)
                    continue
            else:
                responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(transport_aid), mrl = 0, check_status = False))
                responses.append(tag.transceive(bytearray.fromhex(transport_apdu_2), timeout = 5))
                print("done writing apdu")
                print(tag)
                second_loop = False
        elif test_name == 'throughput_emulator_activity':
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex('F0010203040607FF')))
            commands = ["80CA010100", "80CA010200", "80CA010300", "80CA010400", "80CA010500", "80CA010600",
                        "80CA010700", "80CA010800", "80CA010900", "80CA010A00", "80CA010B00", "80CA010C00",
                        "80CA010D00", "80CA010E00", "80CA010F00"]
            for command in commands:
                responses.append(tag.transceive(bytearray.fromhex(command), 1))
        # elif test_name == 'fifty_taps':
        #fifty taps test: uses transport_service_1 logic
        elif test_name == 'on_and_off_host_service':

            try: 
                responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex('A000000151000000')))
            except Exception as error:
                log.info("exception - expected")    
            try:
                responses.append(tag.transceive(bytearray.fromhex(offhost_command_apdu), timeout = None))
            except Exception as error:
                log.info("exception - expected")    
            try: 
                responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex('A000000003000000')))
            except Exception as error:
                log.info("exception - expected")    
            try: 
                responses.append(tag.transceive(bytearray.fromhex(offhost_command_apdu), timeout = None))
            except Exception as error:
                log.info("exception - expected")    
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(access_aid)))
            #only this one shoudl work
            responses.append(tag.transceive(bytearray.fromhex(command_apdu)))
        elif test_name == 'large_aids':
            for i in (range(256)):
                responses.append(tag.transceive(bytearray.fromhex('F00102030414' + '{:02x}'.format(i) + '81'), timeout = None))
        elif test_name == 'dynamic_aids':
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(ppse_aid)))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(visa_aid)))
            responses.append(tag.transceive(bytearray.fromhex('80CA01F000'), timeout = 5000))
        elif test_name == 'prefix_payment_aids' or (wallet_role and test_name == 'prefix_payment_aids_2'):
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(ppse_aid)))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(mc_aid)))
            responses.append(tag.transceive(bytearray.fromhex('80CA01F000'), timeout = 5000))
        # elif test_name == 'prefix_payment_aids_2' and not wallet_role:
        elif test_name == 'dual_non_payment_prefix_other':
            transport_prefix_aid = 'F001020304'
            access_prefix_aid = 'F005060708'
            if not second_loop:
                try:
                    tag.transceive(bytearray.fromhex(select_transport_apdu), timeout = 1)
                except Exception as error:
                    second_loop = True
                    clf.close()
                    tag = None
                    continue
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(transport_prefix_aid + 'FFFF')))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(transport_prefix_aid + 'FFAA')))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(transport_prefix_aid + 'FFAABBCCDDEEFF')))
            responses.append(tag.transceive(bytearray.fromhex('80CA01F000'), timeout = 5000))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(access_prefix_aid + 'FFFF')))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(access_prefix_aid + 'FFAA')))
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex(access_prefix_aid + 'FFAABBCCDDEEFF')))
            responses.append(tag.transceive(bytearray.fromhex('80CA010000010203'), timeout = 5000))
            second_loop = False
        # elif test_name == 'other_prefix_aids':
            
        else:
            responses.append(tag.send_apdu(cla, ins, p1, p2, data=bytearray.fromhex('F005060708'), check_status=False))
            # responses.append(tag.transceive(bytearray.fromhex(offho), timeout = None))

        assert len(responses) == len(apdu_response_expected_sequence)
        for i in range(len(responses)):
            log.info("responses. Expected: %s actual: %s", responses[i].hex(), apdu_response_expected_sequence[i])
        #if all the same, return test pass. else, return false
        clf.close()
        




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
