import logging

user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36"
socks_proxy = ("127.0.0.1",1088)
fetch_interval_in_second = 1
base_url = "http://www.careercup.com/page"
query_params = {'pid':'amazon-interview-questions','topic':'c-plus-plus-interview-questions'}
cache_size = 30
retries = 3
companies = ['amazon','google','microsoft','facebook','twitter','alibaba']
fetcher_number = 4
miner_number = 4
inserts_per_transaction = 100
queue_timeout_in_second = 5
logging_level = logging.DEBUG