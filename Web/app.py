from flask import Flask, request, jsonify, render_template
from models import translate
from search import fact_check
from search import get_searched_news
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('page.html')

@app.route('/predict', methods=['POST'])
def predict():
    Chinese_title = request.form['title']
    English_title = translate(Chinese_title, 'ChiToEng')
    info1 = fact_check(English_title)
    info2 = get_searched_news(English_title)
    return render_template('page.html', Chinese_title=Chinese_title, English_title=English_title, info=info1+info2)
                            

if __name__ == "__main__":
    app.run(port=5000,debug = True)
