import urllib2
import socks
import socket

import Queue
import random
import time
from datetime import datetime
import logging

import threading2 as threading
from mechanize import Browser

from CareerCupParser import CareerCupParser
from CupUtil import LimitedCache
import CupConfig
from CupDBManager import CupDBManager

url_queue = Queue.Queue()
page_queue = Queue.Queue()
question_queue = Queue.Queue()
tempts = {}

class Fetcher(threading.Thread):
    def __init__(self, url_queue, page_queue):
        threading.Thread.__init__(self)
        self.url_queue = url_queue
        self.page_queue = page_queue
        self.browser = Browser()
        self.disguise()
        self.daemon = True

    def disguise(self):
        self.browser.addheaders=[('User-agent', CupConfig.user_agent),('Accept','*/*')]

    def run(self):
        global __cache__
        logging.debug("Fetcher" + "_"+threading.current_thread().name+"_"+str(threading.current_thread().ident))
        while True:
            url = self.url_queue.get()
            logging.info("Fetching "+url)
            page = None
            retry_count = 0
            url_id = CareerCupParser.url_id(url)

            if url_id in __cache__:
                logging.debug("Cache hit "+url) 
                page = __cache__[url_id]
                self.page_queue.put(page)
                self.url_queue.task_done()
            else:
                req = urllib2.Request(url)
                self.page_queue.put(page)
                self.url_queue.task_done()
                try:
                    page = self.browser.open(req).read()
                    self.page_queue.put(page)
                    self.url_queue.task_done()

                except Exception as e:
                    if isinstance(e, urllib2.HTTPError):
                        if e.code in [401, 403, 404, 501, 503]:
                            # raise Exception("Failed to fetch page: " + url + ", error code" + str(e.code))
                            logging.warn("Failed to fetch page: " + url + ", error code" + str(e.code))
                    # put it back to queue
                    if url not in tempts:
                        retried_urls[url_id] = 1
                        self.url_queue.put(url)
                    elif tempts[url_id] < CupConfig.retries:
                        self.url_queue.put(url)
                        tempts[url_id] = tempts[url_id] + 1
                    else:
                        # raise Exception("Failed to fetch page: " + url + " after "+ str(CupConfig.retries)+" retries")
                        logging.warning("Failed to fetch page: " + url + " after "+ str(CupConfig.retries)+" retries")
                        self.url_queue.task_done()

            time.sleep(CupConfig.fetch_interval_in_second)

class Miner(threading.Thread):
    def __init__(self, page_queue, question_queue):
        threading.Thread.__init__(self)
        self.page_queue = page_queue
        self.question_queue = question_queue
        self.daemon = True
        # _strptime bug workaround
        datetime.strptime('2015','%Y')

    def run(self):
        logging.debug("Miner" + "_"+threading.current_thread().name+"_"+str(threading.current_thread().ident))
        while True:
            page = self.page_queue.get()
            questions = CareerCupParser.parse(page)
            for q in questions:
                question_queue.put(q)
            self.page_queue.task_done()

class Keeper(threading.Thread):
    def __init__(self, question_queue):
        threading.Thread.__init__(self)
        self.question_queue = question_queue
        self.daemon = True
        self.pending_inserts = 0
        # self.bulk = []

    def run(self):
        global question_count
        logging.debug("Keeper" + "_" + threading.current_thread().name + "_" + str(threading.current_thread().ident))

        self._db_manager = CupDBManager()
        try:
            self._db_manager.create_database()
        except:
            pass

        while(True):
            logging.debug("Total questions:" + str(question_count))
            question = None
            try: 
                question = self.question_queue.get(timeout=CupConfig.queue_timeout_in_second)
            except:
                self._db_manager.commit()
                continue

            self.save(question)
            question_count = question_count + 1
            self.question_queue.task_done()
            if self.pending_inserts > CupConfig.inserts_per_transaction:
                self._db_manager.commit()
                self.pending_inserts = 0

        self._db_manager.commit()
        self._db_manager.close()

    def save(self,question):
        inserted_question_id = self._db_manager.insert_question(question)
        self.pending_inserts = self.pending_inserts + 1
        for tag in question.tags:
            tag = tag.lower()
            self._db_manager.insert_tag(tag,self.is_tag_company(tag))
            self._db_manager.insert_question_with_tag(inserted_question_id, tag)
            self.pending_inserts = self.pending_inserts + 2

    def is_tag_company(self,tag_name):
        if tag_name in CupConfig.companies:
            return 1
        return 0

def main():
    global __cache__ 
    __cache__ = LimitedCache(size_limit=CupConfig.cache_size)

    global question_count
    question_count = 0

    logging.basicConfig(format='[%(levelname)s]:%(message)s', level=CupConfig.logging_level)

    # set up proxy if necessary
    if CupConfig.socks_proxy is not None:
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, CupConfig.socks_proxy[0], CupConfig.socks_proxy[1])
        socket.socket = socks.socksocket
        socket.create_connection = create_connection

    # cpu = random.choice(list(threading.system_affinity()))
    # threading.process_affinity((cpu,))

    for i in range(CupConfig.fetcher_number+1):
        pf = Fetcher(url_queue, page_queue)
        pf.start()
    
    urls = CareerCupParser.generate_target_urls(CupConfig.base_url, CupConfig.query_params, __cache__)
    for url in urls:
        url_queue.put(url)

    for i in range(CupConfig.miner_number+1):
        m = Miner(page_queue, question_queue)
        m.start()

    # "Don't use Sqlite3 in a threaded application"
    k = Keeper(question_queue)
    k.start()
        
    url_queue.join()
    page_queue.join()
    question_queue.join()

    logging.info('All done.')

def create_connection(address, timeout=None, source_address=None):
    sock = socks.socksocket()
    sock.connect(address)
    return sock

if __name__ == '__main__':
    main()
