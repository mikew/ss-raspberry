import util
from consumer import Consumer
import environment
import cache

import logging
log = logging.getLogger('ss.wizard')

class Wizard(object):
    def __init__(self, endpoint, environment = environment.default, avoid_flv = False):
        super(Wizard, self).__init__()
        self.endpoint    = endpoint
        self.file_hint   = None
        self.avoid_flv   = avoid_flv
        self.environment = environment
        self.consumer    = None
        self.source_list = []

        try:
            def get_sources():
                return util.gzip_request(util.sources_endpoint(self.endpoint))

            self.payload     = self.environment.str_to_json(cache.fetch('%s-sources' % self.endpoint, get_sources, expires = cache.TIME_HOUR / 2))
            self.source_list = self.payload.get('items', [])
            self.file_hint   = self.payload['resource']['display_title']

            log.debug('%s has %s sources' % (self.file_hint, len(self.source_list)))
        except Exception, e:
            log.exception('Unable to get wizard info for %s' % endpoint)
            pass

    def filtered_sources(self):
        filtered = []

        try:
            sources  = self.payload.get('items', [])
            filtered = filter(lambda x: x['_type'] == 'foreign', sources)
        except: pass

        return filtered

    def translate(self, foreign):
        final_url = foreign.get('final_url')

        if final_url:
            return final_url
        else:
            response = self.environment.json( util.translate_endpoint( foreign['original_url'], foreign['foreign_url'] ) )
            return util.translated_from(response)

    #def sources(self):
        #for foreign in self.filtered_sources():
            #try:
                #consumer = Consumer(self.translate(foreign), environment = self.environment)
                #consumer.consume()
                #yield consumer
                #break
            #except GeneratorExit:
                #pass
            #except Exception, e:
                #util.print_exception(e)
                #continue

    def sources(self, cb):
        for foreign in self.source_list:
            try:
                consumer = Consumer(self.translate(foreign), environment = self.environment)

                if self.avoid_flv and '.flv' in consumer.asset_url():
                    log.info('Avoiding .flv')
                    raise Exception('Avoiding .flv')

                cb(consumer)
                self.consumer = consumer
                break
            except Exception, e:
                log.exception('Error on %s' % consumer.url)
                self.consumer = None
                continue

if __name__ == '__main__':
    util.log_to_stderr()
    import os, sys
    args     = sys.argv
    test_url = args[1]

    worked = 0
    def test():
        w = Wizard(test_url)

        #def print_url(c): c.consume()
        #w.sources(print_url)
        #w.consumer.asset_url()
        #w.consumer.file_name()

        def print_every_url(c):
            global worked
            c.asset_url()
            c.file_name()
            c.consume()
            worked += 1
            raise Exception('moving on.')

        w.sources(print_every_url)
        print '%d of %d worked' % (worked, len(w.source_list))

    test()
