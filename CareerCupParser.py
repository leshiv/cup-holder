import math
import time
import base64
from datetime import datetime
import logging

from mechanize import Browser
from bs4 import BeautifulSoup

import CupConfig
from CupModel import Question

host_url = 'http://www.careercup.com'
# html parser& utils powered by bs4 
class CareerCupParser:

    @staticmethod
    def _probe_page_numbers(br, url, probe_range, cache):
        if br is None:
            br = Browser()
            br.addheaders=[('User-agent', CupConfig.user_agent),('Accept','*/*')]
        
        start = probe_range[0]
        end = probe_range[1]
        index = start

        if  probe_range[1] - probe_range[0] <= 1:
            return probe_range[0]

        for n in range(int(round(math.log(probe_range[1] - probe_range[0])))+2):
            index = start + 2**n
            if index > end:
                index = end

            target_url = url + "&n=" +str(start + 2**n)
            logging.debug("Probing page number "+ str(index))
            page = br.open(target_url).read()

            if CareerCupParser._is_null_page(page):
                next_range =(start + (2**(n-1) if n >= 1 else 0), index)
                return CareerCupParser._probe_page_numbers(br, url, next_range, cache)
            else:
                cache[CareerCupParser.url_id(target_url)]=page

            time.sleep(CupConfig.fetch_interval_in_second)

    @staticmethod
    def _is_null_page(page):
        sign = "Sorry - no more questions!"
        if sign in page:
            return True
        return False

    @staticmethod
    def generate_target_urls(base_url,query_params,cache):
        filtered_url = base_url + '?'
        c = 0
        pml = len(query_params.keys())
        for p, v in query_params.items():
            filtered_url += p+'='+v
            if c < pml-1:
                filtered_url += '&'
            c += 1
        max_page_num = CareerCupParser._probe_page_numbers(None, filtered_url, (0,2**20), cache)
        logging.info("There are " + str(max_page_num) + " pages")
        # urls = [None] * (max_page_num+1)
        urls = []
        for i in range(max_page_num):
            urls.append(filtered_url+'&'+'n='+str(i+1))

        return urls

    @staticmethod
    def url_id(url):
        url_id = base64.urlsafe_b64encode(url)
        return url_id

    @staticmethod
    def parse(page):
        soup = BeautifulSoup(page)
        lis = soup.find_all('li',class_='question')
        questions = []
        for l in lis:
            # check
            q = CareerCupParser._parse_single(l)
            questions.append(q)

        return questions

    @staticmethod
    def _parse_single(soup):
        q = Question()

        content = ''
        content_doms = soup.find_all('p')
        if content_doms: 
            content = ''.join(content_doms[0].strings)
            # unix
            content = str(content).replace('\r', '\n')
        else:
            return None

        path = ''
        entry_doms = soup.find_all('span', class_='entry')
        if entry_doms:
            path_doms = entry_doms[0].find_all('a')
            if path_doms:
                path = path_doms[0].get('href')

        link = host_url + path

        question_id = 'careercup_'+path.split('id=')[1]

        vote_doms = soup.find_all('div', class_='votesNetQuestion')
        up_votes = 0
        if vote_doms:
            try:
                up_votes = int(vote_doms[0].text)
            except Exception as e:
                logging.warn("Invalid upvote count")
            #   raise e

        comment_doms = soup.find_all('span', class_='commentCount')
        comment_count = 0
        if comment_doms:
            try:
                comment_count = int(comment_doms[0].text)
            except Exception as e:
                logging.warn("Invalid comment count")

        tags = []
        tag_doms = soup.find_all('span', class_='tags')
        if tag_doms:
            tag_span = tag_doms[0]
            [tags.append(str(a.text)) for a in tag_span.find_all('a')]

        creation_date = None
        creation_date_doms = soup.find_all('abbr', class_='timeago')
        if creation_date_doms:
            creation_date_str = creation_date_doms[0].get('title')
            # creation_date = datetime.strptime(creation_date_str,'%B %d, %Y')
            creation_date = datetime.strptime(creation_date_str,'%Y-%m-%dT%H:%M:%S.%fZ')
            

        q.question_id = question_id
        q.question_content = content
        q.raw_html = soup
        q.tags = tags
        q.link = link
        q.up_votes = up_votes
        q.comment_count = comment_count

        if creation_date:
            q.creation_date = creation_date

        return q

