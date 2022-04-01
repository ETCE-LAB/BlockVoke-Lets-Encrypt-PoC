# This file sends revocation transactions and then waits and simultaneously logs revocation transactions are witnessed in the mempool or blockchain.

import blockvoke_bitcoin_rpc as BBR
import generate_certificate as GC
import revocation_logger as RL
import revoke_certificate as RC
import blockvoke_parser as BP
import sys, argparse
import tqdm
import threading
import time
from decimal import Decimal

TEST_LOGGER_CSV_FILE = "./working_dir/test_logs/TEST_{}.csv"

rev_logger_mutex = threading.Lock()
rev_logger = RL.RevocationLogger()

revoked=False
confirmed=False

def is_revoked(rlog) -> bool:
    return (rlog["Cert revocation type"] != "")
        

def communicate_revocation_transactions_from_mempool(rpcconnect):
    global rev_logger_mutex, rev_logger, revoked

    while(not revoked):
        print("Parsing transactions in mempool")
        new_revocations = BP.get_revocations(tqdm.tqdm(BP.get_tx_list_in_mempool(rpcconnect)))
        if new_revocations:
            rev_logger_mutex.acquire()
        else:
            continue

        for new_revocation in new_revocations:
            rev_logger.cert_revoked_from_mempool(new_revocation,"", "")
        rev_logger_mutex.release()
        time.sleep(1)
        
        
def communicate_mined_revocation_transactions(block_height, rpcconnect):
    global rev_logger_mutex, rev_logger, confirmed

    bh = block_height
    while(not confirmed):
        btd = BBR.get_bitcoind_connection(rpcconnect=rpcconnect)
        current_bh = btd.getblockchaininfo()["blocks"]
        if current_bh >= bh:
            print("Parsing transactions in blocks {}".format(list(range(bh, current_bh+1))))
            for blockh in tqdm.tqdm(range(bh, current_bh+1)):
                blocktime = btd.getblock(btd.getblockhash(blockh))["time"]
                new_revocations = BP.get_revocations(BP.get_tx_list_in_blockrange([blockh]))
                if new_revocation:
                    rev_logger_mutex.acquire()
                    for new_revocation in new_revocations:
                        rev_logger.cert_revoked_from_blockchain(new_revocation,
                                                                "",
                                                                "",
                                                                blockh,
                                                                blocktime)
                    rev_logger_mutex.release()
        bh = current_bh
        time.sleep(5)
       
def main(id,
         block_height,
         rpcconnect):
    global rev_logger_mutex, rev_logger, revoked, confirmed
    rev_logger.read(TEST_LOGGER_CSV_FILE.format(id))

    btd = BBR.get_bitcoind_connection(rpcconnect=rpcconnect)
    current_bh = btd.getblockchaininfo()["blocks"]

    block_height = current_bh if block_height is None else block_height
    
    t1 = threading.Thread(target=communicate_revocation_transactions_from_mempool, args=(rpcconnect,)).start()
    t2 = threading.Thread(target=communicate_mined_revocation_transactions, args=(block_height, rpcconnect)).start()

    print("Sending revocation transactions for {} certificates".format(len(rev_logger.certificates)))

    for DNS, cert_log in tqdm.tqdm(rev_logger.certificates.items()):
        if(cert_log["TX_Pair sent timestamp"] != ""):
            print("{0} was already revoked at {1}".format(DNS,
                                                          cert_log["TX_Pair sent timestamp"]))
            continue

        if(cert_log["CO_funded"] == "False"):
            print("{} has not been funded yet".format(DNS))
            continue

        txids = RC.revoke_certificate(DNS, 0, send=True) 

        if type(txids[0]) == str:
            rev_logger.tx_pair_sent(DNS, txids[0], txids[1])

    while(not revoked):
        rev_logger_mutex.acquire()
        if(all([is_revoked(rlog) for dns, rlog in rev_logger.certificates.items()])):
            print("All Certificates revoked and logged")
            rev_logger.write(TEST_LOGGER_CSV_FILE.format(id))
            revoked = True
        rev_logger_mutex.release()
 
    while(not confirmed):
        rev_logger_mutex.acquire()
        if(all([is_revoked(rlog) for dns, rlog in rev_logger.certificates.items()])):
            print("All Certificates revoked and transactions confirmed")
            rev_logger.write(TEST_LOGGER_CSV_FILE.format(id))
            confirmed = True
        rev_logger_mutex.release()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Revoke test certificates and wait for BlockVoke transactions")
    parser.add_argument("-i", "--id", type=str, help="Test identifier", required=True)
    parser.add_argument("-b", "--block-height", type=int, help="Block Height after which the script should check for Revocation Trasactions", required=False)
    parser.add_argument("-r", "--rpcconnect", type=str, help="Alternate rpcconnect ip address for fetching Bitcoin transactions")
    args = parser.parse_args()
    main(args.id, args.block_height, args.rpcconnect)
