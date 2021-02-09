from time import sleep
from selenium.common.exceptions import NoSuchElementException
import requests
import re
import lxml
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


driver = webdriver.PhantomJS()
count = 0

# 请求html文件
def getHTMLText(url):
    try:
        kv = {'user-agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=kv) # 防止查源user-agent
        r.raise_for_status() # 确保200
        r.encoding = r.apparent_encoding # 防止乱码
        demo = r.text
        return demo
    except:
        print("爬取失败")


def getBookNameList(demo, lists):
    # 利用BeautifulSoup组织html文件
    soup = BeautifulSoup(demo, 'lxml')  
    # 利用正则表达式找到对应地址
    lista = soup.find_all("a", href=re.compile("/guwen\/book_[0-9A-Z]{30,100}\.aspx"))
    tags = lista[1::3] # 每一本书有三个相同的a标签，选择了第二个a标签，其中有一个b标签里有这本书的名字  
    for tag in tags:
#         print(tag.string + "" + tag["href"])
        dic = {}
        dic["book"] = tag.string
        if "href" in tag.attrs: # 可能没有附链接
            dic["href"] = tag["href"]
        else:
            dic["href"] = ''
        lists.append(dic) # 书名：链接url
    return lists
	

# 查找type为正史类的书
keyword = '正史类'
pages = 3 # 有三页
lists = []
base_url = 'https://so.gushiwen.cn'# 基本url
articles = [] # 对于每一篇，存储书名，所属大类，章节名字，文章地址，内容

# Step1: 获取书名+地址
for page in range(pages):
    url = base_url + '/guwen/Default.aspx?p=' + str(page+1) + '&type='+keyword
    demo = getHTMLText(url)
    book_hrefs = getBookNameList(demo, lists)

# print(book_hrefs)


# Step2: 获取篇章+地址+内容
for book_href in book_hrefs:
    name = book_href['book']
    href = book_href['href']
    url = base_url + href
    demo = getHTMLText(url) # 复用
    soup = BeautifulSoup(demo, 'lxml')
    category_list = soup.select("div.bookcont")
#     print(category_list)
    for category in category_list:
        # 每一章节的名字和地址
        chapter_list = category.select("a")
        for chapter in chapter_list:
            chapter_name = chapter.string
            if "href" in chapter.attrs:
                chapter_href = chapter["href"]
            else:
                chapter_href = ''
            dic = {}
            dic["book"] = name # 书名
            dic["category"] = category.strong.string # 一类章节的归类名
            dic["chapter"] = chapter_name # 章节名字
            # 文章地址 与 文章内容
            if chapter_href == '':
                dic["url"] = ''
                dic["content"] = ''
            else:
                dic["url"] = base_url + chapter_href 
                print(dic["url"])
                dic["content"] = []

                driver.get(dic["url"])
                content_list = []
                try:
                    input = driver.find_element_by_partial_link_text('译文')
                except NoSuchElementException:
                    print("没有找到译文按钮")
                    try:
                        input = driver.find_element_by_partial_link_text('原文')
                        input.click()
                        input2 = driver.find_element_by_partial_link_text('段译')
                        input2.click()
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        content_list = soup.select("div.left > div.sons > div > div.contson > p")

                    except NoSuchElementException:
                        print("没有找到原文按钮")
                else:
                    input.click()
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    content_list = soup.select(
                        ".right > div > div.shisoncont > div.contson > p")  # cont46653FD803893E4F37C44D29335BA231 > div.contson


                contents = ''

                for content in content_list:
                     if content.string is not None:  # content可能为NoneType
                        contents = contents + content.string.replace('\u3000', '  ') + '\n'  # 处理编码不同的空格表示

                dic["content"] = contents
                if contents is not '':
                    count = count + 1
                else:
                    continue

            articles.append(dic) # 对于每一篇，存储书名，所属大类，章节名字，文章地址，内容
            print(dic)
            print("不为空的有"+str(count))
            # 导出为txt
            with open('D:\\classic_data\\' + dic["book"] + '·' + dic["category"]+ '·' + dic["chapter"] + '.txt', 'w', encoding='utf-8') as f:
                # 要加encoding，不然可能失败
                for key, value in dic.items():
                    f.write(key)
                    f.write(': ')
                    f.write('\n')
                    f.write(str(value))
                    f.write('\n')
                f.close()