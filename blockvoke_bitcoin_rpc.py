"""Python lib for all JSON-RPC calls to bitcoind for bitcoin related
 actions of BlockVoke

"""

import os

from bitcoinlib.services.bitcoind import BitcoindClient
from bitcoinlib.config.config import configparser
from bitcoinlib.services.authproxy import AuthServiceProxy
from decimal import Decimal

BITCOIND_CONFIG_FILE_PATH = os.path.join(os.path.realpath("config"), "bitcoin.conf")

def get_help():
    print(get_bitcoind_connection().help())

def get_bitcoind_connection(wallet_name=None) -> BitcoindClient:
    """Connects to the JSON RPC bitocind server

    """

    cp = configparser.ConfigParser()

    cp.read(BITCOIND_CONFIG_FILE_PATH)

    bitcoind_rpcuser, bitcoind_rpcpass, bitcoind_rpcport = cp.get("rpc", "rpcuser"), cp.get("rpc", "rpcpassword"), cp.get("rpc", "rpcport")

    service_url = "http://{0}:{1}@127.0.0.1:{2}{3}".format(bitcoind_rpcuser,
                                                           bitcoind_rpcpass,
                                                           bitcoind_rpcport,
                                                           ("/wallet/{}".format(wallet_name) if wallet_name else ""))

    return AuthServiceProxy(service_url)

def __initialize_faucet__():
    """Creates a wallet with address that can be a faucet for regtest
    chains

    """
    btd = get_bitcoind_connection()
    btd.createwallet("faucet")

    del btd

    btd = get_bitcoind_connection(wallet_name="faucet")
    faucet_address = btd.getnewaddress("faucetaddress")

    print("New Faucet address: ", faucet_address)

    btd.generatetoaddress(101, faucet_address)

    unspent = btd.listunspent(100, 200, [faucet_address])

    btd.unloadwallet("faucet")

    return unspent

def __initialize_ca__():
    """Creates a wallet by the name ca0 if it does not exists, or simply loads it

    """
    btd = get_bitcoind_connection()
    try:
        btd.createwallet("ca0")
    except Exception as E:
        print("Wallet already exists, attempting to load wallet")
        btd.loadwallet("ca0")
    finally:
        print("CA wallet loaded")

def __initialize_miner__():
    """Creates a miner who exclusively mines blocks to their addresses

    """
    btd = get_bitcoind_connection()
    btd.createwallet("miner")

    del btd

    btd = get_bitcoind_connection(wallet_name="miner")
    miner_address = btd.getnewaddress("mineraddress")

    print("New Miner address: ", miner_address)

    btd.unloadwallet("miner")

def __initialize_all__():
    __initialize_faucet__()
    __initialize_miner__()
    __initialize_ca__()

def mine_blocks(num=10):
   """Mines some blocks to the miner's address

   """ 
   btd = get_bitcoind_connection("miner")
   btd.loadwallet("miner")
   miner_address = list(btd.getaddressesbylabel("mineraddress").keys())[0]

   btd.generatetoaddress(num, miner_address)
   btd.unloadwallet("miner")

def get_faucet_info():
    """Get the address of faucet and unspent balance

    For use in a regtest chain.
    
    Faucet should already be initialized

    """

    btd = get_bitcoind_connection("faucet")
    btd.loadwallet("faucet")

    faucet_address = list(btd.getaddressesbylabel("faucetaddress").keys())

    unspent = btd.listunspent(1, 2000, faucet_address)

    btd.unloadwallet("faucet")

    return unspent

def get_bitcoin_from_faucet2(address, amount):
    btd = get_bitcoind_connection("faucet")
    btd.loadwallet("faucet")
    btd.sendtoaddress(address, amount)
    mine_blocks(1)
    btd.unloadwallet("faucet")

def get_bitcoin_from_faucet(address, amount, fees=Decimal("0.00001")):
    """Get some bitcoin from faucet
    
    For use in a regtest chain.
    
    Faucet should already be initialized

    """
    faucet_unspent = get_faucet_info()
    btd = get_bitcoind_connection("faucet")
    btd.loadwallet("faucet")

    try:
        faucet_balance = faucet_unspent[0]["amount"] - Decimal(amount) - Decimal(fees)
        recipient_balance = Decimal(amount)
        rawtransaction = btd.createrawtransaction(
            [{
                "txid": faucet_unspent[0]["txid"],
                "vout": faucet_unspent[0]["vout"]
            }],
            [{
                faucet_unspent[0]["address"]:faucet_balance
            },
            {
                address:recipient_balance
            }])
        
        # print("Raw Transaction: ", rawtransaction)
        
        signed_rawtransaction = btd.signrawtransactionwithwallet(rawtransaction)

        # print("Signed Transaction: ", signed_rawtransaction,
        #       type(signed_rawtransaction))
        
        txid = btd.sendrawtransaction(signed_rawtransaction["hex"])
        
        mine_blocks(1)
        
    except Exception as E:
        print(faucet_unspent)
        btd.unloadwallet("faucet")
        raise E

    btd.unloadwallet("faucet")

    return txid


# btd_ca = get_bitcoind_connection("ca-test")
# btd_ca.createwallet("ca-test")

# btd_co = get_bitcoind_connection("co-test")
# btd_co.createwallet("co-test")

# ca_addr = btd_ca.getnewaddress()

# co_addr = btd_co.getnewaddress()

# ca_addr_info = btd_ca.getaddressinfo(ca_addr)
# co_addr_info = btd_co.getaddressinfo(co_addr)


# multisig_addr_info = btd_co.addmultisigaddress(1, [ca_addr_info["pubkey"],
#                                                    co_addr_info["pubkey"]],
#                                                "legacy")


# get_bitcoin_from_faucet2(co_addr, Decimal("0.00012"))



############### Test Initialization complete 


###############  Test Transactions


# co_unspent = btd_co.listunspent()[0]

# txfund_transaction = btd_co.createrawtransaction(
#     [{
#         "txid":co_unspent["txid"],
#         "vout":co_unspent["vout"]
#     }],
#     {multisig_addr_info["address"]:Decimal("0.00011")})

# txfund_transaction_signed = btd_co.signrawtransactionwithkey(txfund_transaction,
#                                                              [btd_co.dumpprivkey(co_addr)])


################# Test TxFund Transaction Complete

# txfund_transaction_decoded = btd_co.decoderawtransaction(txfund_transaction_signed["hex"])

# txrevoke_transaction = btd_co.createrawtransaction(
#     [{
#         "txid":txfund_transaction_decoded["txid"],
#         "vout":0,
#         "scriptPubKey":txfund_transaction_decoded["vout"][0]["scriptPubKey"]["hex"],
#         "redeemScript":multisig_addr_info["redeemScript"]
#     }],
#     {co_addr:Decimal("0.0001")})

# txrevoke_transaction_signed = btd_co.signrawtransactionwithkey(txrevoke_transaction,
#                                                                [btd_co.dumpprivkey(co_addr)],
#                                                                [{"txid":txfund_transaction_decoded["txid"],
#                                                                  "vout":0,
#                                                                  "scriptPubKey":txfund_transaction_decoded["vout"][0]["scriptPubKey"]["hex"],
#                                                                  "redeemScript":multisig_addr_info["redeemScript"],
#                                                                  "amount":Decimal("0.00011")}])

################## Test TxRevoke Transaction Complete

# txfund_txid = btd_co.sendrawtransaction(txfund_transaction_signed["hex"])

################## Test TxFund Transaction Sent

# txrevoke_txid = btd_co.sendrawtransaction(txrevoke_transaction_signed["hex"])

################### Test TxRevoke Transaction Sent

