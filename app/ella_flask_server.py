from flask import Flask
from flask import request
import time

from .extract_ieee_papers import extract_papers,get_paper_link_details,get_download_link,initialize_webdriver


app = Flask(__name__)


@app.route('/')
def home_page():
    return "<h1>Welcome to Ella Server</h1>"

@app.route("/search",methods=["GET","POST"])
def search():
    query_text = request.args.get("queryText")
    rows_per_page = request.args.get("rowsPerPage")
    range = None
    filters = None
    range = request.args.get("range")
    filters = request.args.get("filters")
    print(filters)
    web_driver = initialize_webdriver()
    response = extract_papers(web_driver,query_text,rows_per_page,range,filters)
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

@app.route("/getDownloadLink",methods=["GET","POST"])
def download_link_endpoint():
    start = time.time()
    link = request.args.get("link")
    response = get_download_link(link)
    end = time.time()
    print(end-start)
    return response
