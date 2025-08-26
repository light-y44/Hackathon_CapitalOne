from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from pydub import AudioSegment
import sys
import os
import json 
import numpy as np
import math
from datetime import datetime, date
from decimal import Decimal
import time

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),  '..')))

from utils.calcWeather import calculate_weather_data
from utils.calIndx import calculate_indices_data
from utils.utils import  calulateArea, calculateYieldPred, huggingFaceAuth, translate_hi_to_en, translate_en_to_hi, debug_json, serialize_recommendations
from utils.repaymentLogic import preSeasonCalc
from FT_model.model import FineTunedLlama
from models.stt import load_asr_model
from models.repayment import FarmInputs, FarmDebtManager
from agentic_framework.agent import Agent

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

agent = Agent()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# BASE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# current_dir = os.path.dirname(__file__) 
# GEN_FINETUNED_DIR = os.path.join(current_dir, "../FT_model/adapter")
# FINANCE_FINETUNED_DIR = os.path.join(current_dir,"../FT_model/finance_adapter")

# llama = FineTunedLlama(BASE_MODEL, GEN_FINETUNED_DIR)
# finance_llama = FineTunedLlama(BASE_MODEL, FINANCE_FINETUNED_DIR)

asr_pipe = load_asr_model()

# huggingFaceAuth()

@app.route('/api/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    audio_file = request.files['audio']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    webm_path = os.path.join(UPLOAD_FOLDER, f"recording_{timestamp}.webm")
    audio_file.save(webm_path)

    # Convert to WAV
    wav_path = webm_path.replace(".webm", ".wav")
    sound = AudioSegment.from_file(webm_path, format="webm")
    sound.export(wav_path, format="wav")

    # Transcribe
    hindi_text = asr_pipe(wav_path)["text"]
    # print("Transcribed Hindi text:", hindi_text)
    english_text = translate_hi_to_en(hindi_text)

    return jsonify({
        "message": "Audio transcribed successfully",
        "hindi_text": hindi_text,
        "english_text": english_text
    })


@app.route('/api/submit_query', methods=['POST'])
def submit_query():
    data = request.get_json()
    query = data.get("query", "").strip()
    lang = data.get("lang", "en")
    if not query:
        return jsonify({"message": "No query provided"}), 400
    
    # response = llama.ask(query, "agriculture")
    time.sleep(2)
    response = agent.run(query)

    if "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1].strip()

    # Translate response to Hindi
    if lang == "hi":
        response = translate_en_to_hi(response)

    return jsonify({"message": response})


@app.route('/api/submit_initial_inputs', methods=['POST'])
def submit_initial_inputs():

    data = request.get_json()

    district = data.get("district", "").strip().title()
    crop = data.get("crop", "").strip().title()
    year = int(data.get("year"))
    area = float(data.get("farmArea")) 
    loan_amount = float(data.get("loanAmount"))
    interest_rate = float(data.get("interestRate"))
    month = data.get("month")
    off_farm_income = float(data.get("nonFarmIncome", 0.0))
    input_cost = float(data.get("inputCost", 0.0))
    monthly_expenses = float(data.get("monthlyExpenses", 0.0))
    tenure = int(data.get("tenure", 0))
    insurance_premium = float(data.get("insurancePremium", 0.0))

    if month == "November":
        predicted_yield, predicted_price = preSeasonCalc(
            area=area,
            district=district,
            crop=crop,
            year=year,
            monthly_expenses=monthly_expenses,
            tenure=tenure,
            Insurance_premium=insurance_premium,
            Input_cost=input_cost,
            off_farm_income=off_farm_income,
            interest_rate=interest_rate,
            principal=loan_amount
        )
        predicted_price = np.mean(predicted_price)
    else:
        weather_df = calculate_weather_data(year, district)
        indices_df = calculate_indices_data(year, district)
        area_district = calulateArea(district, crop, year) or area

        predicted_yield, predicted_price = calculateYieldPred(
            weather_df, 
            indices_df, 
            area_district, 
            crop, 
            district
        )

    fi = FarmInputs(
        area_ha=area,
        loan_principal=loan_amount,
        annual_interest_rate=interest_rate,
        off_farm_monthly=off_farm_income,
        input_cost=input_cost,
        household_monthly=monthly_expenses,
        loan_tenure_months=tenure,
        insurance=insurance_premium,
        yield_q_per_ha=predicted_yield*10,
        price_per_q=predicted_price,
        harvest_months = [4]
    )

    out = FarmDebtManager(fi).recommend()

    # Use before jsonify
    debug_json(out["recommendations"])

    recs_serialized = serialize_recommendations(out["recommendations"][:3])
    baseline_serialized = serialize_recommendations(out["baseline"])
    scenarios_serialized = serialize_recommendations(out.get("scenarios"))

    return jsonify({
        "recommendations": recs_serialized,
        "baseline": baseline_serialized,
        "scenarios": scenarios_serialized,
        "message": f"Predicted Yield {predicted_yield} for {crop} in {district} for year {year}"
    })


if __name__ == "__main__":
    app.run(debug=True)
