"Put this inside revoke_certificate.py"

import blockvoke_bitcoin_rpc as BTD
from decimal import Decimal
import traceback
from pprint import pprint

############### Test Initialisation starts

# btd_ca = get_bitcoind_connection("ca-test")
# btd_ca.createwallet("ca-test")
# btd_ca.loadwallet("ca-test")

# btd_co = get_bitcoind_connection("co-test2")
# btd_co.loadwallet("co-test2")
# btd_co.createwallet("co-test2")

# ca_addr = btd_ca.getnewaddress("ca-test-address")
# ca_addr = list(btd_ca.getaddressesbylabel("ca-test-address").keys())[0]
# co_addr = btd_co.getnewaddress("co-test-address")
# co_addr = list(btd_co.getaddressesbylabel("co-test-address").keys())[0]

# ca_addr_info = btd_ca.getaddressinfo(ca_addr)
# co_addr_info = btd_co.getaddressinfo(co_addr)


# multisig_addr_info = btd_co.addmultisigaddress(1, [ca_addr_info["pubkey"],
#                                                    co_addr_info["pubkey"]],
#                                                "legacy")

# pprint(multisig_addr_info)

# get_bitcoin_from_faucet(co_addr, Decimal("0.00000600"))

# pprint(btd_co.getbalance())

###############  Test Initialisation complete

###############  Test Revocation

# (txfund, txrevoke) = create_revocation_transactions(btd_co,
#                                                     co_addr,
#                                                     multisig_addr_info,
#                                                     80*"1")

# print("################ TXFUND ##################")
# decoded_txfund = btd_co.decoderawtransaction(txfund["hex"])
# pprint(decoded_txfund)

# print("############### TXREVOKE ##################")
# decoded_txrevoke = btd_co.decoderawtransaction(txrevoke["hex"])
# pprint(decoded_txrevoke)


########## SEND TRANSACTIONS ############

# btd_co.sendrawtransaction(txfund["hex"])
# btd_co.sendrawtransaction(txrevoke["hex"])
