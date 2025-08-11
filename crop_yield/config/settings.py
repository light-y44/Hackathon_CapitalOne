import os
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT")
GCS_BUCKET = os.getenv("GCS_BUCKET")

ROI_COORDS = eval(os.getenv("ROI_COORDS"))  # polygon coords
START_DATE = os.getenv("START_DATE")
END_DATE = os.getenv("END_DATE")
CLOUD_THRESH = int(os.getenv("CLOUD_THRESH", 20))
