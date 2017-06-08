
**_Issues Faced by us on executing the claires file._**

**_Preliminary asumption as to where the problem might be is that the site or the link redirects us to "http://www.claires.co.uk" due to location difference._**

Note: **We are running Futura on python3.5**

**----------------------------------------------------------------------------------------------------------**     
**1).**
><h7>(env) skymap@skymap-HP-EliteBook-8460p:~/PycharmProjects/Virtual env/futura$ python3.5 -m futura    futura.scrapers.claires.claires_com -p stdout   
[futura] [2017-06-08 11:21:15,319] [PID 6196] [INFO] Begin Scraping     
[futura.support.bs4] [2017-06-08 11:21:15,324] [PID 6196] [INFO] Starting claires.claires_com     
Spider error processing <GET http://www.claires.co.uk> (referer: None)   
Traceback (most recent call last):   
&nbsp;&nbsp;&nbsp;&nbsp;File "/home/skymap/PycharmProjects/Virtual env/env/lib/python3.5/site-packages/scrapy/utils/defer.py", line 102, in iter_errback   
    &nbsp;&nbsp;&nbsp;&nbsp;yield next(it)   
  &nbsp;&nbsp;&nbsp;&nbsp;File "/home/skymap/PycharmProjects/Virtual env/env/lib/python3.5/site-packages/scrapy/spidermiddlewares/offsite.py", line 29, in process_spider_output   
    &nbsp;&nbsp;&nbsp;&nbsp;for x in result:    
  &nbsp;&nbsp;&nbsp;&nbsp;File "/home/skymap/PycharmProjects/Virtual env/env/lib/python3.5/site-   packages/scrapy/spidermiddlewares/referer.py", line 339, in <genexpr>   
    &nbsp;&nbsp;&nbsp;&nbsp;return (_set_referer(r) for r in result or ())   
  &nbsp;&nbsp;&nbsp;&nbsp;File "/home/skymap/PycharmProjects/Virtual env/env/lib/python3.5/site-    packages/scrapy/spidermiddlewares/urllength.py", line 37, in <genexpr>   
    &nbsp;&nbsp;&nbsp;&nbsp;return (r for r in result or () if _filter(r))   
  &nbsp;&nbsp;&nbsp;&nbsp;File "/home/skymap/PycharmProjects/Virtual env/env/lib/python3.5/site-packages/scrapy/spidermiddlewares/depth.py", line 58, in <genexpr>   
    &nbsp;&nbsp;&nbsp;&nbsp;return (r for r in result or () if _filter(r))   
  &nbsp;&nbsp;&nbsp;&nbsp;File "/home/skymap/PycharmProjects/Virtual env/futura/futura/support/bs4.py", line 81, in cache_and_seed    
&nbsp;&nbsp;&nbsp;&nbsp;    **url_data = response.request.url_data**   
&nbsp;&nbsp;&nbsp;&nbsp;**AttributeError: 'Request' object has no attribute 'url_data'**   
[futura] [2017-06-08 11:21:17,665] [PID 6196] [INFO] Scraping took 2.35s    

2).

>On checking the dir(response.request)   
WE get--->    
>['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__',     '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__',     '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__',     '__weakref__', '_body', '_encoding', '_get_body', '_get_url', '_meta', '_set_body', '_set_url', '_url', 'body',     'callback', 'cookies', 'copy', 'dont_filter', 'encoding', 'errback', 'flags', 'headers', 'meta', 'method',      'priority', 'replace', 'url']    

>It has "url" as attribute but not "url_data"

3).

>So on replacing __"url_data = response.request.url_data"__ as __"url_data = response.request.url"__ in the bs4.py file     under "cache_and_seed" function and executing the code gives us the desired results.    

4).

>We are still not clear on the use of **_"@register"_** as to how to use it more efficiently to scrape multiple links** at a time.    
The seeder generates the links, but when they are passed into the extracter it is done serially, which tmakes the scraping a very time taking process.




```python

```
