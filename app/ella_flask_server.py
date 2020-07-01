from flask import Flask
import extract_ieee_papers_info as epi

app = Flask(__name__)

@app.route('/')
def main_root():
    epi.extract_papers('edge computing')
