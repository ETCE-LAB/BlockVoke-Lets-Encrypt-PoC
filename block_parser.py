from blockvoke_bitcoin_rpc import get_bitcoind_connection

import time

def get_block_tx_list(height):
    btd = get_bitcoind_connection()

    blockhash = btd.getblockhash(height)
    txids = btd.getblock(blockhash)["tx"]

    return [btd.getrawtransaction(txid, 1, blockhash) for txid in txids]

def get_tx_list_in_blockrange(blockrange):
    return [tx for block_tx_list in [get_block_tx_list(height) for height in blockrange] for tx in block_tx_list] 

def is_OP_RETURN_OUTPUT(output):
    return output["scriptPubKey"]["type"] == "nulldata" and output["scriptPubKey"]["asm"][10:28] == "BlockVoke".encode().hex()

def get_OP_RETURN(tx):
    return [output["scriptPubKey"]["asm"][10:] for output in filter(is_OP_RETURN_OUTPUT, tx["vout"])]

def get_revocations(tx_list):
    return [OP_RETURN[0] for OP_RETURN in [get_OP_RETURN(tx) for tx in tx_list] if OP_RETURN]

