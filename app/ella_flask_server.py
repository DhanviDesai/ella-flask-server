from flask import Flask

app = Flask(__name__)

@app.route('/')
def main_root():
    return '<h1>Hello world</h1>'
