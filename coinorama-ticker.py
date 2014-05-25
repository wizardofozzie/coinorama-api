#!/usr/bin/python
#
# Coinorama ticker API demo, markets and network info
#
# This file is distributed as part of Coinorama
# Copyright (c) 2013-2014 Nicolas BENOIT
#
# version 0.4.1 ; 2014-05-25
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#


import json
from httplib import HTTPConnection
from datetime import datetime
from sys import stdout, stderr


def get_version ( ):
    return '0.4.1'


def fetchData ( server, markets, network, blockchain ):
    marketsData = None
    networkData = None
    blockchainData = None

    connection = HTTPConnection ( server, timeout=5 )

    # markets
    connection.request ( 'GET', markets )
    r = connection.getresponse ( )
    if ( r.status == 200 ):
        marketsData = r.read ( )
    else:
        stderr.write ( 'error: fetchData() got status %d for markets\n' % r.status )
        return None

    # network
    connection.request ( 'GET', network )
    r = connection.getresponse ( )
    if ( r.status == 200 ):
        networkData = r.read ( )
    else:
        stderr.write ( 'error: fetchData() got status %d for network\n' % r.status )
        return None

    # blockchain
    connection.request ( 'GET', blockchain )
    r = connection.getresponse ( )
    if ( r.status == 200 ):
        blockchainData = r.read ( )
    else:
        stderr.write ( 'error: fetchData() got status %d for blockchain\n' % r.status )
        return None

    connection.close ( )

    # parse JSON
    return ( json.loads(marketsData), json.loads(networkData), json.loads(blockchainData) )



# markets
MKT_RATE = 0       # BTC rate against exchange currency
MKT_VOLUME = 1     # trading volume (past+current day)
MKT_DIRECTION = 2  # rate direction (0:down, 1:stable, 2:up)
MKT_DIRECTION_CHAR = [ u'\u2193', u'\u2192', u'\u2191' ] # down, stable, up
MKT_USD_CONV = 3   # exchange currency to USD conversion rate

MKT_EXCH_CURRENCY = { "bstamp":"USD",
                      "btce":"USD",
                      "bfinex":"USD",
                      "itbitUSD":"USD",
                      "krakenUSD":"USD",
                      "anxUSD":"USD",
                      "bchina":"CNY",
                      "huobi":"CNY",
                      "anxHKD":"HKD",
                      "krakenEUR":"EUR",
                      "itbitEUR":"EUR",
                      "bcentral":"EUR",
                      "bitcurexPLN":"PLN",
                      "bitmarketPLN":"PLN",
                      "bitbayPLN":"PLN",
                      "mercadoBRL":"BRL" };

def getAvgRate ( markets ):
    total_volume = 0.0
    mkt_sum = 0.0
    # weighted USD average of all available exchanges
    for t in markets['ticks']:
        mkt_sum += (t['tick'][MKT_RATE] * t['tick'][MKT_USD_CONV]) * t['tick'][MKT_VOLUME]
        total_volume += t['tick'][MKT_VOLUME]
    return (mkt_sum / total_volume)

def printMarkets ( data ):
    for t in data['ticks']:
        stdout.write ( ' ' + t['name'] )
        stdout.write ( ': %s' % MKT_DIRECTION_CHAR [ t['tick'][MKT_DIRECTION] ] )
        try:
            stdout.write ( ' %.2f %s' % (t['tick'][MKT_RATE], MKT_EXCH_CURRENCY[t['name']]) )
        except KeyError as e:
            stdout.write ( ' %.2f %s' % (t['tick'][MKT_RATE], '???') )
        stdout.write ( ' ; %.1f BTCs traded' % t['tick'][MKT_VOLUME] )
        stdout.write ( '\n' )


# network
NWK_BLOCK_ID = 0         # most recent block ID
NWK_BLOCK_TSTAMP = 1     # most recent block timestamp
NWK_CURRENT_DIFF = 2     # current network difficulty
NWK_CURRENT_PERIOD = 3   # current period length (seconds)
NWK_CURRENT_NB = 4       # number of blocks in current period
NWK_PAST_DIFF = 5        # difficulty of previous period
NWK_PAST_PERIOD = 6      # length of previous period (seconds)
NWK_PAST_NB = 7          # number of blocks in previous period

def printNetwork ( data ):
    t = data['ticks'][0]['tick'] # for now, only one crypto-currency available : Bitcoin
    stdout.write ( ' Block: %d' % t[NWK_BLOCK_ID] )
    stdout.write ( ' ; %s UTC\n' % datetime.utcfromtimestamp(t[NWK_BLOCK_TSTAMP]) )
    stdout.write ( ' Difficulty: %s\n' % t[NWK_CURRENT_DIFF] )

    hashrate = t[NWK_CURRENT_DIFF] * 7.158278826666667 # target hashrate
    hash_past = (t[NWK_PAST_DIFF] * 7.158278826666667) * (t[NWK_PAST_NB] / (t[NWK_PAST_PERIOD] / 600))
    hash_recent = hashrate * (t[NWK_CURRENT_NB] / (t[NWK_CURRENT_PERIOD] / 600))
    hash_wavg = ((hash_past*3)+hash_recent) / 4 # weighted hashrate, may be improved by considering periods length
    stdout.write ( ' Hashrate: %.1f Phash/sec' % (hash_wavg/1000000000) ) # MegaHash/sec converted to PetaHash/sec
    stdout.write ( '\n' )
    return


# market cap
def getNbCoinsMined ( block_id ):
    reward = 50
    halving = 210000
    total = 0
    while ( block_id > 0 ):
        nb_blocks = min ( halving, block_id )
        total += reward * nb_blocks
        block_id -= nb_blocks
        reward /= 2.0
    return total

def printMarketCap ( markets, block_id ):
    nbcoins = getNbCoinsMined ( block_id )
    avg = getAvgRate(markets)
    stdout.write ( ' Nb. Coins: %d BTCs\n' % getNbCoinsMined(block_id) )
    stdout.write ( ' Average Rate: %.2f USD/BTC\n' % avg )
    stdout.write ( ' Market Cap: %.2f Billions USD' % ((nbcoins*avg)/1000000000) )
    stdout.write ( '\n' )
    return


# blockchain
def printBlock ( block ):
    stdout.write ( ' Block: %d\n' % block['i'] )
    stdout.write ( ' Hash: %s\n' % block['h'] )
    stdout.write ( ' Previous Hash: %s\n' % block['p'] )
    stdout.write ( ' Merkle Tree: %s\n' % block['r'] )
    stdout.write ( ' Difficulty: %s\n' % block['d'] )
    stdout.write ( ' Nonce: %d\n' % block['n'] )
    stdout.write ( ' Size: %.2f Kbytes\n' % (float(block['s'])/1024) )
    stdout.write ( ' Nb. TXs: %d\n' % block['z'] )
    stdout.write ( '\n' )
    return


#
# main program
#
if __name__ == "__main__":
    t = fetchData ( 'coinorama.net', '/api/markets', '/api/network', '/api/blockchain' )
    if ( t != None ):
        (mkt_data,nwk_data,bc_data) = t
        print ( '\nCoinorama.net Ticker API demo v%s' % get_version() )
        print ( '\nMarkets:' )
        printMarkets ( mkt_data )
        print ( '\nNetwork:' )
        printNetwork ( nwk_data )
        print ( '\nMarket Cap:' )
        printMarketCap ( mkt_data, nwk_data['ticks'][0]['tick'][NWK_BLOCK_ID] )
        print ( '\nBlockchain:' )
        printBlock ( bc_data['data']['b'] )
