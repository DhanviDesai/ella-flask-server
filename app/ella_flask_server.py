from flask import Flask
from flask import request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
import sys
import math
import time
import os
import json

base_url = "https://ieeexplore.ieee.org/search/searchresult.jsp?"

GOOGLE_CHROME_BIN = '/app/.apt/usr/bin/google_chrome'

CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'

web_driver = None

app = Flask(__name__)

def attach_search_query(query):
    query_url = base_url+"queryText="+query+"&rowsPerPage=10"
    return query_url

def initialize_webdriver():
    chrome_options = Options()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    webdriver1 = webdriver.Chrome(executable_path=str(os.environ.get("CHROMEDRIVER_PATH")),options=chrome_options)
    print('Finished initalize')
    return webdriver1

def get_paper_title_and_link(div):
    h2 = div.find_elements_by_tag_name("h2")[0]
    paper_link = h2.find_elements_by_tag_name("a")[0].get_attribute("href")
    return h2.text,paper_link

def get_paper_authors(div):
    authors = []
    p = div.find_elements_by_class_name("author")[0]
    spans = p.find_elements_by_tag_name("span")
    for span in spans:
        aas = span.find_elements_by_tag_name("a")
        if( len(aas) > 0 ):
            author = aas[0].text
            authors.append(author)
    return authors

def get_paper_description(div):
    description_div = div.find_elements_by_class_name("description")[0]
    description_div_list = description_div.find_elements_by_tag_name("a")
    description = None
    if(len(description_div_list) > 0):
        description = description_div_list[0].text
    pub = description_div.find_elements_by_class_name("publisher-info-container")[0].text
    publisher_info = pub.split("|")
    return description,publisher_info

def get_total_count_and_pages(div):
    dashboard_header = div.find_elements_by_class_name("Dashboard-header")[0]
    span = dashboard_header.find_elements_by_tag_name("span")[0]
    strong_span = span.find_elements_by_tag_name("span")[1]
    total_count = int(strong_span.text.replace(",",""))
    total_pages = math.ceil(total_count/10)
    return total_count,total_pages

def extract_papers(query):
    start = time.time()
    query_url = attach_search_query(query)
    web_driver = initialize_webdriver()
    final_paper_list = []
    with web_driver as driver:
        wait = WebDriverWait(driver,20)
        driver.get(query_url)
        wait.until(presence_of_element_located((By.CLASS_NAME,"main-section")))
        metadata = {}
        print('Finished waiting')
        total_count,total_pages = get_total_count_and_pages(driver.find_elements_by_class_name("Dashboard-section")[0])
        metadata["total_count"] = total_count
        metadata["total_pages"] = total_pages
        #print(total_count)
        #print(total_pages)
        #print("*********************************************************************")
        final_paper_list.append(metadata)
        results = driver.find_elements_by_class_name("List-results-items")
        for div in results:
            paper = {}
            title,paper_link = get_paper_title_and_link(div)
            authors = get_paper_authors(div)
            description,publisher_info = get_paper_description(div)
            paper["title"] = title
            paper["authors"] = authors
            paper["description"] = description
            paper["publisher_info"] = publisher_info
            paper["paper_link"] = paper_link
            #print(title)
            #print(authors)
            #print(description)
            #print(publisher_info)
            #print('--------------------------------------------------------------------------------------------------------')
            final_paper_list.append(paper)
        #driver.close()
    end = time.time()
    print(end-start)
    response = json.dumps(final_paper_list)
    return response

@app.route('/')
def home_page():
    return "<h1>Welcome to Ella Server</h1>"

@app.route("/search",methods=["GET","POST"])
def search():
    query_text = request.args.get("queryText")
    extract_papers(query_text)
