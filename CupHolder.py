import urllib2
# import threading

import socks
import socket

import Queue
import random
import time

import threading2 as threading
from mechanize import Browser

from CareerCupParser import CareerCupParser
from CupUtil import LimitedCache
import CupConfig

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
        global __CACHE__
        print("Fetcher")
        while True:
            url = self.url_queue.get()
            print("###### Fetching :"+url)
            page = None
            retry_count = 0
            url_id = CareerCupParser.url_id(url)

            if url_id in __CACHE__:
                print("###### Cache hit :"+url) 
                page = __CACHE__[url_id]
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
                            print("Failed to fetch page: " + url + ", error code" + str(e.code))
                    # put it back to queue
                    if url not in tempts:
                        retried_urls[url_id] = 1
                        self.url_queue.put(url)
                    elif tempts[url_id] < CupConfig.retries:
                        self.url_queue.put(url)
                        tempts[url_id] = tempts[url_id] + 1
                    else:
                        # raise Exception("Failed to fetch page: " + url + " after "+ str(CupConfig.retries)+" retries")
                        print("Failed to fetch page: " + url + " after "+ str(CupConfig.retries)+" retries")
                        self.url_queue.task_done()

            time.sleep(CupConfig.fetch_interval_in_second)

class Miner(threading.Thread):
    def __init__(self, page_queue, question_queue):
        threading.Thread.__init__(self)
        self.page_queue = page_queue
        self.question_queue = question_queue
        self.daemon = True

    def run(self):
        print("Miner")
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

    def run(self):
        print("Keeper")
        while(True):
            question = self.question_queue.get()
            self.save(question)
            self.question_queue.task_done()

    def save(self,question):
        print(question.question_content)
        
def main():
    global __CACHE__ 
    __CACHE__ = LimitedCache(size_limit=CupConfig.cache_size)

    # set up proxy is necessary
    if CupConfig.socks_proxy is not None:
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, CupConfig.socks_proxy[0], CupConfig.socks_proxy[1])
        socket.socket = socks.socksocket
        socket.create_connection = create_connection

    # cpu = random.choice(list(threading.system_affinity()))
    # threading.process_affinity((cpu,))

    for i in range(5):
        pf = Fetcher(url_queue, page_queue)
        pf.start()
    
    urls = CareerCupParser.generate_target_urls(CupConfig.base_url, CupConfig.query_params, __CACHE__)
    for url in urls:
        url_queue.put(url)

    for i in range(5):
        m = Miner(page_queue, question_queue)
        m.start()

    for i in range(5):
        k = Keeper(question_queue)
        k.start()
        
    url_queue.join()
    page_queue.join()
    question_queue.join()

def create_connection(address, timeout=None, source_address=None):
    sock = socks.socksocket()
    sock.connect(address)
    return sock

if __name__ == '__main__':
    main()
