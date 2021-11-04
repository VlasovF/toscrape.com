import requests
from bs4 import BeautifulSoup
import os

SITE_URL = 'https://books.toscrape.com/'

def get_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    return soup

def collect_categories(url):
    home_page = get_page(url)
    nav_list = home_page.find_all('ul', class_='nav-list')[0]
    cat_list = nav_list.select('ul.nav-list > li > ul > li > a')
    categories = []
    for i in cat_list:
        categories.append({'name': i.text.strip(),
                          'link': url + i['href']})
    return categories

def collect_books_from_page(cat_name, page):
    book_links = page.select('article.product_pod > h3 > a')
    for link in book_links:
        book_title = link['title'].replace('/', ' or ')
        path = 'Books/' + cat_name + '/' + book_title +'.html'
        if not os.path.exists(path):
            response = requests.get(SITE_URL + 'catalogue/' + link['href'][9:])
            file = open(path, mode='w', encoding='utf8')
            file.write(response.text)
            file.close()

def collect_books_of_category(category):
    if not os.path.exists('Books/' + category['name']):
        os.mkdir('Books/' + category['name'])
    cat_link = category['link'][0:-10]
    next_page_to_collect = category['link']
    while next_page_to_collect:
        page = get_page(next_page_to_collect)
        collect_books_from_page(category['name'], page)
        html_link = page.select('ul.pager > li.next > a')
        if html_link:
            next_page_to_collect = cat_link + html_link[0]['href']
        else:
            next_page_to_collect = ''
    print('Books from category ' + category['name'] + ' collected!')

def scrap_all():
    if not os.path.exists('Books'):
        os.mkdir('Books')
    categories = collect_categories(SITE_URL)
    for category in categories:
        collect_books_of_category(category)

if __name__ == '__main__':
    scrap_all()