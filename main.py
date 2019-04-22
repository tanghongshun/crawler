#! /usr/bin/env python
# coding=utf-8
import requests
from urllib import parse
import pymysql
from proxy import get_proxy
import random
from headers import user_agents

# headers = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
           #'Chrome/73.0.3683.103 Safari/537.36'
douban_url = 'https://movie.douban.com/j/new_search_subjects?'
item_list = ['导演', '编剧', '主演', '类型', '制片国家/地区', '语言', '上映日期', '片长', '又名']


def rid(raw, trash):
    for pair in trash:
        first = pair[0]
        end = pair[1]
        while 1:
            head = raw.find(first)
            if head == -1:
                break
            tail = raw.find(end, head)
            if tail == -1:
                break
            if tail + 1 < len(raw):
                raw = raw[0: head] + raw[tail + 1:]
            else:
                raw = raw[0: head]
    return raw


def get_url(offset):
    query_param = {
    'sort': 'T',
    'range': '0, 10',
    'tags': '',
    'playable': '',
    'unwatched': '',
    }
    query_params = parse.urlencode(query_param)
    full_url = douban_url + query_params + '&start=%s' % offset
    return full_url


def get_imdb(url, proxy_list):
    s = requests.Session()
    s.headers['User-Agent'] = random.choice(user_agents)
    proxy = random.choice(proxy_list)
    response_imdb = s.get(url)
    response_imdb.raise_for_status()
    response_imdb = response_imdb.content.decode('utf-8')
    infor_start = response_imdb.find('<script type="application/ld+json">')
    EN_name_start = response_imdb.find('"name":', infor_start) + 9
    EN_name_end = response_imdb.find('"', EN_name_start)
    EN_name = response_imdb[EN_name_start: EN_name_end]
    rating_people_start = response_imdb.find('"ratingCount":') + 15
    rating_people_end = response_imdb.find(',', rating_people_start)
    rating_people = response_imdb[rating_people_start: rating_people_end]
    rating_value_start = response_imdb.find('"ratingValue":') + 16
    rating_value_end = response_imdb.find('"', rating_value_start)
    rating_value = response_imdb[rating_value_start: rating_value_end]
    return EN_name, rating_people, rating_value


def get_detail(movie_str, proxy_list):
    infor = {}
    name_start = movie_str.find('<span property="v:itemreviewed">') + 32
    name_end = movie_str.find('</span>', name_start)
    infor['name'] = movie_str[name_start: name_end]
    print(infor['name'])
    image_start = movie_str.find('title="点击看更多海报">') + 35
    image_end = movie_str.find('"', image_start)
    infor['image'] = movie_str[image_start: image_end]
    short_on = movie_str.find('<div id="hot-comments" class="tab">')
    short_start = movie_str.find('<span class="short">', short_on) + 20
    short_end = movie_str.find('</span>', short_start)
    infor['short'] = movie_str[short_start: short_end][:500]
    infor_head = movie_str.find('<div id="info">')
    infor_tail = movie_str.find('</div>', infor_head)
    infor_str = movie_str[infor_head: infor_tail]
    for item in item_list:
        pos = infor_str.find(item)
        pos_start = infor_str.find(':', pos) + 1
        pos_end = infor_str.find('<br/>', pos_start)
        trash = [['<', '>']]
        infor[item] = rid(infor_str[pos_start: pos_end], trash).replace(' ', '')
    douban_rating_start = movie_str.find('<strong class="ll rating_num" property="v:average">') + 51
    douban_rating_end = movie_str.find('</strong>', douban_rating_start)
    infor['douban_rating'] = movie_str[douban_rating_start: douban_rating_end]
    douban_rating_people_start = movie_str.find('<a href="collections" class="rating_people"><span property="v:votes">') + 69
    douban_rating_people_end = movie_str.find('</span>', douban_rating_people_start)
    infor['douban_people'] = movie_str[douban_rating_people_start: douban_rating_people_end]
    imdb = movie_str.find('IMDb链接:')
    if imdb != -1:
        imdb_start = movie_str.find('<a href="', imdb) + 9
        imdb_end = movie_str.find('"', imdb_start)
        imdb_url = movie_str[imdb_start: imdb_end]
        EN_name, imdb_rating_people, imdb_rating = get_imdb(imdb_url, proxy_list)
        infor['EN_name'] = EN_name
        infor['imdb_people'] = imdb_rating_people
        infor['imdb_rating'] = imdb_rating
    else:
        infor['EN_name'] = ''
        infor['imdb_people'] = ''
        infor['imdb_rating'] = ''
    return infor


def con_sql(infor):
    conn = pymysql.connect(host='114.116.15.154',
                           port=3306,
                           user='root',
                           passwd='fe1e796b07d35484',
                           db='imdb',
                           charset='utf8'
                           )
    cursor = conn.cursor()
    sql = """insert into films(name, image, director, writter, actor, category, country, language, open_date, length, nickname, douban_rating, douban_people, EN_name, imdb_people, imdb_rating, comment)
             VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')""" % (infor['name'], infor['image'], infor['导演'], infor['编剧'], infor['主演'], infor['类型'], infor['制片国家/地区'], infor['语言'], infor['上映日期'], infor['片长'], infor['又名'], infor['douban_rating'], infor['douban_people'], infor['EN_name'], infor['imdb_people'], infor['imdb_rating'], infor['short'])
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        print('insert error!')
        conn.rollback()
    conn.close()


if __name__ == '__main__':
    s = requests.Session()
    s.headers['User-Agent'] = random.choice(user_agents)
    i = 0
    proxy_list = get_proxy()
    while 1:
        url = get_url(i)
        proxy = random.choice(proxy_list)
        response = s.get(url, proxies=proxy)
        response.raise_for_status()
        response_str = response.content.decode('utf-8')
        end = 0
        while 1:
            start = response_str.find('url', end)
            if start == -1:
                break
            start += 6
            end = response_str.find('"', start)
            new_url = response_str[start: end].replace('\\', '')
            proxy = random.choice(proxy_list)
            response_movie = s.get(new_url, proxies=proxy)
            response.raise_for_status()
            response_str_movie = response_movie.content.decode('utf-8')
            infor = get_detail(response_str_movie, proxy_list)
            print(infor)
            con_sql(infor)
        i += 20
