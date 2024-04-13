from googlesearch import search
from bs4 import BeautifulSoup 
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
#from googleapiclient.discovery import build
import time
from models import translate
from models import fake_news_results
from models import clickbait_results
from models import get_color
from models import get_verdict
from models import summary
from google_search import get_links


request_headers = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) ' \
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
}

def get_bbc(url:str):
    article = requests.get(url, headers=request_headers)
    soup = BeautifulSoup(article.content, "html.parser")
    update = soup.find('time')
    date = update['datetime'][:10]
    body = soup.find('article')
    title = soup.title.string
    text = [p.text for p in body.find_all("p")] 
    for i in range(len(text)):
        text[i] = text[i].strip()
    text = ' '.join(text)
    return title, date, text

def get_cnn(url:str):
    article = requests.get(url, headers=request_headers)
    soup = BeautifulSoup(article.content, "html.parser")
    update = soup.find('div', {'class' : 'timestamp'})
    date = update.string.strip().strip('\n')[16:]
    body = soup.find_all('p', {'class' : 'paragraph inline-placeholder'})
    title = soup.title.string
    text = []
    for par in body:
        text.append(par.text.strip().strip('\n'))
    text = ' '.join(text)
    return title, date, text

def get_reu(url:str):
    article = requests.get(url, headers=request_headers)
    soup = BeautifulSoup(article.content, "html.parser")
    time = soup.find('time').text
    date = time[time.find('read') + 4: time.find(',') + 6]
    body = soup.find('article')
    title = soup.title.string
    text = [p.text for p in body.find_all("p")] 
    for i in range(len(text)):
        text[i] = text[i].strip()
    text = ' '.join(text)
    return title, date, text

links = ['https://www.bbc.com/news/world-asia-64871603', 
         'https://edition.cnn.com/2023/03/07/us/five-things-march-7-trnd',
         'https://www.reuters.com/world/biden-says-us-forces-would-defend-taiwan-event-chinese-invasion-2022-09-18/']

def get_searched_news(s):
    res = [[]]
    for url in get_links(s): 
        lst = []
        if(url[:20] == 'https://www.bbc.com/'): 
            title, date, text = get_bbc(url)
        elif url[:24] == 'https://edition.cnn.com/':
            title, date, text = get_cnn(url)
        elif(url[:24] == 'https://www.reuters.com/'):
            title, date, text = get_reu(url)
        else:
            continue
        lst.append("News Article")
        lst.append(title)
        lst.append(date)
        lst.append(url)
        lst.append(fake_news_results(text))
        lst.append(clickbait_results(title))
        lst.append(translate(summary(text), 'EngToChi'))

        res.append(lst)
    
    return res[1:]

def fact_check(s):
    s = s.lower()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(options=chrome_options)
    browser.get('https://www.factcheck.org/search/#gsc.tab=0&gsc.q=' + s + '&gsc.sort=')
    soup = BeautifulSoup(browser.page_source, "lxml")
    links = soup.find_all('a', {'class' : 'gs-title'})
    info = [[]]
    titles = []
    dates = []
    tags = []  #title, date, url, tag, text
    for i in range(0, min(4, len(links)), 2):
      cur = []
      link = links[i]
      url = link.get('href')
      if(url == None or url == 'https://www.factcheck.org/'):
          continue
      r = requests.get(url)
      bs = BeautifulSoup(r.text, 'lxml')
      title = bs.title
      date = bs.find('time', {'class' : 'entry-date published updated'})

      if(title == None or date == None):
          break
      cur.append('Fact Check Article')
      cur.append(title.string[:-16])
      cur.append(date.string)
      cur.append(url)

      tag = bs.find('li', {'class' : 'post_tag'})
      if(tag != None):
          for cat in tag.find_all('li'):
              if(cat.text != None):
                  cur.append(cat.text)

      for script in bs(["script", "style"]):
          script.extract()    

      text = bs.body.get_text()
      a_tags = bs.find_all('h2')

      final_text = ""
      if(len(a_tags) > 0 and (a_tags[0].string == 'Quick Take' or a_tags[0].string == 'SciCheck Digest')):
          head, sep, tail = text.partition('Full Story')
          print(title.string)
          print(head)
          head, sep, tail = head.partition(a_tags[0].string)
          final_text = tail
      else:
          lines = (line.strip() for line in text.splitlines())
          chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
          text = '\n'.join(chunk for chunk in chunks if chunk)

          head, sep, tail = text.partition('Editor’s note:')
          s = title.string[:-16]
          head = head.replace("’", "'")
          head = head.replace("‘", "'")
          head, sep, tail = head.partition(s)
          final_text = sep + tail
          final_text = summary(final_text)

      cur.append(translate(final_text, 'EngToChi'))
      info.append(cur)

    info = info[1:]
    return info
