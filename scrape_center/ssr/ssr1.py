import logging
import requests
import re
from json import dumps
from multiprocessing import Pool
from rich.logging import RichHandler
from rich.traceback import install
from os import mkdir
from retrying import retry
from shutil import rmtree

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[RichHandler()])
install(show_locals=True)
url = "https://ssr1.scrape.center/page/"
page = 10
timeout = 10


def request(url):
    try:
        logging.info(f'requesting {url}...')
        response = requests.get(url, timeout=timeout)
    except Exception as e:
        logging.error(f'request failed:{str(e)}')
        return
    if response.status_code == 200:
        logging.info(f'request {url} success')
    else:
        logging.warning(f'request status code is abnormal:{response.status_code}')
        return
    return response.text


def get_links(text):
    logging.info('Getting links...')
    links = re.findall(r'<a.*href="(.*)".*class="name">', str(text))
    for i in range(len(links)):
        links[i] = 'https://ssr1.scrape.center' + links[i]
    logging.info(f'links:{links}')
    return links

@retry(stop_max_attempt_number=3, retry_on_result=lambda x: x is False)
def get_data(text):
    try:
        logging.info('Acquiring information...')
        cover = re.search(r'<img.*\n.*\n.*src="(.*?)".*\n.*class="cover">', str(text)).group(1)
        title = re.search(r'<h2.*class="m-b-sm">(.*?)</h2>', str(text)).group(1)
        type_ = re.findall(
            r'<button.*\n.*class="el-button category el-button--primary el-button--mini">.*\n.*<span>(.*?)</span>.*\n.*'
            r'</button>',
            str(text))
        score = re.search(r'<div .*class="el-col el-col-24 el-col-xs-8 el-col-sm-4"><p .*\n.*>(.*\n.*)</p>',
                          str(text)).group(1)
        drama = re.search(r'<div.*class="drama">.*\n.*<p.*>(.*\n.*\n.*)</p></div>', str(text)).group(1)
        type_ = ' '.join(type_)
        return {'cover': cover,
                'title': title,
                'type': type_,
                'score': float(str(score).strip()),
                'drama': drama}
    except Exception as e:
        logging.warning(f'Acquisition failed:{str(e)},Retrying...')
        return False


def save_data(data):
    logging.info('Saving data...')
    try:
        name = data.get('title')
        remove_char = "/\\:*?\"<>|"
        for i in remove_char:
            name = name.replace(i, '')
        file_path = f'ssr1_data/{name}.json'
        f = open(file_path, 'w', encoding='utf-8')
        f.write(dumps(data, indent=2, ensure_ascii=False))
        f.close()
    except Exception as e:
        logging.error(f'Save failed:{str(e)}')


def main(page):
    text = request(url + str(page))
    if text:
        links = get_links(text)
        if links:
            for j in links:
                text = request(j)
                data = get_data(text)
                logging.info(f'The information obtained is:{dumps(data, indent=2, ensure_ascii=False)}')
                save_data(data)


if __name__ == '__main__':
    logging.info('Deleting old folders...')
    try:
        rmtree('ssr1_data')
    except FileNotFoundError as e:
        pass
    except Exception as e:
        logging.error(f'Delete failed:{str(e)}')
        exit()
    try:
        logging.info('A new folder is being created...')
        mkdir('ssr1_data')
    except Exception as e:
        logging.error(f'Create failed:{str(e)}')
        exit()
    logging.info('starting request...')
    pool = Pool()
    pages = range(1, page + 1)
    pool.map(main, pages)
    pool.close()
    pool.join()
    logging.info('finishing request')
