import requests
from bs4 import BeautifulSoup
import sqlite3
import os
import re

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

def get_price_float(text_price):
    return float(re.findall(r'\d+[.]\d+', text_price)[0])

def get_data_from_file(file_path):
    file = open(file_path, mode='r', encoding='utf8')
    html_text = file.read()
    file.close()
    soup = BeautifulSoup(html_text, 'lxml')
    article = soup.find('h1').text
    print(article)
    try:
        description = soup.select('article.product_page > p')[0].text
    except:
        description = ''
    product_table = soup.select('article.product_page > table > tr > td')
    upc = product_table[0].text

    in_stock = int(re.findall(r'\d+', product_table[5].text)[0])

    incl_price = get_price_float(product_table[2].text)
    excl_price = get_price_float(product_table[3].text)
    tax = get_price_float(product_table[4].text)

    n_reviews = int(product_table[6].text)

    str_raiting = soup.select('p.star-rating')[0]['class'][1]
    raiting_dict = {'One': 1,
                    'Two': 2,
                    'Three': 3,
                    'Four': 4,
                    'Five': 5}
    raiting = raiting_dict[str_raiting]

    book_info = {'article': article,
                 'description': description,
                 'raiting': raiting,
                 'upc': upc,
                 'in_stock': in_stock,
                 'incl_price': incl_price,
                 'excl_price': excl_price,
                 'tax': tax,
                 'n_reviews': n_reviews}

    return book_info

def get_data_from_files():
    data = []
    for category in os.listdir('Books'):
        for book in os.listdir('Books/' + category):
            path = 'Books/' + category + '/' + book
            data.append(get_data_from_file(path))
    return data

def save_data_in_sqlite():
    data = get_data_from_files()
    conn = sqlite3.connect('toscrape.db')
    cursor = conn.cursor()

    cursor.execute('''DROP TABLE IF EXISTS books;''')

    cursor.execute('''CREATE TABLE books (
        id INTEGER PRIMARY KEY,
        article TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL,
        raiting INTEGER NOT NULL,
        upc TEXT NOT NULL UNIQUE,
        in_stock INTEGER NOT NULL,
        incl_price REAL NOT NULL,
        excl_price REAL NOT NULL,
        tax REAL NOT NULL,
        n_reviews INTEGER NOT NULL);''')

    cursor.executemany('''INSERT INTO books (
        article,
        description,
        raiting,
        upc,
        in_stock,
        incl_price,
        excl_price,
        tax,
        n_reviews)
        VALUES (
        :article,
        :description,
        :raiting,
        :upc,
        :in_stock,
        :incl_price,
        :excl_price,
        :tax,
        :n_reviews);''', data)
    
    conn.commit()
    cursor.close()
    print('Saved in sqlite')

def scrap_all():
    if not os.path.exists('Books'):
        os.mkdir('Books')
    categories = collect_categories(SITE_URL)
    for category in categories:
        collect_books_of_category(category)
    save_data_in_sqlite()

if __name__ == '__main__':
    scrap_all()