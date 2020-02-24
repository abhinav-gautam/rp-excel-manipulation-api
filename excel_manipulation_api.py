from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib
import pandas as pd
import traceback
import sys
from openpyxl import load_workbook
import pyrebase

firebaseConfig = {
    "apiKey": "AIzaSyDb4gXoMuP5sBXlCq_8RANO-xNjsRAz0i8",
    "authDomain": "results-994c3.firebaseapp.com",
    "databaseURL": "https://results-994c3.firebaseio.com",
    "projectId": "results-994c3",
    "storageBucket": "results-994c3.appspot.com",
    "messagingSenderId": "864936938014",
    "appId": "1:864936938014:web:ad194b8b14a7a39ec2bc0f",
    "measurementId": "G-6RCZ7312QV"
  }

firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()

app = Flask(__name__)
CORS(app)

dtc_model5 = joblib.load("model5.pkl")
print('Models loaded')
model5_columns = joblib.load("model5_columns.pkl")
print('Model columns loaded')

@app.route('/')
def index():
    return "Hello, World!"


@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    if dtc_model5:
        try:
            # Getting file_url from request
            _json = request.json
            file_url = _json[0]['url']

            # Reading data from firebase file
            data = pd.read_excel(file_url)
            test_data = data[model5_columns]

            # Making predictions
            prediction = list(dtc_model5.predict(test_data))
            print("Predictions Done!")
            pred = ['Pass' if x==1 else 'Fail' for x in prediction ]
            data['Predictions'] = pred

            # Downloading result file as result_predicted.xlsx and writing predictions in it
            storage.child('files/result.xlsx').download('/','result_predicted.xlsx')
            book = load_workbook("result_predicted.xlsx")
            print("File opening done")
            writer = pd.ExcelWriter("result_predicted.xlsx", engine='openpyxl')
            writer.book = book
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            data.to_excel(writer, "Sheet1") 
            writer.save()
            print("Writing Done!")

            # Storing back result_predicted.xlsx into firebase storage
            storage.child("files/result_predicted.xlsx").put("result_predicted.xlsx")
            return jsonify({'prediction':"Writing Done!"})
        except:
            return jsonify({'trace': traceback.format_exc()})


if __name__ == '__main__':
    app.run()