from flask import Flask, render_template, request, jsonify, redirect, url_for
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

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),  '..')))

from utils.calcWeather import calculate_weather_data
from utils.calIndx import calculate_indices_data
from utils.utils import  calulateArea, calculateYieldPred, huggingFaceAuth, translate_hi_to_en, translate_en_to_hi
from utils.repaymentLogic import preSeasonCalc
from FT_model.model import FineTunedLlama
from models.stt import load_asr_model
from models.repayment import FarmInputs, FarmDebtManager

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"

current_dir = os.path.dirname(__file__) 
GEN_FINETUNED_DIR = os.path.join(current_dir, "../FT_model/adapter")
FINANCE_FINETUNED_DIR = os.path.join(current_dir,"../FT_model/finance_adapter")

llama = FineTunedLlama(BASE_MODEL, GEN_FINETUNED_DIR)
finance_llama = FineTunedLlama(BASE_MODEL, FINANCE_FINETUNED_DIR)

asr_pipe = load_asr_model()


# Temporary in-memory store for repayment notifications
repayment_notifications = []

huggingFaceAuth()

gl_rec = None
gl_baseline = None

@app.route('/')
def index():
    return render_template("index.html", notifications=repayment_notifications)

@app.route('/notification_page')
def notification_page():
    baseline_fields = [
        "gross_revenue",
        "net_revenue_after_marketing",
        "net_farm_income",
        "seasonal_offfarm_income",
        "total_available",
        "seasonal_household_need",
        "emi_monthly_baseline",
        "seasonal_loan_outflow_baseline",
        "surplus_before_loan",
        "surplus_after_loan",
        "debt_sustainability_index"
    ]
    baseline = {field: request.args.get(field) for field in baseline_fields}

    recs_raw = request.args.get("recommendations", "[]")
    try:
        recommendations = json.loads(recs_raw)
        print("Decoded recommendations:", recommendations)
    except Exception:
        print("I am here")
        recommendations = []

    return render_template("repayment.html", baseline=baseline, recommendations=recommendations)

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
    
    response = llama.ask(query, "agriculture")

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
    
    response = finance_llama.ask(query, "finance", inputs = [gl_baseline, gl_rec])

    if "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1].strip()

    return jsonify({"message": response})




def to_serializable(val):
    """Convert common non-JSON types to JSON-serializable Python primitives."""
    # None
    if val is None:
        return None

    # Numpy scalars
    if isinstance(val, (np.generic,)):
        return val.item()

    # Numpy arrays -> lists
    if isinstance(val, (np.ndarray,)):
        return [to_serializable(x) for x in val.tolist()]

    # Built-in collections
    if isinstance(val, (list, tuple, set)):
        return [to_serializable(x) for x in val]

    if isinstance(val, dict):
        return {str(k): to_serializable(v) for k, v in val.items()}

    # Decimal -> float or str (Decimal may be large-precision)
    if isinstance(val, Decimal):
        return float(val)

    # datetimes
    if isinstance(val, (datetime, date)):
        return val.isoformat()

    # floats with Inf/NaN (JSON doesn't support Infinity/NaN)
    if isinstance(val, float):
        if math.isinf(val) or math.isnan(val):
            # Choose how to map these — I use None, you can use "Infinity" string if you prefer
            return None
        return val

    # ints, bools, str are fine
    if isinstance(val, (int, bool, str)):
        return val

    # custom objects: attempt to serialize __dict__
    if hasattr(val, "__dict__"):
        return to_serializable(vars(val))

    # fallback: try repr (safe) OR string
    try:
        return str(val)
    except Exception:
        return None

def serialize_recommendations(recs):
    """Serialize recommendations or any nested structure to JSON-safe Python types."""
    return to_serializable(recs)

def debug_json(obj):
    try:
        return json.dumps(obj)
    except TypeError as e:
        # print problematic types (walk small sample)
        def walk(x, path="root"):
            if isinstance(x, dict):
                for k,v in x.items():
                    walk(v, f"{path}.{k}")
            elif isinstance(x, (list, tuple, set)):
                for i, v in enumerate(x):
                    walk(v, f"{path}[{i}]")
            else:
                if not isinstance(x, (str, int, float, bool, type(None))):
                    print("Non-serializable found at", path, "type:", type(x), "value:", repr(x))
        walk(obj)
        raise


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
    off_farm_income = request.form.get("non-farm-inc", 0.0, type=float)
    input_cost = request.form.get("input-cost", 0.0, type=float)
    monthly_expenses = request.form.get("monthly-exp", 0.0, type=float)
    tenure = request.form.get("tenure", 0, type=int)
    insurance_premium = request.form.get("ins-prem", 0.0, type=float)

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
    else:
        print("Hello!")
        # weather_df = calculate_weather_data(year, district)
        # indices_df = calculate_indices_data(year, district)
        # area_district = calulateArea(district, crop, year) or area

        # predicted_yield, predicted_price = calculateYieldPred(
        #     weather_df, 
        #     indices_df, 
        #     area_district, 
        #     crop, 
        #     district
        # )
    predicted_price = 2400
    predicted_yield = 3.0

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

    gl_rec = recs_serialized
    gl_baseline = baseline_serialized

    return jsonify({
        "recommendations": recs_serialized,
        "baseline": baseline_serialized,
        "scenarios": scenarios_serialized,
        "message": f"Predicted Yield {predicted_yield} for {crop} in {district} for year {year}"
    })


if __name__ == "__main__":
    app.run(debug=True)
