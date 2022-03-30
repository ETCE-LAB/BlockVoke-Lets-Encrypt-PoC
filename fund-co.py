# This file funds the COs addresses with the required amount of bitcoin for the PoC test

import blockvoke_bitcoin_rpc as BBR
import generate_certificate as GC
import revocation_logger as RL
import sys, argparse
import tqdm
from decimal import Decimal


TEST_LOGGER_CSV_FILE = "./working_dir/test_logs/TEST_{}.csv"

def main(id):
    bv_test_logger = RL.RevocationLogger()
    bv_test_logger.read(TEST_LOGGER_CSV_FILE.format(id))
    print("Fetching CO addresses")
    transaction_outputs = {}
    for cert_dns_name, log_value in tqdm.tqdm(bv_test_logger.certificates.items()):
        DNS = log_value["Cert DNS name"]

        if log_value["CO_funded"] == "True":
            print("CO `{}` is already funded, skipping".format(DNS))
            continue

        bv_test_logger.set_co_funded(DNS)
        btd_co = BBR.get_bitcoind_connection(DNS)
        btd_co.loadwallet(DNS)
        try:
            co_address = list(btd_co.getaddressesbylabel("{}-coaddress".format(DNS)).keys())[0]
            transaction_outputs[co_address] = Decimal("0.00000600") 
        except Exception as E:
            btd_co.unloadwallet(DNS)
            print(E)
            raise(E)
        else:
            btd_co.unloadwallet(DNS)


    btd = BBR.get_bitcoind_connection("testnetfaucet")
    btd.loadwallet("testnetfaucet")
    faucet_address = list(btd.getaddressesbylabel("testnetfaucet").keys())[0]

    try:
        rawtransaction = btd.createrawtransaction([], transaction_outputs)
        funded_rawtransaction = btd.fundrawtransaction(
            rawtransaction,
            {
                "changeAddress": faucet_address,
                "fee_rate":1
            })
        fee = funded_rawtransaction["fee"]
        signed_rawtransaction = btd.signrawtransactionwithwallet(
            funded_rawtransaction["hex"])

        decoded_rawtransaction = btd.decoderawtransaction(signed_rawtransaction["hex"])

        # txid = btd.sendrawtransaction(signed_rawtransaction["hex"])
        txid = 1
        print("Transaction `{0}` sent successfully with `{1}` outputs, spending `{2}` BTC as fees".format(txid, len(decoded_rawtransaction["vout"]), fee))
    except Exception as E:
        btd.unloadwallet("testnetfaucet")
        print("Exception Occurred:")
        raise(E)
    else:
        btd.unloadwallet("testnetfaucet")
        try:
            bv_test_logger.write(TEST_LOGGER_CSV_FILE.format(id))
        except Exception as E:
            print("Error saving revocation logger file")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fund CO addresses with the required amount of bitcoin for the PoC test")
    parser.add_argument("-i", "--id", type=str, help="Test identifier", required=True)
    args = parser.parse_args()
    main(args.id)
