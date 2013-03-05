import util
import environment
import cache

import logging
log = logging.getLogger('ss.consumer')

class Consumer(object):
    def __init__(self, url, environment = environment.default):
        import mechanize

        super(Consumer, self).__init__()
        ua = util.random_ua()
        br = mechanize.Browser()
        br.set_handle_robots(False)

        br.addheaders = [
            ('User-agent', ua),
            ('Accept', '*/*'),
            ('Accept-Encoding', 'gzip,deflate,identity'),
            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
            ('Accept-Language', 'en-us,en;q=0.5'),
        ]

        self.ua          = ua
        self.url         = url
        self.agent       = br
        self.final       = None
        self.fname       = None
        self.consumed    = False
        self.environment = environment

    def agent_cookies(self):
        return self.agent._ua_handlers['_cookies'].cookiejar

    def agent_cookie_string(self):
        return '; '.join( ["%s=%s" % (cookie.name, cookie.value) for cookie in self.agent_cookies()] )

    def finished(self):
        return self.final != None

    def set_final(self, final):
        self.final = final

    def consume(self):
        if self.consumed or not cache.stale('%s-url' % self.url, expires = 3 * cache.TIME_HOUR):
            return

        self.proc = self.find_procedure()

        self.initial_request()
        while not self.finished():
            self.run_step(self.proc.pop(0))

        self.consumed = True

    def initial_request(self):
        command = dict(name = 'request_page', args = self.url)
        self.proc.insert(0, command)

    def find_procedure(self):
        import urlparse

        def get_procedures():
            return util.gzip_request(util.procedures_endpoint())

        nil, domain, nil, nil, nil, nil = urlparse.urlparse(self.url)
        found      = None
        procedures = self.environment.str_to_json(cache.fetch('procedures.json', get_procedures, expires = cache.TIME_DAY))

        for proc_domain in procedures.iterkeys():
            if proc_domain in domain:
                found = proc_domain
                break

        if found:
            log.info('Found procedure for %s' % domain)
            proc = procedures[found]
            del proc[0]
            return proc

    def asset_url(self):
        def get_final():
            self.consume()
            return self.final

        cached = cache.fetch('%s-url' % self.url, get_final, expires = 3 * cache.TIME_HOUR)
        log.info(cached)
        return cached

    def file_name(self):
        def get_fname():
            self.consume()
            return self.helper({ 'method': 'file_name', 'asset_url': self.asset_url() })

        if not self.fname:
            self.fname = cache.fetch('%s-fname' % self.url, get_fname, expires = cache.TIME_DAY)

        log.info(self.fname)
        return self.fname

    def run_step(self, step):
        getattr(self, step['name'])(step['args'])

    def request_page(self, url):
        log.debug('Requesting %s' % url)
        self.replace_page( self.agent.open(url) )

    def post_request(self, params):
        import urllib
        url = params['__url']
        del params['__url']

        self.agent.open(url, urllib.urlencode(params))

    def replace_page(self, response):
        response = self.ungzipResponse(response).read()
        cache.instance().set('%s-markup' % self.url, response)

    def markup(self):
        return cache.instance().get('%s-markup' % self.url)

    def wait(self, seconds):
        import time
        log.debug('Waiting for %s seconds' % seconds)
        time.sleep(seconds)

    def submit_form(self, args):
        # TODO: handle more cases
        if args.get('index') is not None:
            self.agent.select_form(nr = args['index'])

        if args.get('name') is not None:
            self.agent.select_form(name = args['name'])

        self.agent.form.set_all_readonly(False)

        button_finder = args.get( 'button', {} )
        if button_finder:
            if button_finder.get('value', None):
                button_finder['label'] = button_finder['value']
                del button_finder['value']

            button = self.agent.form.find_control(**button_finder)
            button.disabled = False

        self.replace_page( self.agent.submit(**button_finder) )

    def helper(self, args):
        import zlib
        default_params = {
            'url':  self.url,
            'page': self.markup()
        }

        helper_url = util.listings_endpoint('/helpers')
        merged     = dict(default_params, **args)
        compressed = zlib.compress(self.environment.to_json(merged), 9)
        params     = { 'payload': compressed }
        resp       = self.environment.json(helper_url, **params)

        if type(resp) is dict:
            self.proc.insert(0, resp)
        elif type(resp) is list:
            resp.reverse()
            for c in resp:
                self.proc.insert(0, c)

        return resp

    def haystack_from(self, args):
        haystack = None
        url      = args.get('url', 'last_page')

        if 'last_page' == url: haystack = self.markup()
        else: haystack = self.ungzipResponse(self.agent.open(url)).read()

        return haystack

    def attribute_from(self, element, args):
        result    = None
        attribute = args.get('attribute', 'default')

        if attribute == 'default':
            tag = element.tag

            if 'a' == tag:
                result = element.get('href')
            elif 'img' == tag:
                result = element.getparent.get('href')
            elif 'embed' == tag:
                result = element.get('src')
            elif 'param' == tag:
                result = element.get('value')
        else:
            result = element.get(attribute)

        return result

    def set_final_if_requested(self, final, args):
        if args.get('final', False): self.set_final(final)

    def asset_from_xpath(self, args):
        haystack = self.haystack_from(args)
        element  = self.environment.xpath(haystack, args['query'])[0]
        result   = self.attribute_from(element, args)
        self.set_final_if_requested(result, args)

    def asset_from_css(self, args):
        haystack = self.haystack_from(args)
        element  = self.environment.css(haystack, args['selector'])[0]
        result   = self.attribute_from(element, args)
        self.set_final_if_requested(result, args)

    def asset_from_regex(self, args):
        import re

        expression = re.compile(args['expression'][7:-1])
        haystack   = self.haystack_from(args)
        result     = expression.findall(haystack)[0]
        self.set_final_if_requested(result, args)

    #from http://mattshaw.org/news/python-mechanize-gzip-response-handling/
    def ungzipResponse(self, r):
        headers  = r.info()
        encoding = headers.get('Content-Encoding', None)

        if encoding == 'gzip':
            import gzip

            gz   = gzip.GzipFile(fileobj = r, mode = 'rb')
            html = gz.read()
            gz.close()

            headers["Content-type"] = "text/html; charset=utf-8"
            r.set_data(html)
            self.agent.set_response(r)

        return r

if __name__ == '__main__':
    util.log_to_stderr()
    import sys
    args     = sys.argv
    test_url = args[1]

    consumer = Consumer(test_url)

    #print consumer.asset_url()
    print consumer.file_name()
