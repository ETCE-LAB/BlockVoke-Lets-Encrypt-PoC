
# Table of Contents

1.  [Dependencies](#orge473ae4)
    1.  [Python Dependencies](#orga624805)
    2.  [Golang](#org408a3d8)
    3.  [Bitcoind](#org1e98978)
    4.  [OpenSSL](#orga7fa5fa)
2.  [Cloning](#orgbc0f93c)
3.  [Building the pebble ACME test server](#org47a5e5a)
4.  [Initialzing the Bitcoin nodes](#orgd7077fe)
5.  [Initializing the BlockVoke PoC bitcoin wallets](#orgd39bde7)
6.  [Running the BlockVoke test](#org9e0de73)
    1.  [Preparation](#org8e44737)
    2.  [Start the pebble ACME server](#org591dd58)
    3.  [Generate Certificates](#org405140d)
    4.  [Fund CO addresses](#org61b9a96)
    5.  [Revoke Test Certificates](#org67eb0d4)

This repository holds the scripts and code used to implement the proof-of-concept implementation of BlockVoke.


<a id="orge473ae4"></a>

# Dependencies


<a id="orga624805"></a>

## Python Dependencies

1.  [bitcoinlib](https://pypi.org/project/bitcoinlib/)
2.  [tqdm](https://pypi.org/project/tqdm/)
3.  [certbot](https://pypi.org/project/certbot/)


<a id="org408a3d8"></a>

## Golang

[Install and setup golang](https://go.dev/doc/install)


<a id="org1e98978"></a>

## Bitcoind

[Install bitcoind](https://en.bitcoinwiki.org/wiki/Bitcoind)


<a id="orga7fa5fa"></a>

## OpenSSL

[Install OpenSSL](https://www.openssl.org/)


<a id="orgbc0f93c"></a>

# Cloning

Please run the following to clone the testnet branch of this repository and the pebble sub-module

    git clone --recursive --branch testnet https://github.com/ETCE-LAB/BlockVoke-Lets-Encrypt-PoC.git


<a id="org47a5e5a"></a>

# Building the pebble ACME test server

The following will build the pebble ACME testserver and place the executables in your GOPATH All dependencies of the pebble test server would be installed automatically.

    cd pebble
    go install -v ./cmd/pebble/...


<a id="orgd7077fe"></a>

# Initialzing the Bitcoin nodes

Create a \`bitcoin.conf\` file with contents such as the following:

    
    # Options only for mainnet
    [main]
    
    # Options only for testnet
    [test]
    txindex=0
    debug=1
    rpcallowip=<IP Address1>
    rpcallowip=0.0.0.0/0
    rpcbind=127.0.0.1
    rpcbind=<IP Address2>
    rpcport=18443
    rpcuser=yourusername
    rpcpassword=yourpassword
    
    # Options only for regtest
    [regtest]
    
    [rpc]
    rpcport=18443
    rpcuser=yourusername
    rpcpassword=yourpassword
    fallbackfee=0.00001

Use an appropriate username and password.

The \`rpcbind\` and \`rpcallowip\` are used so that two bitcoind nodes are used to run the test.

Place a copy of the \`bitcoin.conf\` file in \`BlockVoke-Lets-Encrypt-PoC/config/\`.

Sync at least one bitcoind nodeas follows:

    bitcoind -conf=<path to bitcoin.conf> -server=1 -testnet

This could take several hours, depending on your internet connection


<a id="orgd39bde7"></a>

# Initializing the BlockVoke PoC bitcoin wallets

Once the testnet node has synced, and is still running, please run the following in another terminal on the same machine:

    python blockvoke_bitcoin_rpc.py

This will initialize and load a CA and display a new testnetfaucet address.

Please request some tokens from a bitcoin testnet faucet of your choice to this displayed address.  Depending on how many certificates are required for your test scenario, request 0.00000600 BTC per certificate.

Please also keep the bitcoind server online throughout this process. If for any reason, the node must be shut down, please run the following python script to reload the CA wallet:

    from blockvoke_bitcoin_rpc import __initialize_ca__
    
    __initialize_ca__()


<a id="org9e0de73"></a>

# Running the BlockVoke test


<a id="org8e44737"></a>

## Preparation

Run the following in preparation for the test:

    cd BlockVoke-Lets-Encrypt-PoC
    mkdir working_dir
    cd working_dir
    mkdir cert-keys certbot certificates csrs openssl test_logs
    cd certbot
    mkdir config logs work


<a id="org591dd58"></a>

## Start the pebble ACME server

    PEBBLE_VA_ALWAYS_VALID=1 <Path to pebble executable directory>/pebble -config <Path to BlockVoke-Lets-Encrypt-PoC directory>/pebble/test/config/pebble-config.json

Please note that if this server is shut down, then you must remove the
contents of the certbot config directory like so:

    sudo rm -rf working_dir/certbot/config/*


<a id="org405140d"></a>

## Generate Certificates

Making sure that the Bitcoind node is running on the same machine,
generate the requisite number of certificates for your test scenario,
choosing a test-id.

    usage: python generate-test-certificates.py [-h] -n NUM -i ID
    
    Generate Certificates for a BlockVoke test scenario
    
    options:
      -h, --help         show this help message and exit
      -n NUM, --num NUM  Number of certificates to generate
      -i ID, --id ID     Test identifier


<a id="org61b9a96"></a>

## Fund CO addresses

Once the certificates are generated, the CO addresses need to receive the required BTC for revocation. Please wait for the testnetfaucet to be funded with the requisite credits and confirmed on the testnet before running this.

    usage: python fund-test-cos.py [-h] -i ID [-b BATCH_SIZE]
    
    Fund CO addresses with the required amount of bitcoin for the PoC test
    
    options:
      -h, --help            show this help message and exit
      -i ID, --id ID        Test identifier
      -b BATCH_SIZE, --batch-size BATCH_SIZE
                            Batch size, i.e., maximum number of outputs per transaction

A batch-size of upto 100 certificates has been tested.

The txids are returned by the script.


<a id="org67eb0d4"></a>

## Revoke Test Certificates

Once the transactions are confirmed on the testnet, the certificates can now be revoked.

    usage: python revoke-test-certificates.py [-h] -i TESTID [-b BLOCK_HEIGHT] [-r RPCCONNECT]
    
    Revoke test certificates and wait for BlockVoke transactions
    
    options:
      -h, --help            show this help message and exit
      -i TESTID, --testid TESTID
                            Test identifier
      -b BLOCK_HEIGHT, --block-height BLOCK_HEIGHT
                            Block Height after which the blocks are parsed for Revocation
                            Trasactions. (Only blocks above BLOCK_HEIGHT will be parsed)
      -r RPCCONNECT, --rpcconnect RPCCONNECT
                            Alternate rpcconnect ip address for fetching mempool
                            transactions and newly mined blocks

Please note that if a second bitcoind node is running, then it must accept rpc connections from the IP address of the machine from which this script is run. See [4](#orgd7077fe).

This action will send revocation transactions and wait for them to be witnessed on the mempool. The script will automatically exit after all transactions are confirmed on the testnet.

The revocation logfile location will be displayed, which contains the test results.

