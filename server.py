from bottle import get, run, template, static_file

import ss
import os

root = os.path.abspath(__file__ + '/../')

@get('/')
def index():
    return template('index')

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

run(host = 'localhost', port = 8080, reloader = True)
