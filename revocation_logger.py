"""Revocation logging and datastructure for test-scenarios"""
import logging
import csv
import datetime
import time
from collections import defaultdict

REVOCATION_LOG_FIELDNAMES = ["Cert DNS name",
                             "Cert gen timestamp",
                             "Cert fingerprint",
                             "CO Bitcoin pubkey",
                             "CA Bitcoin pubkey",
                             "Cert multisig address",
                             "CO_funded",
                             "TX_Pair sent timestamp",
                             "Cert revocation type",
                             "Cert revocation timestamp",
                             "Cert revocation blockheight",
                             "Cert revocation blocktime",
                             "Cert revocation fees",
                             "Cert revocation funds",
                             "TX:Fund txid",
                             "TX:Revoke txid"]

def unixtimestampnow():
    return int(time.mktime(datetime.datetime.now().timetuple())) 
    
class RevocationLogger(object):
    def __init__(self):
        self.certificates = {}
        self.__fingerprint_16_index__ = {}
        logging.basicConfig(format="%(asctime)s: %(message)s",
                            level=logging.NOTSET,
                            datefmt="%x %X %Z")
    def read(self, csvfile_path):
        with open(csvfile_path, "r", newline='') as  csvfile:
            certificates = csv.DictReader(csvfile)
            for certificate in certificates:
                self.certificates[certificate["Cert DNS name"]] = certificate
                self.__fingerprint_16_index__[certificate["Cert fingerprint"][:32]] = certificate["Cert DNS name"]
            logging.info("Reading `{0}` certificate entries from `{1}` ".format(len(self.certificates), csvfile_path))
        
    def write(self, csvfile_path):
        with open(csvfile_path, "w", newline='') as csvfile:
            csvfilewriter = csv.DictWriter(csvfile,
                                            fieldnames=REVOCATION_LOG_FIELDNAMES,
                                            quoting=csv.QUOTE_NONNUMERIC)
            csvfilewriter.writeheader()

            def remove_if_tuple(tup):
                return tup[0] if type(tup) == tuple else tup

            for k,v in self.certificates.items():
                csvfilewriter.writerow(
                    {log_key:remove_if_tuple(log_value) for log_key,log_value in v.items()})

            logging.info("Wrote `{0}` certificate entries to `{1}` ".format(len(self.certificates), csvfile_path))

    def add_certificate(self, cert_dns_name,
                        cert_fingerprint,
                        co_bitcoin_pubkey,
                        ca_bitcoin_pubkey,
                        cert_multisig_address):

        if cert_dns_name in self.certificates:
            logging.error("Certificate for `{}` is already in the RevocationLogger, skipping".format(cert_dns_name))
            return

        self.certificates[cert_dns_name] = defaultdict(lambda:'')
        self.certificates[cert_dns_name]["Cert DNS name"] = cert_dns_name
        self.certificates[cert_dns_name]["Cert gen timestamp"] = unixtimestampnow()
        self.certificates[cert_dns_name]["Cert fingerprint"] = cert_fingerprint,
        self.__fingerprint_16_index__[cert_fingerprint[:32]] = cert_dns_name
        self.certificates[cert_dns_name]["CO Bitcoin pubkey"] = co_bitcoin_pubkey,
        self.certificates[cert_dns_name]["CA Bitcoin pubkey"] = ca_bitcoin_pubkey,
        self.certificates[cert_dns_name]["Cert multisig address"] = cert_multisig_address
        self.certificates[cert_dns_name]["CO_funded"] = "False"
        logging.info("Certificate for `{}` added to RevocationLogger".format(cert_dns_name))

    def set_co_funded(self, cert_dns_name):
        try:
            if(self.certificates[cert_dns_name]["CO_funded"]== "False"):
                self.certificates[cert_dns_name]["CO_funded"] = "True"
                # logging.info("CO `{}` is funded".format(cert_dns_name))
            else:
                logging.error("CO `{}` funding is already complete".format(cert_dns_name))
                
        except Exception as E:
            logging.exception(E)

    def tx_pair_sent(self, cert_dns_name, tx_fund_txid, tx_revoke_txid):
        try:
            if(self.certificates[cert_dns_name]["TX_Pair sent timestamp"]== ''):
                self.certificates[cert_dns_name]["TX_Pair sent timestamp"] = unixtimestampnow()
                self.certificates[cert_dns_name]["TX:Fund txid"] = tx_fund_txid
                self.certificates[cert_dns_name]["TX:Revoke txid"] = tx_revoke_txid
            else:
                logging.error(
                    "CO `{0}` revocation transactions were possibly already sent, skipping. Current values (timestamp, txfund txid, txrevoke txid): ({1},{2},{3})".format(cert_dns_name,
                                                                                                                                                                self.certificates[cert_dns_name]["TX_Pair sent timestamp"],
                                                                                                                                                                self.certificates[cert_dns_name]["TX:Fund txid"],
                                                                                                                                                                self.certificates[cert_dns_name]["TX:Revoke txid"]))
                

        except Exception as E:
            logging.exception(E)

    def cert_revoked_from_mempool(self,
                                  cert_fingerprint_16,
                                  cert_revocation_fees,
                                  cert_revocation_funds):
        try:
            if cert_fingerprint_16 not in self.__fingerprint_16_index__:
                logging.error(
                    "Certificate with fingerprint starting with `{}`, witnessed in mempool, not found in logger, skipping".format(cert_fingerprint_16))
                return
            cert_dns_name = self.__fingerprint_16_index__[cert_fingerprint_16]
            if(self.certificates[cert_dns_name]["Cert revocation timestamp"]==''):
                self.certificates[cert_dns_name]["Cert revocation timestamp"] = unixtimestampnow()
                self.certificates[cert_dns_name]["Cert revocation type"] = "mempool"
                self.certificates[cert_dns_name]["Cert revocation fees"] = cert_revocation_fees
                self.certificates[cert_dns_name]["Cert revocation funds"] = cert_revocation_funds
                logging.info("`{}` revoked from mempool".format(cert_dns_name))
            else:
                logging.error(
                    "MEMPOOL:`{0}` was already revoked via `{1}`, skipping".format(cert_dns_name,
                                                                           self.certificates[cert_dns_name]["Cert revocation type"]))
                    
                
        except Exception as E:
            logging.exception(E)

    def cert_revoked_from_blockchain(self,
                                     cert_fingerprint_16,
                                     cert_revocation_fees,
                                     cert_revocation_funds,
                                     cert_revocation_blockheight,
                                     cert_revocation_blocktime):
        try:
            if cert_fingerprint_16 not in self.__fingerprint_16_index__:
                logging.error(
                    "Certificate with fingerprint starting with `{}`, witnessed on blockchain, not found in logger, skipping".format(cert_fingerprint_16))
                return
            cert_dns_name = self.__fingerprint_16_index__[cert_fingerprint_16]
            if(self.certificates[cert_dns_name]["Cert revocation timestamp"]==''):
                self.certificates[cert_dns_name]["Cert revocation timestamp"] = unixtimestampnow()
                self.certificates[cert_dns_name]["Cert revocation type"] = "blockchain"
                self.certificates[cert_dns_name]["Cert revocation fees"] = cert_revocation_fees
                self.certificates[cert_dns_name]["Cert revocation funds"] = cert_revocation_funds
                self.certificates[cert_dns_name]["Cert revocation blockheight"] = cert_revocation_blockheight
                self.certificates[cert_dns_name]["Cert revocation blocktime"] = cert_revocation_blocktime
                logging.info("`{}` revoked and transactions confirmed in blockchain".format(cert_dns_name))
            else:
                self.certificates[cert_dns_name]["Cert revocation blockheight"] = cert_revocation_blockheight
                self.certificates[cert_dns_name]["Cert revocation blocktime"] = cert_revocation_blocktime
                logging.info("Revocation transactions for `{}` confirmed in blockchain".format(cert_dns_name))
                logging.error(
                    "BLOCK_TX:`{0}` was already revoked via `{1}`, skipping".format(cert_dns_name,
                                                                           self.certificates[cert_dns_name]["Cert revocation type"]))
                
        except Exception as E:
            logging.exception(E)
