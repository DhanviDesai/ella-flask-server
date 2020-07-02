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
import requests
from bs4 import BeautifulSoup

base_url = "https://ieeexplore.ieee.org/search/searchresult.jsp?"

scihub_url = "https://sci-hub.tw/"

GOOGLE_CHROME_BIN = '/app/.apt/usr/bin/google_chrome'

CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'

web_driver = None

app = Flask(__name__)

def attach_search_query(query,rows_per_page):
    query_url = base_url+"queryText="+query+"&rowsPerPage="+rows_per_page
    print(query_url)
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

def get_total_count_and_pages(div,rows_per_page):
    dashboard_header = div.find_elements_by_class_name("Dashboard-header")[0]
    span = dashboard_header.find_elements_by_tag_name("span")[0]
    strong_span = span.find_elements_by_tag_name("span")[1]
    total_count = int(strong_span.text.replace(",",""))
    total_pages = math.ceil(total_count/int(rows_per_page))
    return total_count,total_pages

def extract_papers(web_driver,query,rows_per_page):
    start = time.time()
    query_url = attach_search_query(query,rows_per_page)
    final_paper_list = {}
    with web_driver as driver:
        wait = WebDriverWait(driver,20)
        driver.get(query_url)
        wait.until(presence_of_element_located((By.CLASS_NAME,"Dashboard-header")))
        print('Finished waiting')
        total_count,total_pages = get_total_count_and_pages(driver.find_elements_by_class_name("Dashboard-section")[0],rows_per_page)
        final_paper_list["total_count"] = total_count
        final_paper_list["total_pages"] = total_pages
        results = driver.find_elements_by_class_name("List-results-items")
        final_results = []
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
            final_results.append(paper)
        driver.close()
    end = time.time()
    print(end-start)
    final_paper_list["papers"] = final_results
    response = json.dumps(final_paper_list)
    return response

def get_download_link(link):
    url = scihub_url+link
	main_page = requests.get(url)
	soup = BeautifulSoup(main_page.text,"html.parser")
	buttons_div = soup.find("div",attrs = {"id":"buttons"})
	if buttons_div == None:
		return False,None
	all_links = buttons_div.find_all("a")
	for link in all_links:
		if "save" in link.text:
			pdf_url = link.get("onclick").split("=")[1].replace("'","")
			#print('This is the pdf_url {}'.format(pdf_url))
			if("https:" not in pdf_url):
				pdf_url = "https:"+pdf_url
	pdf_page = requests.get(pdf_url)
	try:
		pdf_page.raise_for_status()
	except requests.exceptions.HTTPError as e:
		print('Not downloadable')
		return False,None
	return True,pdf_url

def get_paper_link_details(web_driver,link,type):
    if "Course" in type:
        result = {"error":"You selected a course, no information here"}
        return json.dumps(result)
    result = {}
    with web_driver as driver:
        wait = WebDriverWait(driver,20)
        driver.get(link)
        wait.until(presence_of_element_located((By.CLASS_NAME,"abstract-text")))
        print("Finished waiting")
        title = driver.find_elements_by_class_name("document-title")[0].text
        abstract = driver.find_elements_by_class_name("abstract-text")[0].text
		abstract = abstract.replace("Abstract:","").strip()
        published_in_div = driver.find_elements_by_class_name("stats-document-abstract-publishedIn")[0]
		published_in = published_in_div.find_elements_by_tag_name("a")[0].text
		date_of_conference = driver.find_elements_by_class_name("doc-abstract-confdate")[0].text
		date_of_conference = date_of_conference.replace("Date of Conference:","").strip()
		date_added = driver.find_elements_by_class_name("doc-abstract-dateadded")[0].text
		date_added = date_added.replace("Date Added to IEEE Xplore:","").strip()
        status,download_link = get_download_link(link)
        result["title"] = title
        result["abstract"] = abstract
        result["published_in"] = published_in
        result["date_of_conference"] = date_of_conference
        result["date_added"] = date_added
        result["status"] = status
        result["download_link"] = download_link
        driver.close()
    return json.dumps(result)

@app.route('/')
def home_page():
    return "<h1>Welcome to Ella Server</h1>"

@app.route("/search",methods=["GET","POST"])
def search():
    query_text = request.args.get("queryText")
    rows_per_page = request.args.get("rowsPerPage")
    web_driver = initialize_webdriver()
    response = extract_papers(web_driver,query_text,rows_per_page)
    return response

@app.route("/paperLink",methods=["GET","POST"])
def paper_link():
    start = time.time()
    link = request.args.get("link")
    type = request.args.get("type")
    web_driver = initialize_webdriver()
    response = get_paper_link_details(web_driver,link,type)
    end = time.time()
    print(end-start)
    return response
