import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from pyquery import PyQuery
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


TOTAL_PAGES = 372
MAX_WORKERS = 20
MAX_RETRIES = 4


session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


def request_get_response(url):
    header = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
        )
    }
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return session.get(url, headers=header, timeout=15)
        except requests.exceptions.SSLError as exc:
            last_exc = exc
            wait_seconds = 1.5 * attempt
            print(f"[WARN] SSL error on {url}, retry {attempt}/{MAX_RETRIES} after {wait_seconds:.1f}s: {exc}")
            time.sleep(wait_seconds)
        except requests.RequestException as exc:
            last_exc = exc
            wait_seconds = 1.0 * attempt
            print(f"[WARN] Request error on {url}, retry {attempt}/{MAX_RETRIES} after {wait_seconds:.1f}s: {exc}")
            time.sleep(wait_seconds)
    raise last_exc


def parse_initial_content(content, initial_url):
    page_content = PyQuery(content)
    a_list = page_content(".newsList")("a").items()
    final_article_href = []
    for a_href in a_list:
        temp_url = initial_url + a_href.attr("href")[1:]
        print(temp_url)
        final_article_href.append(temp_url)
    return final_article_href


def article_content(href):
    content = request_get_response(href)
    article = BeautifulSoup(content.text, "html.parser")
    div = article.find_all("div", {"class": "newsShowTitle"})[0]
    article_title = div.find_all("p")[0].get_text()
    print(article_title)
    article_information = div.find_all("div")[0].get_text()
    print(article_information)
    div_information = article.find_all("div", {"id": "maximg"})[0].get_text().strip()
    return article_title, article_information, div_information


def save_data(article_title, article_information, div_information):
    article_data = {
        "标题信息": article_title,
        "文章信息": article_information,
        "文章内容": div_information,
    }
    with open(f"{article_title}.txt", "w", encoding="utf-8") as f:
        json.dump(article_data, f, ensure_ascii=False)


if __name__ == "__main__":
    futures = {}
    seen_urls = set()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i in range(1, TOTAL_PAGES + 1):
            if i == 1:
                page_url = "https://www.yydaobao.cn/?jkkp/"
            else:
                page_url = f"https://www.yydaobao.cn/?jkkp_{i}/"

            print(f"Fetching list page {i}: {page_url}")
            initial_url = page_url.split("?")[0]
            content = request_get_response(page_url)
            final_article_href = parse_initial_content(content.text, initial_url)

            for href in final_article_href:
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                future = executor.submit(article_content, href)
                futures[future] = href

        total = len(futures)
        print(f"Total articles to fetch: {total}")

        for index, future in enumerate(as_completed(futures), start=1):
            href = futures[future]
            try:
                article_title, article_information, div_information = future.result()
                save_data(article_title, article_information, div_information)
                print(f"[{index}/{total}] Saved article: {article_title}")
            except Exception as exc:
                print(f"[WARN] Failed to fetch article {href}: {exc}")
