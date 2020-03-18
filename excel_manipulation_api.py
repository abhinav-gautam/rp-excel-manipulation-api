from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib
import pandas as pd
import traceback
import os
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

# Loading Models
dtc_model1 = joblib.load("model1.pkl")
dtc_model2 = joblib.load("model2.pkl")
dtc_model3 = joblib.load("model3.pkl")
dtc_model4 = joblib.load("model4.pkl")
dtc_model5 = joblib.load("model5.pkl")
print('[+] Models loaded')

# Loading Model Columns
model1_columns = joblib.load("model1_columns.pkl")
model2_columns = joblib.load("model2_columns.pkl")
model3_columns = joblib.load("model3_columns.pkl")
model4_columns = joblib.load("model4_columns.pkl")
model5_columns = joblib.load("model5_columns.pkl")
print('[+] Model columns loaded')


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    if dtc_model1 and dtc_model2 and dtc_model3 and dtc_model4 and dtc_model5:
        try:
            # Getting file_url from request
            _json = request.json
            file_url = _json[0]['url']

            # Getting selected model from request
            selected_model = _json[0]['selected_model']

            # Creating predicted file name
            file_name = _json[0]['name']
            predicted_file_name = file_name.strip("." + file_name.split(".")[len(file_name.split(".")) - 1]) + "_" + str(selected_model) + "_predicted.xlsx"

            # Reading data from firebase file
            data = pd.read_excel(file_url)

            # Making predictions
            if selected_model == 'Model5':
                test_data = data[model5_columns]
                prediction = list(dtc_model5.predict(test_data))
            elif selected_model == 'Model4':
                test_data = data[model4_columns]
                prediction = list(dtc_model4.predict(test_data))
            elif selected_model == 'Model3':
                test_data = data[model3_columns]
                prediction = list(dtc_model3.predict(test_data))
            elif selected_model == 'Model2':
                test_data = data[model2_columns]
                prediction = list(dtc_model2.predict(test_data))
            else:
                test_data = data[model1_columns]
                prediction = list(dtc_model1.predict(test_data))

            print("[+] Predictions Done")
            pred = ['Pass' if x == 1 else 'Fail' for x in prediction]
            data['Predictions'] = pred

            # Downloading result file as temp.xlsx and writing predictions in it
            storage.child('files/' + file_name).download('/', 'temp.xlsx')
            book = load_workbook("temp.xlsx")
            print("[+] File opening done")
            writer = pd.ExcelWriter("temp.xlsx", engine='openpyxl')
            writer.book = book
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            data.to_excel(writer, "Sheet1")
            writer.save()
            print("[+] Writing Done")

            # Storing back test.xlsx into firebase storage
            storage.child("files/" + predicted_file_name).put("temp.xlsx")

            # Removing temp.xlsx
            os.remove("temp.xlsx")
            return jsonify({'predicted_file_name': predicted_file_name, "status": 200})
        except:
            return jsonify({'trace': traceback.format_exc()})


if __name__ == '__main__':
    app.run(port=12346, debug=True)
