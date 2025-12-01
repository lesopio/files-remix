import json
import os
import re
import time
from typing import List, Dict, Optional, Set

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://www.yydaobao.cn"
START_LIST_URL = "https://www.yydaobao.cn/?jkkp/"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}


def fetch_page_soup(page_url: str) -> BeautifulSoup:
    response = requests.get(page_url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def parse_list_page_links(list_page_url: str, list_page_soup: BeautifulSoup) -> List[str]:
    article_urls: List[str] = []
    candidate_containers = []
    for class_name in ["news-list", "list", "list_box", "left_list", "main-list", "content"]:
        candidate_containers.extend(
            list_page_soup.find_all(class_=lambda class_attr: class_attr and class_name in class_attr)
        )

    if not candidate_containers:
        candidate_containers = [list_page_soup.body] if list_page_soup.body else [list_page_soup]

    unique_links_on_page: Set[str] = set()

    for container in candidate_containers:
        for link_tag in container.find_all("a", href=True):
            href: str = link_tag["href"].strip()
            if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                continue
            if "jkkp" not in href and not href.lower().endswith(".html"):
                continue
            full_url = urljoin(list_page_url, href)
            lowered_url = full_url.lower()
            if any(keyword in lowered_url for keyword in ["index", "list", "channel", "column"]):
                if "index_" in lowered_url:
                    continue

            if full_url not in unique_links_on_page:
                unique_links_on_page.add(full_url)
                article_urls.append(full_url)

    return article_urls


def find_next_page_url(current_list_url: str, list_page_soup: BeautifulSoup) -> Optional[str]:
    next_text_candidates = {"下一页", "下页", "下一页>", "下页>", ">>", "›", "下一页»"}

    for link_tag in list_page_soup.find_all("a", href=True):
        text = (link_tag.get_text() or "").strip()
        if text in next_text_candidates or "下一页" in text:
            href = link_tag["href"].strip()
            if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                continue
            return urljoin(current_list_url, href)
    for link_tag in list_page_soup.find_all("a", href=True):
        href = link_tag["href"].strip().lower()
        if "index_" in href and href.endswith(".html"):
            return urljoin(current_list_url, href)

    return None


def parse_publish_metadata(article_soup: BeautifulSoup) -> Dict[str, str]:
    candidate_texts: List[str] = []
    candidate_nodes = []
    meta_class_candidates = ["info", "meta", "source", "about", "subtitle", "extra", "message"]
    for class_name in meta_class_candidates:
        candidate_nodes.extend(
            article_soup.find_all(class_=lambda class_attr: class_attr and class_name in class_attr)
        )

    if not candidate_nodes:
        candidate_nodes = article_soup.find_all("p", class_=lambda class_attr: class_attr and "info" in class_attr)

    for node in candidate_nodes:
        text = node.get_text(" ", strip=True)
        if text:
            candidate_texts.append(text)
    if not candidate_texts:
        for paragraph in article_soup.find_all("p"):
            paragraph_text = paragraph.get_text(" ", strip=True)
            if any(keyword in paragraph_text for keyword in ["来源", "发布时间", "发布单位", "作者"]):
                candidate_texts.append(paragraph_text)

    publish_time = ""
    publish_unit = ""

    date_pattern = re.compile(r"(20\d{2}[年/-]\s*\d{1,2}[月/-]\s*\d{1,2}日?)")
    source_pattern = re.compile(r"(?:来源|发布单位|发布|供稿|作者)[:：]\s*([^\s|｜]+)")

    for text in candidate_texts:
        if not publish_time:
            match = date_pattern.search(text)
            if match:
                publish_time = match.group(1).replace("年", "-").replace("月", "-").replace("日", "")
                publish_time = re.sub(r"-+", "-", publish_time).strip("-")
        if not publish_unit:
            match = source_pattern.search(text)
            if match:
                publish_unit = match.group(1).strip()
        if publish_time and publish_unit:
            break

    return {
        "publish_time": publish_time,
        "publish_unit": publish_unit,
    }


def parse_article_page(article_url: str) -> Dict[str, str]:
    article_soup = fetch_page_soup(article_url)
    title = ""
    h1_tag = article_soup.find("h1")
    if h1_tag and h1_tag.get_text(strip=True):
        title = h1_tag.get_text(strip=True)
    else:
        title_tag = article_soup.find(
            class_=lambda class_attr: class_attr and any(
                keyword in class_attr for keyword in ["title", "bt", "biaoti"]
            )
        )
        if title_tag:
            title = title_tag.get_text(strip=True)

    if not title:
        if article_soup.title and article_soup.title.get_text(strip=True):
            title = article_soup.title.get_text(strip=True)

    article_content_text = ""
    content_container = None


    xpath_like_selector = (
        "html > body > div > div > div:nth-of-type(7) > div:nth-of-type(1) > "
        "div:nth-of-type(2) > div:nth-of-type(2)"
    )
    content_container = article_soup.select_one(xpath_like_selector)


    if not content_container:
        for key in ["content", "article", "article-body", "articleContent", "text", "detail"]:
            content_container = article_soup.find(
                "div", class_=lambda class_attr: class_attr and key.lower() in class_attr.lower()
            )
            if content_container:
                break

    if not content_container:
        content_container = article_soup.find(
            "section", class_=lambda class_attr: class_attr and "content" in class_attr
        ) or article_soup.find("div", id=lambda element_id: element_id and "content" in element_id)

    if content_container:
        paragraphs = [p.get_text(" ", strip=True) for p in content_container.find_all("p")]
        article_content_text = "\n".join(text for text in paragraphs if text)
    else:
        body_tag = article_soup.body or article_soup
        article_content_text = body_tag.get_text("\n", strip=True)

    publish_info = parse_publish_metadata(article_soup)

    return {
        "url": article_url,
        "title": title,
        "publish_time": publish_info.get("publish_time", ""),
        "publish_unit": publish_info.get("publish_unit", ""),
        "content": article_content_text,
    }


def fetch_articles_from_first_page(list_page_url: str = START_LIST_URL, delay_seconds: float = 0.5) -> List[Dict[str, str]]:
    print(f"Fetching list page: {list_page_url}")
    try:
        list_page_soup = fetch_page_soup(list_page_url)
    except Exception as exc:
        print(f"[WARN] Failed to fetch list page {list_page_url}: {exc}")
        return []

    article_urls_on_first_page = parse_list_page_links(list_page_url, list_page_soup)
    print(f"  Found {len(article_urls_on_first_page)} article links on the first page.")

    articles_data: List[Dict[str, str]] = []
    for index, article_url in enumerate(article_urls_on_first_page):
        print(f"[{index + 1}/{len(article_urls_on_first_page)}] Fetching article: {article_url}")
        try:
            article_data = parse_article_page(article_url)
            articles_data.append(article_data)
        except Exception as exc:
            print(f"[WARN] Failed to parse article {article_url}: {exc}")
        time.sleep(delay_seconds)

    return articles_data


def save_articles_to_txt(articles: List[Dict[str, str]], folder: str = "articles_txt") -> None:
    os.makedirs(folder, exist_ok=True)
    for idx, article in enumerate(articles, start=1):
        safe_title = re.sub(r"[\\/:*?\"<>|]+", "_", article.get("title") or f"article_{idx}")
        filename = os.path.join(folder, f"{idx:02d}_{safe_title}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"标题：{article.get('title', '')}\n")
            f.write(f"发布时间：{article.get('publish_time', '')}\n")
            f.write(f"发布单位：{article.get('publish_unit', '')}\n")
            f.write("正文：\n")
            f.write(article.get("content", ""))
        print(f"Saved article to {filename}")


def save_to_json(data: List[Dict[str, str]], filename: str = "yydaobao_jkkp_articles.json") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} articles to {filename}")


def main():
    articles_on_first_page = fetch_articles_from_first_page(START_LIST_URL)
    if not articles_on_first_page:
        return
    save_articles_to_txt(articles_on_first_page)
    save_to_json(articles_on_first_page)


if __name__ == "__main__":
    main()


