import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv 

load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

DATA_FOLDER = "../scripts/final_output" 

# --- 🎯 DEFINE YOUR DESIRED COLUMNS HERE ---
# This set defines the ONLY columns the script will use.
# Any other fields in the JSON will be ignored.
REQUIRED_COLUMNS = {
    "refined_question",
    "answer",
    "difficulty",
    "original_question",
    "role",
    "skill",
    "source",
    "answer_code"
}

FILENAMES_TO_UPLOAD = [

    "AI_ML_Architect_refined.json",
    "Big_Data_Engineer_refined.json",
    "Blockchain_Developer_refined.json",
    "Business_Intelligence_BI_Analyst_refined.json",
    "Cloud_Architect_Engineer_refined.json",
    "Cybersecurity_Specialist_Analyst_refined.json",
    "Data_Analyst_refined.json",
    "Data_Engineer_refined.json",
    "Data_Scientist__GenAI_Developer__AI_Engineer_refined.json",
    "Database_Administrator_DBA_refined.json",
    "DevOps_Engineer_refined.json",
    "Full-stack_Developer_refined.json",
    "IT_Project_Manager_refined.json",
    "Mobile_Application_Developer_refined.json",
    "Prompt_Engineer_refined.json",
    "Site_Reliability_Engineer_SRE_refined.json",
    "Software_Architect_refined.json",
    "Software_Development_Engineer_SDE_refined.json",
    "UI_UX_Designer_refined.json",
    "Embedded_Systems_Engineer_refined.json",
    "Game_Developer_refined.json",
    "QA_Test_Automation_Engineer_refined.json",
    "Quantitative_Developer_HFT_Developer_refined.json",
    "Robotics_Engineer_refined.json"
]

# --- Main Script ---
def upload_listed_data():
    """
    Reads data, standardizes it against REQUIRED_COLUMNS, and uploads it to Supabase.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY not found in your .env file.")
        return

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Successfully connected to Supabase.")

        for filename in FILENAMES_TO_UPLOAD:
            file_path = os.path.join(DATA_FOLDER, filename)
            print(f"\n--- Processing file: {file_path} ---")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not isinstance(data, list):
                    print(f"⚠️ Warning: Skipping {file_path} because its content is not a list of objects.")
                    continue

                print(f"Found {len(data)} records to process and standardize.")

                # --- NEW STANDARDIZATION LOGIC ---
                standardized_data = []
                for original_record in data:
                    new_record = {}
                    # Build a new record using only the required columns
                    for column in REQUIRED_COLUMNS:
                        # Use .get() to safely get a value. If the key is missing, it returns None (null).
                        new_record[column] = original_record.get(column, None)
                    standardized_data.append(new_record)

                # Insert the fully standardized data into the Supabase table
                response = supabase.table('interview_questions').insert(standardized_data).execute()

                if hasattr(response, 'error') and response.error:
                    print(f"❌ Error uploading data from {file_path}: {response.error}")
                else:
                    print(f"✅ Successfully uploaded data from {file_path}.")

            except FileNotFoundError:
                print(f"❌ Error: File not found at '{file_path}'. Please check the filename and folder.")
            except json.JSONDecodeError:
                print(f"❌ Error: Could not decode JSON from '{file_path}'. Please check if the file is a valid JSON.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    upload_listed_data()