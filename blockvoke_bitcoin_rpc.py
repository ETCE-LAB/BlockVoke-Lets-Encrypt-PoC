"""Python lib for all JSON-RPC calls to bitcoind for bitcoin related
 actions of BlockVoke

"""

import os

from bitcoinlib.services.bitcoind import BitcoindClient
from bitcoinlib.config.config import configparser
from bitcoinlib.services.authproxy import AuthServiceProxy
from decimal import Decimal

BITCOIND_CONFIG_FILE_PATH = os.path.join(os.path.realpath("config"), "bitcoin.conf")
ALTERNATE_BITCOIND_CONFIG_FILE_PATH = os.path.join(os.path.realpath("config"), "bitcoin.conf")

def get_help():
    print(get_bitcoind_connection().help())

def get_bitcoind_connection(wallet_name=None, rpcconnect=None) -> BitcoindClient:
    """Connects to the JSON RPC bitocind server
    
    `127.0.0.1` is used if rpcconnect is not specified.

    """

    bitcoind_ip = rpcconnect if rpcconnect != None else "127.0.0.1"

    cp = configparser.ConfigParser()

    cp.read(BITCOIND_CONFIG_FILE_PATH)

    bitcoind_rpcuser, bitcoind_rpcpass, bitcoind_rpcport = cp.get("rpc", "rpcuser"), cp.get("rpc", "rpcpassword"), cp.get("rpc", "rpcport")

    service_url = "http://{0}:{1}@{2}:{3}{4}".format(bitcoind_rpcuser,
                                                     bitcoind_rpcpass,
                                                     bitcoind_ip,
                                                     bitcoind_rpcport,
                                                     ("/wallet/{}".format(wallet_name) if wallet_name else ""))

    return AuthServiceProxy(service_url)

def __initialize_faucet__():
    """Creates a wallet with address that provides bitcoin to the CO's
    

    """
    btd = get_bitcoind_connection()
    btd.createwallet("testnetfaucet")

    # del btd

    # btd = get_bitcoind_connection(wallet_name="faucet")
    # faucet_address = btd.getnewaddress("faucetaddress")

    # print("New Faucet address: ", faucet_address)

    # btd.generatetoaddress(101, faucet_address)

    # unspent = btd.listunspent(100, 200, [faucet_address])

    btd.unloadwallet("testnetfaucet")

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

    For use in the testnet chain.
    
    Faucet should already be initialized

    """

    btd = get_bitcoind_connection("testnetfaucet")
    btd.loadwallet("testnetfaucet")

    faucet_address = list(btd.getaddressesbylabel("testnetfaucet").keys())

    unspent = btd.listunspent(1, 9999999, faucet_address)

    btd.unloadwallet("testnetfaucet")

    return unspent

def get_bitcoin_from_faucet2(address, amount):
    btd = get_bitcoind_connection("testnetfaucet")
    btd.loadwallet("testnetfaucet")
    btd.sendtoaddress(address, amount, fee_rate="1")
    # mine_blocks(1)
    btd.unloadwallet("testnetfaucet")

def get_bitcoin_from_faucet(address, amount):
    """Get some bitcoin from faucet

    Creates the transactions itself, and uses a fee_rate of 1sat/vB

    Faucet should already be initialized

    """
    btd = get_bitcoind_connection("testnetfaucet")
    btd.loadwallet("testnetfaucet")
    faucet_address = list(btd.getaddressesbylabel("testnetfaucet").keys())[0]

    try:

        rawtransaction = btd.createrawtransaction(
            [],
            {address:amount})

        funded_rawtransaction = btd.fundrawtransaction(
            rawtransaction,
            {
                "changeAddress":faucet_address,
                "fee_rate":1
            })

        print("Fee:", str(funded_rawtransaction["fee"]))
        
        signed_rawtransaction = btd.signrawtransactionwithwallet(
            funded_rawtransaction["hex"])

        # print("Signed Transaction: ", signed_rawtransaction,
        #       type(signed_rawtransaction))
        
        txid = btd.sendrawtransaction(signed_rawtransaction["hex"])
        
    except Exception as E:
        btd.unloadwallet("testnetfaucet")
        raise E

    btd.unloadwallet("testnetfaucet")

    return txid
