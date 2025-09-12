import os
import json

# --- Configuration ---

# The folder where your JSON files are located. This is now used for both reading and writing.
DATA_FOLDER = "F:/interview-SaaS/backend/scripts/final_output"

# The list of all your filenames to be processed.
FILENAMES_TO_PROCESS = [
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

# --- Helper Function for Cleaning Text ---
def clean_answer_text(text: str) -> str:
    """
    Cleans the text by removing only the asterisks, preserving all whitespace.
    """
    if not isinstance(text, str):
        return text
    return text.replace('*', '')


# --- Main Script for In-Place Processing ---
def preprocess_files_inplace():
    """
    Reads all specified JSON files, cleans the 'answer' field,
    and saves the results back to the original file (overwrite).
    """
    for filename in FILENAMES_TO_PROCESS:
        # This path is now used for both reading and writing
        file_path = os.path.join(DATA_FOLDER, filename)
        
        print(f"\n--- Processing (in-place): {filename} ---")

        try:
            # Step 1: Read the entire file's content into memory
            with open(file_path, 'r', encoding='utf-8') as f_in:
                original_data = json.load(f_in)

            # Step 2: Process the data in memory
            cleaned_data = []
            for record in original_data:
                new_record = record.copy()
                if 'answer' in new_record:
                    new_record['answer'] = clean_answer_text(new_record['answer'])
                cleaned_data.append(new_record)

            # Step 3: Write the cleaned data back to the SAME file
            with open(file_path, 'w', encoding='utf-8') as f_out:
                json.dump(cleaned_data, f_out, indent=4, ensure_ascii=False)

            print(f"✅ Successfully updated file in-place: {file_path}")

        except FileNotFoundError:
            print(f"❌ Error: File not found at '{file_path}'. Skipping.")
        except Exception as e:
            print(f"❌ An unexpected error occurred while processing {filename}: {e}")

if __name__ == "__main__":
    print("Starting in-place preprocessing. Your original files will be overwritten.")
    preprocess_files_inplace()
    print("\nIn-place preprocessing complete!")