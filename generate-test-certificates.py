# This file generates the required number of certificates for the PoC test

import blockvoke_bitcoin_rpc as BBR
import generate_certificate as GC
import revocation_logger as RL
import sys, argparse
import tqdm

TEST_LOGGER_CSV_FILE = "./working_dir/test_logs/TEST_{}.csv"
CERT_COUNTRY = "DE"
CERT_STATE = "Niedersachsen"
CERT_LOCATION = "Göttingen"
CERT_ORGANISATION = "Example {0}-{1} Organisation"
CERT_ORGANISATIONAL_UNIT = "Example {0}-{1} Organisational Unit"
CERT_COMMON_NAME = "example-{0}-{1}.org"
CERT_DNS = CERT_COMMON_NAME
CERT_EMAIL = "co@example-{0}-{1}.org"

def main(num, id):
    bv_test_logger = RL.RevocationLogger()
    print("Generating test Certificates")
    for i in tqdm.tqdm(range(1, num+1)):
        
        try:
            certificate_fingerprint, co_address_pubkey, ca_address_pubkey, cert_multisig_address = GC.generate_certificate(
            CERT_COUNTRY,
            CERT_STATE,
            CERT_LOCATION,
            CERT_ORGANISATION.format(id, i),
            CERT_ORGANISATIONAL_UNIT.format(id, i),
            CERT_COMMON_NAME.format(id, i),
            CERT_DNS.format(id, i),
            CERT_EMAIL.format(id, i))

        except Exception as E:
            print("Error generating Certificate {}".format(i))
            print(E)
            continue

        try:
            bv_test_logger.add_certificate(
                CERT_DNS.format(id, i),
                certificate_fingerprint,
                co_address_pubkey,
                ca_address_pubkey,
                cert_multisig_address)
        except Exception as E:
           print("Error logging generated Certificate {}".format(i)) 
           print(E)

    bv_test_logger.write(TEST_LOGGER_CSV_FILE.format(id))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Certificates for a BlockVoke test scenario")
    parser.add_argument("-n", "--num", type=int, help="Number of certificates to generate", required=True)
    parser.add_argument("-i", "--id", type=str, help="Test identifier", required=True)

    args = parser.parse_args()
    main(args.num, args.id)

