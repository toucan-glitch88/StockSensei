# project
# StockSensei

StockSensei is an educational AI/ML app that predicts whether a stock may go up or down the next trading day.

## Team Members

* [Tanay Kataru]
* [Mohit Modi]
* [Eashan Tilaye]
* [Havish Vatti]

## Features

* Stock search
* Up/Down prediction
* Confidence score
* Simple explanation

## Disclaimer

For educational use only. Not financial advice.

## Running the Backend

1. Install dependencies:
python3 -m pip install flask pandas scikit-learn joblib

2. Start the backend:
python3 backend/app.py

3. Test prediction:
http://127.0.0.1:5000/predict/AAPL


## Backend Setup

The backend uses Flask and a saved machine learning model to predict whether a stock may go up or down.

### Install dependencies

```bash
python3 -m pip install -r requirements.txt

