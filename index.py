# /index.py
from flask import Flask, request, jsonify, render_template
import os
import requests
import pickle
import datetime
import pandas as pd
import numpy as np
import random
import logging

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.warning('Starting')

app = Flask(__name__)

state = 'start'
result = {}
label = []



# @app.route('/webhook', methods=['POST'])
# def webhook():
#     data = request.get_json(silent=True)
#     print('[ DATA ]', data)
#     if data['queryResult']['queryText'] == 'yes':
#         reply = {
#             "fulfillmentText": "Ok. Tickets booked successfully.",
#         }
#         return jsonify(reply)

#     elif data['queryResult']['queryText'] == 'no':
#         reply = {
#             "fulfillmentText": "Ok. Booking cancelled.",
#         }
#         return jsonify(reply)


def Label_Message(message):
    logging.info('In lable message')
    # load the model from disk
    model_filename = 'model/final_model.sav'
    tfidf_filename = 'model/tfidf.sav'
    idcategory_filename = 'model/id_to_category.sav'
    
    model = pickle.load(open(model_filename, 'rb'))
    tfidf = pickle.load(open(tfidf_filename, 'rb'))
    id_to_category =  pickle.load(open(idcategory_filename, 'rb'))
    
    #pred = model.predict(tfidf.transform([message]).toarray())
    #message_label = id_to_category[pred[0]]
    
    # Get top 3 options with the highest probability
    n = 3         # top 3 probabilities
    probas = model.predict_proba(tfidf.transform([message]).toarray())
    best_n = np.flip(np.argsort(probas, axis=1)[:,-n:])
    message_labels = []
    
    for i in  best_n[0]:
        message_labels.append(id_to_category[i])
    
    return message_labels



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

    districts = pd.read_excel('model/districts.xlsx')
    
    address = message.replace('-', ' ')
    address = address.replace(',', ' ')
    address = address.split()
    dist = districts.loc[districts['name'].isin(address)]
    if len(dist) > 0:
        return dist.iloc[0]['district']
    
    return -1



def Create_message(message):
    logging.info('In Create Message')
    global result
    global state
    global label
    result['response'] = ''
    ## State : on, start, confirm, address, done
    result['status'] = 'on'
    
    if state == 'start':
        label = Label_Message(message)
        result['message'] = message
        result['response'] = 'سپاس، گزارش شما دریافت شد، جهت تایید آیا گزارش شما مربوط به  '
        
        if label[0] == 'nezafat':
            result['response'] +=  'نظافت معابر است؟ (بله، خیر)'
            result['label'] = 'نظافت معابر'
        elif label[0] == 'liaroobi':
            result['response'] += ' لای روبی جوی است؟ (بله، خیر)'
            result['label'] = 'لای روبی جوی'
        elif label[0] == 'terekidegi':
            result['response'] += 'ترکیدگی لوله است؟ (بله، خیر)'
            result['label'] = 'ترکیدگی لوله'
            
        state = 'confirm'
    
    
    elif state == 'confirm':
        
        if message == 'بله':
            result['response'] = 'سپاس، لطفا آدرس دقیق محل گزارش را وارد کنید'
            state = 'address'
            
        elif message == 'خیر':
            result['response'] = 'کدام گزینه مربوط به گزارش شماست؟ (فقط عدد گزینه را وارد کنید)'
            for i in range(len(label)):
                if label[i] == 'nezafat':
                    result['response'] +=   '<br> ' + str(i + 1) + '. نظافت معابر'
                elif label[i] == 'liaroobi':
                    result['response'] +=  '<br> ' + str(i + 1) + '. لای روبی جوی'
                elif label[i] == 'terekidegi':
                    result['response'] += '<br> ' + str(i + 1) + '. ترکیدگی لوله'   
            state = 'chageLabel'       
        
        else:
            result['response'] = 'لطفا تنها با بله یا خیر جواب دهید'
            state = 'confirm'
    
    elif state == 'chageLabel':
        
        if message == '1':
            result['label'] = label[0]
            result['response'] = 'سپاس، لطفا آدرس دقیق محل گزارش را وارد کنید'
            state = 'address'
            
        elif message == '2':
            result['label'] = label[1]
            result['response'] = 'سپاس، لطفا آدرس دقیق محل گزارش را وارد کنید'
            state = 'address'
            
        elif message == '3':  
            result['label'] = label[2]
            result['response'] = 'سپاس، لطفا آدرس دقیق محل گزارش را وارد کنید'
            state = 'address'
        else:
            result['response'] = 'لطفا تنها عدد گزینه را وارد کنید'
            state == 'chageLabel'
    
    
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
            state = 'done'
            
        else:
            result['response'] = 'به نظر میرسد آدرس وارد شده دقیق و صحیح نیست، لطفا دوباره آدرس را به شکل دقیق وارد کنید'
            state = 'address'
            
    elif state == 'done':
        result['response'] = 'گزارش شما ثبت شده است'
        result['status'] = 'done'
        
        
    return result


      
@app.route('/')
def index():
    global state
    state = 'start'
    return render_template('index2.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    response_text = Create_message(message)
    #print('\nRESPONSE TEXT ', response_text)
    logging.info('In Send message, Response Text: ',  response_text)
    return jsonify(response_text)

# run Flask app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')