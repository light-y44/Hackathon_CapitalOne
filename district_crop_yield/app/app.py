from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from datetime import datetime
from pydub import AudioSegment
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),  '..')))

from utils.calcWeather import calculate_weather_data
from utils.calIndx import calculate_indices_data
from utils.utils import  calulateArea, calculateYieldPred, huggingFaceAuth, translate_hi_to_en, translate_en_to_hi
from utils.repaymentLogic import preSeasonCalc
from FT_model.model import FineTunedLlama
from models.stt import load_asr_model

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"

current_dir = os.path.dirname(__file__) 
GEN_FINETUNED_DIR = os.path.join(current_dir, "../FT_model/adapter")
FINANCE_FINETUNED_DIR = os.path.join(current_dir,"../FT_model/finance_adapter")

llama = FineTunedLlama(BASE_MODEL, GEN_FINETUNED_DIR)
finance_llama = FineTunedLlama(BASE_MODEL, FINANCE_FINETUNED_DIR)

# asr_pipe = pipeline(
#     "automatic-speech-recognition",
#     model="ARTPARK-IISc/whisper-tiny-vaani-hindi",
#     chunk_length_s=30,
#     device=0
# )
# asr_pipe.model.config.forced_decoder_ids = asr_pipe.tokenizer.get_decoder_prompt_ids(
#     language="hi", task="transcribe"
# )
asr_pipe = load_asr_model()


# Temporary in-memory store for repayment notifications
repayment_notifications = []

huggingFaceAuth()

@app.route('/')
def index():
    return render_template("index.html", notifications=repayment_notifications)

@app.route('/notification')
def notification_detail():
    global repayment_notifications
    revenue = request.args.get('revenue')
    expenses = request.args.get('expenses')
    net_cash_flow = request.args.get('net_cash_flow')
    loan_repayment = request.args.get('loan_repayment')
    notif_dict = {
        "revenue": f"{float(revenue):.2f}" if revenue is not None else None,
        "expenses": f"{float(expenses):.2f}" if expenses is not None else None,
        "net_cash_flow": f"{float(net_cash_flow):.2f}" if net_cash_flow is not None else None,
        "loan_repayment": f"{float(loan_repayment):.2f}" if loan_repayment is not None else None
    }

    repayment_notifications.append(notif_dict)
    return render_template("index.html", notifications=repayment_notifications)

@app.route('/notification_page')
def notification_page():
    # revenue = request.args.get('revenue')
    # expenses = request.args.get('expenses')
    # net_cash_flow = request.args.get('net_cash_flow')
    # loan_repayment = request.args.get('loan_repayment')

    # notif = {
    #     "revenue": revenue,
    #     "expenses": expenses,
    #     "net_cash_flow": net_cash_flow,
    #     "loan_repayment": loan_repayment
    # }
    return render_template("repayment.html")

@app.route('/get_insurance')
def get_insurance():
    pass 


@app.route('/upload_audio', methods=['POST'])
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


@app.route('/submit_query', methods=['POST'])
def submit_query():
    query = request.form.get("query")

    print("Request form data:", request.form)

    if not query:
        return jsonify({"message": "No query provided"}), 400
    
    response = llama.ask(query)

    if "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1].strip()

    # Translate response to Hindi
    response = translate_en_to_hi(response)
    
    return jsonify({"message": response})

@app.route('/submit_finance_query', methods=['POST'])
def submit_finance_query():
    query = request.form.get("query")
    if not query:
        return jsonify({"message": "No query provided"}), 400
    
    response = finance_llama.ask(query)

    if "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1].strip()

    return jsonify({"message": response})


@app.route('/submit_initial_inputs', methods=['POST'])
def submit_initial_inputs():
    # Get form inputs
    district = request.form.get("district").strip().title()
    crop = request.form.get("crop").strip().title()
    year = int(request.form.get("year"))
    area = float(request.form.get("area"))
    loan_amount = float(request.form.get("loan"))
    interest_rate = float(request.form.get("interest"))
    month = request.form.get("month")

    if month == "November":
        predicted_yield = preSeasonCalc(
            area=area,
            district=district,
            crop=crop,
            year=year,
            monthly_expenses=10000,  # Default value, can be adjusted
            tenure=6,  # Default value, can be adjusted
            Insurance_premium=5000,  # Default value, can be adjusted
            Input_cost=30000,  # Default value, can be adjusted
            off_farm_income=8000,  # Default value, can be adjusted
            interest_rate=interest_rate,
            principal=loan_amount
        )
        return redirect(url_for(
            'notification_detail',
            revenue=predicted_yield['revenue'],
            expenses=predicted_yield['expenses'],
            net_cash_flow=predicted_yield['net_cash_flow'],
            loan_repayment=predicted_yield['loan_repayment']
        ))

    else:
        # Get weather and indices data for the selected year & district
        weather_df = calculate_weather_data(year, district)   # should return dict or DataFrame
        indices_df = calculate_indices_data(year, district)   # should return dict or DataFrame
    
        # Get area if a match exists, else fallback
        area_district = calulateArea(district, crop, year)
        if area_district is None:
            area_district = area

        predicted_yield = calculateYieldPred(
            weather_df, 
            indices_df, 
            area_district, 
            crop, 
            district
        )
    # Return the predicted yield

    return jsonify({
        "predicted_yield": predicted_yield,
        "message": f"Predicted Yield {predicted_yield} for {crop} in {district} for year {year}"
    })



if __name__ == "__main__":
    app.run(debug=True)
