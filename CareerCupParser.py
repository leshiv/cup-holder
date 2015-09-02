import math

import time

from mechanize import Browser
from BeautifulSoup import BeautifulSoup

from CupConfig import CupConfig

__config__ = CupConfig()

class CareerCupParser:

	@staticmethod
	def _probe_page_numbers(br, url, probe_range):
		if br is None:
			br = Browser()
			br.addheaders=[('User-agent', __config__.user_agent),('Accept','*/*')]
		
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
			print("######### Probing:"+str(index))
			page = br.open(target_url).read()
			
			if CareerCupParser._is_null_page(page):
				next_range =(start + (2**(n-1) if n >= 1 else 0), index)
				return CareerCupParser._probe_page_numbers(br, url, next_range)

	@staticmethod
	def _is_null_page(page):
		sign = "Sorry - no more questions!"
		if sign in page:
			return True
		return False

	@staticmethod
	def generate_target_urls(base_url,query_params):
		filtered_url = base_url + '?'
		c = 0
		pml = len(query_params.keys())
		for p, v in query_params.items():
			filtered_url += p+'='+v
			if c < pml-1:
				filtered_url += '&'
			c += 1
		max_page_num = CareerCupParser._probe_page_numbers(None,filtered_url,(0,2**20))
		print("######### Max page number:" +str(max_page_num))
		# urls = [None] * (max_page_num+1)
		urls = []
		for i in range(max_page_num):
			urls.append(filtered_url+'&'+'n='+str(i+1))

		return urls


	@staticmethod
	def parse(page):
		soup = BeautifulSoup(page)
		lis = soup.findAll(['li'])
		for l in lis:
			print(l)
		questions = []
		return questions

	@staticmethod
	def _parse_single(chunk):
		pass
