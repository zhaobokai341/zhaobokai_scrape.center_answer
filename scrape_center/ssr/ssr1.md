# 代码解释

这段Python代码的主要功能是从一个特定的网页（[https://ssr1.scrape.center/](https://ssr1.scrape.center/)
）上抓取电影信息，并将这些信息保存为JSON文件。代码使用了多进程和重试机制来提高抓取的效率和可靠性。下面是对代码的详细解释：

## 1. 导入必要的库

```python
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
```

- ```logging```：用于记录日志信息。
- ```requests```：用于发送HTTP请求。
- ```re```：用于正则表达式匹配。
- ```json.dumps```：用于将Python对象转换为JSON字符串。
- ```multiprocessing.Pool```：用于创建进程池，实现多进程。
- ```rich.logging.RichHandler```：用于美化日志输出。
- ```rich.traceback.install```：用于美化异常追踪信息。
- ```os.mkdir```：用于创建目录。
- ```retrying.retry```：用于实现重试机制。
- ```shutil.rmtree```：用于删除目录。

## 2. 配置日志

```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[RichHandler()])
install(show_locals=True)
```

- 配置日志记录器，设置日志级别为INFO，并使用RichHandler美化输出。
- 安装traceback，以便在捕获异常时显示详细的本地变量信息。

## 3. 定义请求的URL、页数和超时时间

```python
url = "https://ssr1.scrape.center/page/"
page = 10
timeout = 10
```

- ```url```：请求的基础URL。
- ```page```：要抓取的页数。
- ```timeout```：请求的超时时间。

## 4. 定义请求函数

```python
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
```

- 发送HTTP GET请求，并记录请求的URL和结果。

## 5. 获取链接

```python
def get_links(text):
    logging.info('Getting links...')
    links = re.findall(r'<a.*href="(.*)".*class="name">', str(text))
    for i in range(len(links)):
        links[i] = 'https://ssr1.scrape.center' + links[i]
    logging.info(f'links:{links}')
    return links
```

- 使用正则表达式从网页内容中提取电影详情页的链接。

## 6. 获取数据

```python
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
```

- 使用正则表达式从网页内容中提取电影信息，并使用retry装饰器实现重试机制

## 7. 保存数据

```python
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
```

- 将电影信息保存为JSON文件，文件名为电影标题，并去除文件名中的非法字符。

## 8. 主函数

```python
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
```

- 主函数，负责抓取指定页数的电影信息，并保存。

## 9. 主程序入口

```python
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
```

- 删除旧的文件夹```ssr1_data```，如果不存在则忽略错误。
- 创建新的文件夹```ssr1_data```。
- 创建进程池，并发执行```main```函数，抓取所有指定页数的电影信息。

CodeGeeX生成
