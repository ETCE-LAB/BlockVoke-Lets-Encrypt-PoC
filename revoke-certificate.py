# Python lib to revoke a `BlockVoke` certificate (as CO)

import os
from pprint import pprint
from datetime import datetime
import traceback
from decimal import Decimal
from cryptography.x509 import load_pem_x509_certificate, ObjectIdentifier, SubjectAlternativeName, DNSName
from blockvoke_bitcoin_rpc import get_bitcoind_connection, get_bitcoin_from_faucet

def create_txfund_transaction(bitcoind_rpcproxy_connection, coaddress, cert_multisig):
    # co_unspent = bitcoind_rpcproxy_connection.listunspent()[0]

    txfund_transaction = bitcoind_rpcproxy_connection.createrawtransaction(
        [# {
        # "txid":co_unspent["txid"],
        # "vout":co_unspent["vout"]
        # }
        # Since fundrawtransaction will add the coaddress automatically
         ],
        {cert_multisig["address"]:Decimal("0.00000477")})

    funded_txfund_transaction = bitcoind_rpcproxy_connection.fundrawtransaction(
        txfund_transaction,
        {
            "fee_rate":1,
            "changeAddress":coaddress,
        })

    signed_txfund_transaction = bitcoind_rpcproxy_connection.signrawtransactionwithkey(
        funded_txfund_transaction["hex"],
        [bitcoind_rpcproxy_connection.dumpprivkey(coaddress)])

    return signed_txfund_transaction

def create_OP_RETURN_script(BlockVokeCertificate, revocationCode) -> str:
    """Creates OP_RETURN data represented as a hex string
    
    Assumes that the CO is revoking
    """
    blockvoke_identifier = "BlockVoke".encode().hex() + "00"

    certificate_fingerprint = BlockVokeCertificate.fingerprint(BlockVokeCertificate.signature_hash_algorithm).hex()[:32]

    certificate_days_since = format((BlockVokeCertificate.not_valid_before - datetime(2020, 2, 2)).days, '08x')

    revocationCode_hex = format(revocationCode, "02x")

    return blockvoke_identifier + certificate_fingerprint + certificate_days_since + revocationCode_hex

def create_txrevoke_transaction(bitcoind_rpcproxy_connection,
                                coaddress,
                                cert_multisig,
                                OP_RETURN,
                                txfund_transaction):
    cert_multisig_address = cert_multisig["address"]

    decoded_txfund_transaction = bitcoind_rpcproxy_connection.decoderawtransaction(txfund_transaction["hex"])


    # txrevoke_transaction = bitcoind_rpcproxy_connection.createrawtransaction(
    #     [{
    #         "txid":decoded_txfund_transaction["txid"],
    #         "vout":0,
    #         "scriptPubKey":decoded_txfund_transaction["vout"][0]["scriptPubKey"]["hex"],
    #         "redeemScript":cert_multisig["redeemScript"]
    #     }],
    #     {coaddress:decoded_txfund_transaction["vout"][0]["value"],
    #      "data":OP_RETURN})

    # pprint(bitcoind_rpcproxy_connection.decoderawtransaction(txrevoke_transaction))

    # funded_txrevoke_transaction = bitcoind_rpcproxy_connection.fundrawtransaction(
    #     txrevoke_transaction,
    #     {
    #         "fee_rate":"1",
    #         "subtractFeeFromOutputs":[0] # Subtract the fee from the coaddress output
    #     })

    txrevoke_transaction = bitcoind_rpcproxy_connection.createrawtransaction(
        [{
            "txid":decoded_txfund_transaction["txid"],
            "vout":0,
            "scriptPubKey":decoded_txfund_transaction["vout"][0]["scriptPubKey"]["hex"],
            "redeemScript":cert_multisig["redeemScript"]
        }],
        {coaddress:decoded_txfund_transaction["vout"][0]["value"]-Decimal("0.00000170"),
         "data":OP_RETURN})

    signed_txrevoke_transaction = bitcoind_rpcproxy_connection.signrawtransactionwithkey(
        txrevoke_transaction,
        [bitcoind_rpcproxy_connection.dumpprivkey(coaddress)],
        [{"txid":decoded_txfund_transaction["txid"],
          "vout":0,
          "scriptPubKey":decoded_txfund_transaction["vout"][0]["scriptPubKey"]["hex"],
          "redeemScript":cert_multisig["redeemScript"],
          "amount":decoded_txfund_transaction["vout"][0]["value"]}])
    
    return signed_txrevoke_transaction

def create_revocation_transactions(bitcoind_rpcproxy_connection,
                                   coaddress,
                                   cert_multisig,
                                   OP_RETURN):
    txfund_transaction = create_txfund_transaction(
        bitcoind_rpcproxy_connection,
        coaddress,
        cert_multisig)

    txrevoke_transaction = create_txrevoke_transaction(
        bitcoind_rpcproxy_connection,
        coaddress,
        cert_multisig,
        OP_RETURN,
        txfund_transaction)

    return txfund_transaction, txrevoke_transaction

def revoke_certificate(DNS,
                       revocationCode,
                       working_dir="./working_dir",
                       bitcoin_wallet=None,
                       send=False):

    """Revoke a certificate using the BlockVoke protocol

    """

    BlockVokeCertificate = None
    with open(os.path.join(working_dir,
                           "certificates",
                           "{}-cert.pem".format(DNS)), "rb") as certificate_file:
        
        BlockVokeCertificate = load_pem_x509_certificate(certificate_file.read())

    cert_multisig_address = BlockVokeCertificate.extensions.get_extension_for_oid(ObjectIdentifier("1.2.3.4")).value.value # Temporary BlockVoke ObjectIdentifier
    ca_address_pubkey_hex = BlockVokeCertificate.extensions.get_extension_for_oid(ObjectIdentifier("1.2.3.5")).value.value # Temporary CA Bitcoin Address Pubkey ObjectIdentifier

    print("Certificate Multisignature address: ", cert_multisig_address)
    print("CA Address Pubkey: ", ca_address_pubkey_hex)

    if bitcoin_wallet==None:
        bitcoin_wallet=DNS

    btd = get_bitcoind_connection(bitcoin_wallet)
    btd.loadwallet(bitcoin_wallet)

    txids = (None, None)
    txfund_transaction, txrevoke_transaction = None, None

    try:
        coaddress = list(btd.getaddressesbylabel("{}-coaddress".format(DNS)).keys())[0]

        coaddress_info = btd.getaddressinfo(coaddress)

        co_address_pubkey_hex = coaddress_info["pubkey"]
        print("CO Address Pubkey: ", co_address_pubkey_hex)

        pubkey1, pubkey2 = co_address_pubkey_hex, ca_address_pubkey_hex.decode()

        if co_address_pubkey_hex.encode() < ca_address_pubkey_hex:
            pubkey2, pubkey1 = co_address_pubkey_hex, ca_address_pubkey_hex.decode()

        cert_multisig = btd.addmultisigaddress(1, [pubkey1, pubkey2], "legacy")

        if cert_multisig_address.decode() != cert_multisig["address"]:
            raise Exception("Error: Generated Multisig address '{0}' != '{1}'".format(cert_multisig_address.decode(), cert_multisig["address"]))

        OP_RETURN = create_OP_RETURN_script(BlockVokeCertificate, revocationCode)

        txfund_transaction, txrevoke_transaction = create_revocation_transactions(
            btd,
            coaddress,
            cert_multisig,
            OP_RETURN)

        if not send:
            txids = (btd.sendrawtransaction(txfund_transaction["hex"]),
                     btd.sendrawtransaction(txrevoke_transaction["hex"]))

    except Exception as E:
        print("Unable to Revoke BlockVoke Certificate:")
        traceback.print_exception(type(E), E, E.__traceback__)
    finally:
        btd.unloadwallet(bitcoin_wallet)

    return (txids if not send else (txfund_transaction, txrevoke_transaction))
