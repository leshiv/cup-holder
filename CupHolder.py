import urllib2
# import threading

import socks
import socket

import Queue

import time

import threading2 as threading
from mechanize import Browser
from BeautifulSoup import BeautifulSoup

from CareerCupParser import CareerCupParser
from CupConfig import CupConfig

url_queue = Queue.Queue()
page_queue = Queue.Queue()
question_queue = Queue.Queue()

__config__ = CupConfig()

class Fetcher(threading.Thread):
    def __init__(self, url_queue, page_queue):
        threading.Thread.__init__(self)
        self.url_queue = url_queue
        self.page_queue = page_queue
        self.browser = Browser()
        self.disguise()
        self.daemon = True

    def disguise(self):
        self.browser.addheaders=[('User-agent', __config__.user_agent),('Accept','*/*')]

    def run(self):
        print("Fetcher")
        while True:
            url = self.url_queue.get()
            req = urllib2.Request(url)
            res = self.browser.open(req)
            self.page_queue.put(res)
            self.url_queue.task_done()

class Miner(threading.Thread):
    def __init__(self, page_queue, question_queue):
        threading.Thread.__init__(self)
        self.page_queue = page_queue
        self.question_queue = question_queue
        self.daemon = True

    def run(self):
        print("Miner")
        while True:
            res = self.page_queue.get()
            data = res.read()
            print(data)
            self.page_queue.task_done()

class Keeper(threading.Thread):
    def __init__(self, question_queue):
        threading.Thread.__init__(self)
    def run(self):
        pass
    def save(self,question):
        pass

def main():
    cpu = random.choice(list(threading.system_affinity()))
    threading.process_affinity((cpu,))

    for i in range(5):
        pf = Fetcher(url_queue, page_queue)
        pf.start()
    
    urls = CareerCupParser.generate_target_urls(__config__.base_url, __config__.query_params)
    for url in urlss:
        url_queue.put(url)

    for i in range(5):
        m = Miner(page_queue, question_queue)
        m.start()
        
    url_queue.join()
    page_queue.join()
    question_queue.join()

def create_connection(address, timeout=None, source_address=None):
    sock = socks.socksocket()
    sock.connect(address)
    return sock

if __name__ == '__main__':
    if __config__.socks_proxy is not None:
        # set up socks proxy
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, __config__.socks_proxy[0], __config__.socks_proxy[1])
        socket.socket = socks.socksocket
        socket.create_connection = create_connection

    # main()
