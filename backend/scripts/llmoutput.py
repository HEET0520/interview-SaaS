import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq
import re

# -------------------------------
# Setup logging
# -------------------------------
LOG_FILE = "refinement_pipeline.log"
# Clear the log file at the start of a new run
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# -------------------------------
# Load API key and initialize client
# -------------------------------
try:
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in .env file.")
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    logging.error(f"Failed to initialize API client: {e}")
    exit(1) # Exit if the API key isn't found

# -------------------------------
# Config
# -------------------------------
# Assumes the script is in the same directory as the input/output folders
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "output_new"
OUTPUT_DIR = BASE_DIR / "final_output"
OUTPUT_DIR.mkdir(exist_ok=True) # Ensure the output directory exists

BATCH_SIZE = 15
MODEL =  "llama-3.1-8b-instant"  #"gemma2-9b-it"#"deepseek-r1-distill-llama-70b" #"llama-3.3-70b-versatile" # Using a known stable model from Groq
API_TIMEOUT = 120 # Seconds to wait for API response

# -------------------------------
# System Prompt
# -------------------------------
# -------------------------------
# System Prompt (REVISED AND IMPROVED)
# -------------------------------
SYSTEM_PROMPT = """
You are an expert technical interviewer and educator. Your task is to process interview questions and provide high-quality, refined versions with detailed answers.

For EACH question, you must follow this exact two-step process:

**Step 1: Categorize the Question**
First, determine if the question is primarily **Conceptual** or **Coding**.
- **Conceptual** questions ask for definitions, explanations, comparisons, or theory (e.g., "What is overfitting?", "Compare REST APIs and GraphQL.").
- **Coding** questions ask for an algorithm, a function implementation, or a practical solution in code (e.g., "Write a function to reverse a string.", "How do you find a duplicate number in an array?").

**Step 2: Generate the Answer Based on the Category**
- **If the question is Conceptual**, your answer MUST be a clear, text-only explanation. Use Markdown for formatting, bullet points, and examples. You are **strictly forbidden** from including any code blocks (i.e., ```) in your answer.
- **If the question is Coding**, your answer MUST first explain the logic or algorithm step-by-step, and then provide a clean, well-commented code block to demonstrate the solution.

Finally, assign a difficulty level: "Beginner", "Intermediate", or "Advanced".

Your final output MUST be a valid JSON array of objects. Each object in the array must strictly conform to the following structure:
{
  "refined_question": "The improved question text.",
  "answer": "The detailed answer in Markdown format, following the rules above.",
  "difficulty": "One of 'Beginner', 'Intermediate', or 'Advanced'."
}

Do NOT include any text, explanations, or markdown outside of the final JSON array.
"""

# -------------------------------
# NEW: Robust JSON Parsing Function
# This is the core fix for your problem.
# -------------------------------
def parse_llm_json_output(text: str) -> List[Dict[str, Any]]:
    """
    Finds and parses all JSON objects embedded within a string.
    This is much more robust than trying to parse the whole string as one.
    """
    # Regex to find all occurrences of text between {...}, non-greedily
    json_object_pattern = re.compile(r'\{.*?\}', re.DOTALL)
    
    potential_json_strings = json_object_pattern.findall(text)
    
    parsed_objects = []
    for json_str in potential_json_strings:
        try:
            # Clean up newlines and backslashes that might break parsing
            clean_str = json_str.replace('\n', ' ').replace('\r', '')
            parsed_objects.append(json.loads(clean_str))
        except json.JSONDecodeError as e:
            logging.warning(f"Could not parse a JSON object: {e}\nProblematic string: {json_str[:100]}...")
            
    return parsed_objects

# -------------------------------
# Process batch of questions (updated)
# -------------------------------
def process_batch(questions_batch: List[Dict], role: str) -> List[Dict]:
    """
    Sends a batch of questions to the LLM and processes the response.
    """
    logging.info(f"Processing batch of {len(questions_batch)} questions for role: {role}")

    user_prompt = f"Process the following interview questions for the role: **{role}**.\n\n"
    for idx, qa in enumerate(questions_batch, 1):
        # Constructing a clean list for the prompt
        user_prompt += f"{idx}. Question: \"{qa['question']}\"\n"
        # Optional: include skill if available and useful
        # user_prompt += f"   Skill: {qa.get('skill', 'N/A')}\n"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=8000,
            timeout=API_TIMEOUT,
        )
        content = response.choices[0].message.content
        
        # Use the new robust parsing function
        refined_data = parse_llm_json_output(content)

        if not refined_data:
            # Save the raw content for manual review if parsing still fails
            fallback_path = OUTPUT_DIR / f"{role.replace(' ', '_')}_FAILED_RAW_{int(time.time())}.txt"
            with open(fallback_path, "w", encoding="utf-8") as f:
                f.write(content)
            logging.error(f"Could not parse response for role {role}. Saved raw output to {fallback_path}")
            return [] # Return empty list to signify failure for this batch

        # Merge original metadata with the refined data
        if len(refined_data) != len(questions_batch):
            logging.warning(f"Mismatch in count for role {role}. "
                            f"Sent {len(questions_batch)} questions but received {len(refined_data)} answers.")
        
        # Safely merge metadata, even if counts mismatch
        for i, refined_item in enumerate(refined_data):
            if i < len(questions_batch):
                original_item = questions_batch[i]
                refined_item["original_question"] = original_item["question"]
                refined_item["role"] = role
                refined_item["skill"] = original_item.get("skill", "N/A")
                refined_item["source"] = original_item.get("source", "N/A")

        logging.info(f"Successfully processed batch for role: {role}")
        return refined_data

    except Exception as e:
        logging.error(f"An API error occurred while processing batch for role {role}: {e}")
        return [] # Return empty list on API error

# -------------------------------
# Process one JSON file (updated)
# -------------------------------
def refine_role_json(input_path: Path):
    """
    Loads a JSON file, processes it in batches, and saves the refined output.
    """
    role = input_path.stem.replace("_", " ")
    logging.info(f"--- Starting new role: {role} ---")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Could not read or parse input file {input_path.name}: {e}")
        return

    total_questions = len(data)
    if total_questions == 0:
        logging.warning(f"Input file {input_path.name} is empty. Skipping.")
        return
        
    total_batches = (total_questions + BATCH_SIZE - 1) // BATCH_SIZE
    logging.info(f"Total questions: {total_questions} ({total_batches} batches)")

    refined_results = []
    start_time = datetime.now()

    for batch_idx, start_idx in enumerate(range(0, total_questions, BATCH_SIZE), start=1):
        end_idx = start_idx + BATCH_SIZE
        batch = data[start_idx:end_idx]
        logging.info(f"Processing Batch {batch_idx}/{total_batches} (questions {start_idx + 1}-{min(end_idx, total_questions)})")

        refined_batch = process_batch(batch, role)
        if refined_batch:
            refined_results.extend(refined_batch)

        # Progress and ETA calculation
        elapsed_seconds = (datetime.now() - start_time).total_seconds()
        avg_time_per_batch = elapsed_seconds / batch_idx
        remaining_batches = total_batches - batch_idx
        eta_seconds = avg_time_per_batch * remaining_batches
        eta = datetime.now() + timedelta(seconds=eta_seconds)

        logging.info(f"Progress: {len(refined_results)}/{total_questions} questions refined. "
                     f"Batch {batch_idx}/{total_batches} complete. "
                     f"ETA: {eta.strftime('%H:%M:%S')}")

        # Rate limit sleep to be polite to the API
        if batch_idx < total_batches:
            time.sleep(20)

    # Save the final refined file
    if refined_results:
        output_path = OUTPUT_DIR / f"{input_path.stem}_refined.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(refined_results, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully saved refined data for {role} to {output_path}")
    else:
        logging.error(f"No results were generated for {role}. Check logs for errors.")

# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    json_files = list(INPUT_DIR.glob("*.json"))
    logging.info(f"Found {len(json_files)} JSON files to process in {INPUT_DIR}")
    
    for json_file in json_files:
        # Simple check to avoid re-processing already refined files
        if "_refined" not in json_file.stem and "_FIXED" not in json_file.stem:
            refine_role_json(json_file)
        else:
            logging.info(f"Skipping already processed file: {json_file.name}")
            
    logging.info("--- All roles processed successfully. ---")