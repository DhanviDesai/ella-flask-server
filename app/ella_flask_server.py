from flask import Flask
import extract_ieee_papers_info

app = Flask(__name__)

@app.route('/')
def main_root():
    extract_ieee_papers_info.extract_papers('edge computing')
