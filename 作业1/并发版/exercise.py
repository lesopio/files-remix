import requests,json,time
from pyquery import PyQuery
from bs4 import BeautifulSoup


def request_get_response(url):
    header = {
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
    }
    response = requests.get(url,headers=header)
    return response

def parse_initial_content(content,initial_url):
    # 创建一个Pyquery对象
    page_content =PyQuery(content)
    # 提取所有的a链接
    a_list = page_content('.newsList')('a').items()
    # 拼接每一个文章的URL
    final_article_href = []
    for a_href in a_list:
        # 拼接每一个文章的URL
        temp_url = initial_url+a_href.attr('href')[1:]
        print(temp_url)
        final_article_href.append(temp_url)
    return final_article_href

def article_content(href):
    # 发送请求,获取响应
    content = request_get_response(href)
    # 解析数据
    article = BeautifulSoup(content.text,'html.parser')
    # 提取文章的标题信息
    div = article.find_all('div',{"class":"newsShowTitle"})[0]
    article_title = div.find_all('p')[0].get_text()
    print(article_title)
    # 提取文章的发布时间和发布者
    article_information = div.find_all('div')[0].get_text()
    print(article_information)
    # 获取每个文章的内容
    div_information = article.find_all('div', {"id": "maximg"})[0].get_text().strip()
    time.sleep(3)
    return article_title,article_information,div_information

def save_data(article_title,article_information,div_information):
    article_data = {
        '标题信息':article_title,
        '文章信息':article_information,
        "文章内容":div_information,
    }
    json.dump(article_data,open(str(article_title)+".txt",'w',encoding='utf-8'),ensure_ascii=False)

if __name__ == '__main__':
    # 获取url，构造url循环翻页
    for i in range(1,8):
        page_url = "https://www.yydaobao.cn/?jkkp_{}/".format(i)
        # 拆分首页url，保留初始域名
        initial_url = page_url.split("?")[0]
        # 获取发送请求后的页面
        content = request_get_response(page_url)
        # 解析页面，获取每篇文章的url
        final_article_href = parse_initial_content(content.text, initial_url)
        # 获取每个文章页面的具体内容
        for href in final_article_href:
            # 获取每个文章的内容
            article_title, article_information, div_information = article_content(href)
            time.sleep(3)
            # 将数据保存到文本中
            save_data(article_title, article_information, div_information)
            time.sleep(1)

