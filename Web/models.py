import numpy as np
import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import keras
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import googletrans
from googletrans import Translator
from summarizer import Summarizer

device=torch.device('cpu')
fake_news_model = torch.load('fake_news_model.pkl', map_location ='cpu') # load pretrained model
clickbait_model = keras.models.load_model('Clickbait_model.pkl') # load pretrained model
translator = Translator() # load pretrained model
summary_model = Summarizer('distilbert-base-uncased', hidden=[-1,-2], hidden_concat=True) # load pretrained model

def summary(text):
    result = summary_model(text,num_sentences=3)
    full = ''.join(result)
    return full

def preprocess_text(text):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    parts = []
    text_len = len(text.split(' '))
    delta = 300
    max_parts = 5
    nb_cuts = int(text_len / delta)
    nb_cuts = min(nb_cuts, max_parts)
    for i in range(nb_cuts + 1):
        text_part = ' '.join(text.split(' ')[i * delta: (i + 1) * delta])
        parts.append(tokenizer.encode(text_part, return_tensors="pt", max_length=500).to(device))
    return parts

def translate(text, to):
    if(to == 'EngToChi'): 
        result = translator.translate(text, dest = 'zh-tw')
    else: 
        result = translator.translate(text, dest = 'en')
    return result.text

def get_verdict(percent):
    if percent >= 70: 
        return "True" #+ " " + str(percent)
    elif percent >= 40:
        return "Not reliable" #+ " " + str(percent)
    else:
        return "Be careful: Might be fake" #+ " " + str(percent)

def fake_news_results(text):
    text_parts = preprocess_text(text)
    overall_output = torch.zeros((1,2)).to(device)
    try:
        for part in text_parts:
            if len(part) > 0:
                overall_output += fake_news_model(part.reshape(1, -1))[0]
    except RuntimeError:
        print("GPU out of memory, skipping this entry.")
    overall_output = F.softmax(overall_output[0], dim=-1)

    value, result = overall_output.max(0)

    term = "fake"
    score = value.item()
    if result.item() == 0:
        term = "real"
    if (term == "fake"):
      score = 1 - score
    percent = round(score * 100)

    return get_verdict(percent), get_color(percent)

def get_color(percent):
    if percent >= 70: 
        return "green"
    elif percent >= 40:
        return "orange"
    else:
        return "red"    

def clickbait_results(text):
    data = pd.read_csv("clickbait_data.csv")
    txt = data['headline'].values
    tokenizer = Tokenizer(num_words=5000)
    tokenizer.fit_on_texts(txt)
    text = [text]
    token_text = pad_sequences(tokenizer.texts_to_sequences(text), maxlen=500)
    preds = [round(i[0]) for i in clickbait_model.predict(token_text)]
    label = ""
    hue2 = ""
    for (text, pred) in zip(text, preds):
        if(pred == 1.0):
            label = 'Clickbait'
            hue2 = 'red'
        else:
            label = "Not Clickbait"
            hue2 = 'green'
        return label, hue2
