#!/usr/bin/python
#
# Coinorama ticker API demo, markets and network info
#
# This file is distributed as part of Coinorama
# Copyright (c) 2013-2014 Nicolas BENOIT
#
# version 0.6.0 ; 2014-09-06
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
    return '0.6.0'


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
    # disabled following storage problem
    #connection.request ( 'GET', blockchain )
    #r = connection.getresponse ( )
    #if ( r.status == 200 ):
    #    blockchainData = r.read ( )
    #else:
    #    stderr.write ( 'error: fetchData() got status %d for blockchain\n' % r.status )
    #    return None

    connection.close ( )

    # parse JSON
    #return ( json.loads(marketsData), json.loads(networkData), json.loads(blockchainData) )
    return ( json.loads(marketsData), json.loads(networkData), '' )



# markets
MKT_DIRECTION_CHAR = [ u'\u2193', u'\u2192', u'\u2191' ] # down, stable, up

def getAvgPrice ( markets ):
    total_volume = 0.0
    mkt_sum = 0.0
    # weighted USD average of all available exchanges
    for e in markets['ticks']:
        t = markets['ticks'][e]
        mkt_sum += (t['last'] * t['rusd']) * t['volume']
        total_volume += t['volume']
    return (mkt_sum / total_volume)

def getPriceDirection ( avg, last ):
    if ( abs(avg-last) <= 0.01 ):
        return 1
    elif ( avg > last ):
        return 0
    return 2

class exchange:
    def __init__ ( self, name, tick ):
        self.name = name[0:len(name)-3]
        self.price = tick['last']
        self.volume = tick['volume']
        self.direction = getPriceDirection ( tick['avg'], tick['last'] )
        self.usd_conv = tick['rusd']
        self.currency = name[len(name)-3:]

    def __unicode__ ( self ):
        return u'%s: %s %.2f %s ; %.1f BTCs traded the past 24 hours' % ( self.name, MKT_DIRECTION_CHAR[self.direction],
                                                                          self.price, self.currency, self.volume )
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __cmp__ ( self, other ):
        return (self.volume - other.volume)

def printMarkets ( data ):
    markets = { }
    for t in data['ticks']:
        e = exchange ( t, data['ticks'][t] )
        if e.currency not in markets:
            markets[e.currency] = [ ]
        markets[e.currency].append ( e )
    for c in markets:
        markets[c].sort ( reverse=True )
        print ( ' %s' % c )
        for e in markets[c]:
            print ( '  %s' % e )
    return



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
    print ( ' Block: %d ; %s UTC' % (t[NWK_BLOCK_ID],datetime.utcfromtimestamp(t[NWK_BLOCK_TSTAMP])) )
    print ( ' Difficulty: %s' % t[NWK_CURRENT_DIFF] )

    # hashrate
    hashrate = t[NWK_CURRENT_DIFF] * 7.158278826666667 # target hashrate
    hash_past = (t[NWK_PAST_DIFF] * 7.158278826666667) * (t[NWK_PAST_NB] / (t[NWK_PAST_PERIOD] / 600))
    hash_recent = hashrate * (t[NWK_CURRENT_NB] / (t[NWK_CURRENT_PERIOD] / 600))
    hash_wavg = ((hash_past*3)+hash_recent) / 4 # weighted hashrate, may be improved by considering periods length
    print ( ' Hashrate: %.1f Phash/sec' % (hash_wavg/1000000000) ) # MegaHash/sec converted to PetaHash/sec

    # mining pools
    pools = [ (data['ticks'][0]['pools'][p],p) for p in data['ticks'][0]['pools'] ]
    pools_sum = sum ( [ t[0] for t in pools ] )
    pools.sort ( reverse=True )
    print ( ' Top 5 Mining Pools:' )
    for i in range ( 5 ):
        print ( '  %s %.1f%%' % (pools[i][1],pools[i][0]*100.0/pools_sum) )
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
    avg = getAvgPrice(markets)
    print ( ' Nb. Coins: %d BTCs' % getNbCoinsMined(block_id) )
    print ( ' Average Price: %.2f USD/BTC' % avg )
    print ( ' Market Cap: %.2f Billions USD' % ((nbcoins*avg)/1000000000) )
    return


# blockchain
def printBlock ( block ):
    print ( ' Block: %d' % block['i'] )
    print ( ' Hash: %s' % block['h'] )
    print ( ' Previous Hash: %s' % block['p'] )
    print ( ' Merkle Tree: %s' % block['r'] )
    print ( ' Difficulty: %s' % block['d'] )
    print ( ' Nonce: %d' % block['n'] )
    print ( ' Size: %.2f Kbytes' % (float(block['s'])/1024) )
    print ( ' Nb. TXs: %d' % block['z'] )
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
        #print ( '\nBlockchain:' )
        #printBlock ( bc_data['data']['b'] )
        print ( '' )
