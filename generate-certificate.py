# Python lib to generate a `BlockVoke` Certificate

import subprocess, os, shutil
import blockvoke_bitcoin_rpc as bitcoin

CSR_OPENSSL_CNF = "oid_section = new_oids\n[ new_oids ]\nCO_Bitcoin_Pubkey=1.2.3.4\n\n[req]\ndistinguished_name = req_distinguished_name\n# attributes		= req_attributes\nreq_extensions = v3_req\nprompt = no\n\n[req_distinguished_name]\nC = {0}\nST = {1}\nL = {2}\nO = {3}\nOU = {4}\nCN = {5}\nCO_Bitcoin_Pubkey		= {6}\n[v3_req]\nsubjectAltName = @alt_names\n\n[alt_names]\nDNS.1 = {7}"

def create_CSR(country,
               state,
               location,
               organisation,
               organisational_unit,
               common_name,
               co_bitcoin_pubkey,
               DNS,
               working_dir="./working_dir",
               openssl_working_dir="./working_dir/openssl"):

    with open("{0}/openssl-{1}.cnf".format(openssl_working_dir, DNS), "w") as openssl_cnf:
        openssl_cnf.write(CSR_OPENSSL_CNF.format(country, state,
                                               location, organisation,
                                               organisational_unit,
                                               common_name,
                                               co_bitcoin_pubkey,
                                               DNS))

    ret = subprocess.run(["openssl", "req", "-newkey",
                          "rsa:2048", "-keyout",
                          "{0}/cert-keys/PRIVATEKEY-{1}.key".format(working_dir,
                                                                    DNS), "-out",
                          "{0}/csrs/CSR-{1}.csr".format(working_dir,
                                                        DNS), "-nodes", "-config",
                          "{0}/openssl-{1}.cnf".format(openssl_working_dir,
                                                       DNS)], capture_output=True)
    print(ret.stderr.decode())
    print(ret.stdout.decode())

    ret.check_returncode()

    subprocess.run(["openssl", "req", "-noout", "-text", "-in",
                    "{0}/csrs/CSR-{1}.csr".format(working_dir, DNS)])

def generate_certificate(country,
                         state,
                         location,
                         organisation,
                         organisational_unit,
                         common_name,
                         DNS,
                         email,
                         working_dir="./working_dir",
                         openssl_working_dir="./working_dir/openssl",
                         certbot_working_dir="./working_dir/certbot",
                         pebble_server="https://localhost:14000/dir",
                         bitcoin_wallet=None):

    """
    Generate Certificate (CO)
    
    1. Create a new address in an existing wallet
    2. Generates a CSR using openssl with the pubkey of new address (Unencrypted private key)
    3. Uses certbot to request for certificate generation from pebble ca
    """

    if bitcoin_wallet is None:
        bitcoin_wallet = DNS
        btd = bitcoin.get_bitcoind_connection(bitcoin_wallet)
        btd.createwallet(bitcoin_wallet)
    else:
        btd = bitcoin.get_bitcoind_connection(bitcoin_wallet)
        btd.loadwallet(bitcoin_wallet)

    try:
        new_address = btd.getnewaddress("{}-coaddress".format(bitcoin_wallet))
        new_address_pubkey = (btd.getaddressinfo(new_address))["pubkey"]
    except Exception as E:
        print("Could not generate a new address for the specified wallet")

        print(E)

    finally:
        btd.unloadwallet(bitcoin_wallet)
        del btd

    create_CSR(country,
               state,
               location,
               organisation,
               organisational_unit,
               common_name,
               new_address_pubkey,
               DNS,
               working_dir=working_dir,
               openssl_working_dir=openssl_working_dir)

    subprocess.run(["sudo", "certbot", "--non-interactive",
                    "--agree-tos", "--email", "'{}'".format(email),
                    "--no-eff-email", "--no-verify-ssl",
                    "--standalone",
                    "--config-dir={}/config".format(certbot_working_dir),
                    "--logs-dir={}/logs".format(certbot_working_dir),
                    "--work-dir={}/work".format(certbot_working_dir),
                    "--server={}".format(pebble_server), "register"])

    subprocess.run(["sudo", "certbot", "--non-interactive",
                    "--agree-tos", "--email", "'{}'".format(email),
                    "--no-eff-email", "--no-verify-ssl",
                    "--standalone",
                    "--config-dir={}/config".format(certbot_working_dir),
                    "--logs-dir={}/logs".format(certbot_working_dir),
                    "--work-dir={}/work".format(certbot_working_dir),
                    "--server={}".format(pebble_server), "certonly",
                    "--csr={0}/csrs/CSR-{1}.csr".format(working_dir,
                                                        DNS)])

    os.rename("0000_cert.pem",
              "{0}/certificates/{1}-cert.pem".format(working_dir, DNS))
    os.rename("0000_chain.pem",
              "{0}/certificates/{1}-inter-chain.pem".format(working_dir, DNS))
    os.rename("0001_chain.pem",
              "{0}/certificates/{1}-full-chain.pem".format(working_dir, DNS))

    subprocess.run(["openssl", "x509", "-noout", "-text", "-in",
                    "{0}/certificates/{1}-cert.pem".format(working_dir, DNS)])

    return new_address_pubkey
    

# generate_certificate("DE",
#                      "Niedersachsen",
#                      "Goettingen",
#                      "Example test Organisation2",
#                      "Example test2",
#                      "example-test2.org",
#                      "example-test2.org",
#                      "example@example-test2.org",
#                      working_dir="./working_dir",
#                      openssl_working_dir="./working_dir/openssl",
#                      certbot_working_dir="./working_dir/certbot",
#                      pebble_server="https://localhost:14000/dir",
#                      bitcoin_wallet=None)
