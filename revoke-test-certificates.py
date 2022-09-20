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
testid = None

revoked=False
confirmed=False

def is_revoked(rlog) -> bool:
    return (rlog["Cert revocation type"] != "")

def is_mined(rlog) -> bool:
    return (rlog["Cert revocation blocktime"] != "")

def communicate_revocation_transactions_from_mempool(rpcconnect):
    global rev_logger_mutex, rev_logger, revoked, testid

    while(not revoked):
        new_revocations = BP.get_revocations(BP.get_tx_list_in_mempool(rpcconnect))
        if new_revocations:
            rev_logger_mutex.acquire()
            print("Parsing {} revocation transactions in mempool".format(len(new_revocations)))
        else:
            continue

        for new_revocation in new_revocations:
            rev_logger.cert_revoked_from_mempool(new_revocation,"", "")

        if(all([is_revoked(rlog) for dns, rlog in rev_logger.certificates.items()])):
            revoked = True
            rev_logger.write(TEST_LOGGER_CSV_FILE.format(testid))
        rev_logger_mutex.release()
        time.sleep(1)
        
def communicate_mined_revocation_transactions(block_height, rpcconnect):
    global rev_logger_mutex, rev_logger, confirmed, testid

    bh = block_height
    while(not confirmed):
        btd = BBR.get_bitcoind_connection(rpcconnect=rpcconnect)
        current_bh = btd.getblockchaininfo()["blocks"]
        if current_bh > bh:
            print("Parsing transactions in blocks {}".format(list(range(bh, current_bh))))
            rev_logger_mutex.acquire()
            for blockh in range(bh, current_bh+1):
                blocktime = btd.getblock(btd.getblockhash(blockh))["time"]
                new_revocations = BP.get_revocations(BP.get_tx_list_in_blockrange([blockh]))
                if new_revocations:
                    for new_revocation in new_revocations:
                        rev_logger.cert_revoked_from_blockchain(new_revocation,
                                                                "",
                                                                "",
                                                                blockh,
                                                                blocktime)
            if(all([is_mined(rlog) for dns, rlog in rev_logger.certificates.items()])):
                confirmed = True
                revoked = True
                rev_logger.write(TEST_LOGGER_CSV_FILE.format(testid))
            rev_logger_mutex.release()
            bh = current_bh
        time.sleep(5)
       
def main(tid,
         block_height,
         rpcconnect):
    global rev_logger_mutex, rev_logger, revoked, confirmed, testid
    testid = tid
    rev_logger.read(TEST_LOGGER_CSV_FILE.format(testid))

    num_revoked = 0
    num_confirmed = 0

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
        rev_logger.tx_pair_sent(DNS, txids[0], txids[1])

    bar_revoked = tqdm.tqdm(total=len(rev_logger.certificates),
                           desc="Certificates Revoked")
    bar_confirmed = tqdm.tqdm(total=len(rev_logger.certificates),
                              desc="Revocation Transactions Confirmed")
    
    while(not (revoked and confirmed)):
        time.sleep(2)
        rev_logger_mutex.acquire()
        total_revoked =[is_revoked(rlog) for dns, rlog in rev_logger.certificates.items()].count(True)
        total_confirmed =[is_mined(rlog) for dns, rlog in rev_logger.certificates.items()].count(True)
        if ((total_revoked > num_revoked) # and (not revoked)
            ):
            bar_revoked.update(total_revoked - num_revoked)
            num_revoked = total_revoked

        if ((total_confirmed > num_confirmed) # and (not confirmed)
            ):
            bar_confirmed.update(total_confirmed - num_confirmed)
            num_confirmed = total_confirmed
        # else:
        #     print(bar_confirmed)

        rev_logger_mutex.release()
            
    print("All Certificates revoked and Transactions confirmed successfully")

    # rev_logger_mutex.release()
    # while(not confirmed):
    #     time.sleep(10)
    # rev_logger_mutex.acquire()
    # print("All Certificates revoked and transactions confirmed")
    # rev_logger_mutex.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Revoke test certificates and wait for BlockVoke transactions")
    parser.add_argument("-i", "--testid", type=str, help="Test identifier", required=True)
    parser.add_argument("-b", "--block-height", type=int, help="Block Height after which the blocks are parsed for Revocation Trasactions. (Only blocks above BLOCK_HEIGHT will be parsed)", required=False)
    parser.add_argument("-r", "--rpcconnect", type=str, help="Alternate rpcconnect ip address for fetching mempool transactions and newly mined blocks")
    args = parser.parse_args()
    main(args.testid, args.block_height, args.rpcconnect)
