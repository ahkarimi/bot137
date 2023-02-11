# /index.py
from flask import Flask, request, jsonify, render_template, session
#import os
import pickle
import datetime
import time
import pandas as pd
import numpy as np
import random
import logging
#import speech_recognition as sr

# logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logging.basicConfig(level=logging.DEBUG)



app = Flask(__name__)
app.secret_key = 'MY_SECRET_KEY'


#state = 'start'
#result = {}
#lable = []



def Lable_Message(message):
    logging.warning('In lable_Message')
    # load the model from disk
    model_filename = 'model/final_model.sav'
    tfidf_filename = 'model/tfidf.sav'
    idcategory_filename = 'model/id_to_category.sav'
    
    model = pickle.load(open(model_filename, 'rb'))
    tfidf = pickle.load(open(tfidf_filename, 'rb'))
    id_to_category =  pickle.load(open(idcategory_filename, 'rb'))
    
    #pred = model.predict(tfidf.transform([message]).toarray())
    #message_lable = id_to_category[pred[0]]
    
    # Get top 3 options with the highest probability
    n = 3         # top 3 probabilities
    probas = model.predict_proba(tfidf.transform([message]).toarray())
    best_n = np.flip(np.argsort(probas, axis=1)[:,-n:])
    message_lables = []
    
    for i in  best_n[0]:
        message_lables.append(id_to_category[i])
    logging.warning('Out lable_Message')
    return message_lables



def Is_address(address):
    key_words = ['خیابان', 'کوچه', 'بزرگراه', 'محله', 'میدان', 'پلاک', 'منطقه', 'خیابون', 'اتوبان']
    address = address.replace('-', ' ')
    address = address.replace(',', ' ')
    address = address.split()
    if len(address) > 3:
        for word in key_words:
            if word in address:
                return True
    return False



def Get_district(message):

    districts = pd.read_csv('model/districts.csv')
    
    address = message.replace('-', ' ')
    address = address.replace(',', ' ')
    address = address.split()
    dist = districts.loc[districts['name'].isin(address)]
    if len(dist) > 0:
        return dist.iloc[0]['district']
    
    return -1

def Lable_to_persian(lable):
    res = ''
    if lable == 'nezafat':
        res = 'نظافت معابر'
    elif lable == 'liaroobi':  
        res = 'لای روبی جوی'
    elif lable == 'terekidegi':
        res = 'ترکیدگی لوله'

    return res       

def Create_message(message):
    logging.warning('In create message')
    global result
    #global state
    #global lable
    
    ### State : on, start, confirm, address, done
    lable = session['lable']
    state = session['state']
    result = session['result']
    result['response'] = ''
    result['status'] = 'on'
    
    if state == 'start':
        lable = Lable_Message(message)
        session['lable'] = lable
        result['message'] = message
        result['response'] = 'سپاس، گزارش شما دریافت شد، جهت تایید آیا گزارش شما مربوط به  '
        
        if lable[0] == 'nezafat':
            result['response'] +=  'نظافت معابر است؟ (بله، خیر)'
            result['lable'] = Lable_to_persian(lable[0])
        elif lable[0] == 'liaroobi':
            result['response'] += ' لای روبی جوی است؟ (بله، خیر)'
            result['lable'] = Lable_to_persian(lable[0])
        elif lable[0] == 'terekidegi':
            result['response'] += 'ترکیدگی لوله است؟ (بله، خیر)'
            result['lable'] = Lable_to_persian(lable[0])
            
        session['state'] = 'confirm'
    
    
    elif state == 'confirm':
        
        if message == 'بله':
            result['response'] = 'سپاس، لطفا آدرس دقیق محل گزارش را وارد کنید، مثال: میدان جهاد خیابان فاطمی کوچه دوم'
            session['state'] = 'address'
            
        elif message == 'خیر':
            result['response'] = 'کدام گزینه مربوط به گزارش شماست؟ (فقط عدد گزینه را وارد کنید)'
            for i in range(len(lable)):
                if lable[i] == 'nezafat':
                    result['response'] +=   '<br> ' + str(i + 1) + '. نظافت معابر'
                elif lable[i] == 'liaroobi':
                    result['response'] +=  '<br> ' + str(i + 1) + '. لای روبی جوی'
                elif lable[i] == 'terekidegi':
                    result['response'] += '<br> ' + str(i + 1) + '. ترکیدگی لوله'   
            session['state'] = 'chagelable'       
        
        else:
            result['response'] = 'لطفا تنها با بله یا خیر جواب دهید'
            session['state'] = 'confirm'
    
    elif state == 'chagelable':
        
        if message == '1' or message == '۱':
            result['lable'] = Lable_to_persian(lable[0])
            result['response'] = 'سپاس، لطفا آدرس دقیق محل گزارش را وارد کنید'
            session['state'] = 'address'
            
        elif message == '2' or message == '۲':
            result['lable'] = Lable_to_persian(lable[1])
            result['response'] = 'سپاس، لطفا آدرس دقیق محل گزارش را وارد کنید'
            session['state'] = 'address'
            
        elif message == '3' or message == '۳':  
            result['lable'] = Lable_to_persian(lable[2])
            result['response'] = 'سپاس، لطفا آدرس دقیق محل گزارش را وارد کنید'
            session['state'] = 'address'
            
        else:
            result['response'] = 'لطفا تنها عدد گزینه را وارد کنید'
            session['state'] == 'chagelable'
    
    
    elif state == 'address':
        
        if  Is_address(message):
            reportID = str(random.randint(100, 999))
            result['ID'] = reportID
            result['address'] = message
            result['status'] = 'finished'
            result['district'] = str(Get_district(message))
            result['response'] = 'با سپاس از شما، مشکل ثبت شده و در حال پیگیری است. کد رهگیری: ' + reportID
            time = datetime.datetime.utcnow().replace(microsecond=0)
            result['date'] = str(time)
            result['priority'] = 'کد یک'
            session['state'] = 'done'
            
        else:
            result['response'] = 'به نظر میرسد آدرس وارد شده دقیق و صحیح نیست، لطفا دوباره آدرس را به شکل دقیق وارد کنید'
            session['state'] = 'address'
            
    elif state == 'done':
        result['response'] = 'گزارش شما ثبت شده است، گزارش جدیدی ثبت شود؟ (بله، خیر)'
        result['status'] = 'on'
        
        if message == 'بله':
            result = {}
            result['response'] = 'لطفا گزارش خود را وارد کنید'
            result['status'] = 'on'
            session['state'] = 'start'
            session['lable'] = ''

            
        elif message == 'خیر':
            result['response'] = 'سپاس، گزارش شما ثبت شده است'
            session['state'] = 'done'
        
        else:
            session['state'] = 'done'
            
   
    session['result']  = result
    
    return result


      
@app.route('/')
def index():
    #global state
    #state = 'start'
    session['state'] = 'start'
    session['lable'] = ''
    session['result'] = {}
    return render_template('index2.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    response_text = Create_message(message)
    # app.logger.info("HELLO")
    
    #print('\nRESPONSE TEXT ', response_text)
    return jsonify(response_text)

@app.route('/send_voice', methods=['POST'])
def send_voice():

    r = sr.Recognizer()
    if request.method == "POST":
        
        filename = str(round(time.time()))
        path = "voices/" + filename + ".wav"
        print(path)
        
        f = request.files['audio_data']
        with open(path, 'wb') as audio:
            f.save(audio)
            
    with sr.AudioFile(path) as source:
        data = r.record(source)
        
    message = r.recognize_google(data, language='fa-IR')
    response_text = Create_message(message)
    # print(response_text)
    
    return jsonify(response_text)
   


