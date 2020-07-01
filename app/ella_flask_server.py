from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
import sys
import math
import time
import os

base_url = "https://ieeexplore.ieee.org/search/searchresult.jsp?"

GOOGLE_CHROME_BIN = '/app/.apt/usr/bin/google_chrome'

CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'

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

def get_paper_title(div):
    h2 = div.find_elements_by_tag_name("h2")[0]
    return h2.text

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
    total_pages = math.ceil(total_count/25)
    return total_count,total_pages

def extract_papers(query):
    start = time.time()
    query_url = attach_search_query(query)
    webdriver = initialize_webdriver()
    with webdriver as driver:
        wait = WebDriverWait(driver,3)
        driver.get(query_url)
        wait.until(presence_of_element_located((By.CLASS_NAME,"main-section")))
        print('Finished waiting')
        total_count,total_pages = get_total_count_and_pages(driver.find_elements_by_class_name("Dashboard-section")[0])
        print(total_count)
        print(total_pages)
        print("*********************************************************************")
        results = driver.find_elements_by_class_name("List-results-items")
        for div in results:
            title = get_paper_title(div)
            authors = get_paper_authors(div)
            description,publisher_info = get_paper_description(div)
            print(title)
            print(authors)
            print(description)
            print(publisher_info)
            print('--------------------------------------------------------------------------------------------------------')
        driver.close()
    end = time.time()
    print(end-start)

@app.route('/')
def main_root():
    extract_papers('ml')
