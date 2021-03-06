#!/usr/bin/env python

import ss
from pyomxplayer import OMXPlayer
from bottle import get, run, template, static_file

import os
root = os.path.abspath(__file__ + '/../')

@get('/e/<endpoint:path>')
@get('/')
def index(endpoint = None):
    return template('index')

player = None
@get('/player/play/<endpoint:path>')
def play_media(endpoint):
    wizard = ss.Wizard(endpoint)

    def start_omxplayer(c):
        global player

        c.consume()
        url = c.asset_url()
        f   = c.file_name()

        if '.mp4' not in f:
            raise Exception('skipping non .mp4')

        if player: player.stop()

        player = OMXPlayer(url, args = '-o hdmi', start_playback = True)

    wizard.sources(start_omxplayer)

@get('/payload/<endpoint:path>')
def listings_payload(endpoint):
    from bottle import response
    import urllib
    import urllib2

    req  = urllib2.Request(ss.util.listings_endpoint(endpoint))
    json = urllib2.urlopen(req).read()

    response.content_type = 'application/json'
    return json

@get('/<asset:path>')
def get_asset(asset):
    return static_file(asset, root = root + '/public')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port',   default = 8080, type = int)
    parser.add_argument('-l', '--listen', default = '0.0.0.0')
    args = parser.parse_args()

    run(host = args.listen, port = args.port, reloader = True)
