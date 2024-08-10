import json
import os
import pandas as pd
from flask import Flask, request, jsonify, render_template 
from dotenv import load_dotenv
import openai

from flask_cors import CORS
# Load environment variables from .env file
load_dotenv()
print(f"Loaded OpenAI API key: {os.getenv('OPENAI_API_KEY')}")

# Set your OpenAI API key directly from environment variable for security
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"])

# Load program data from CSV
def load_programs_from_csv(file_path):
    df = pd.read_csv(file_path, on_bad_lines='skip')
    programs = df.to_dict('records')
    return programs

programs = load_programs_from_csv('program_details (1).csv')

def find_program_info(program_name):
    for program in programs:
        if program_name.lower() in program["Degree"].lower():
            return program
    return None

@app.route('/')
def home():
    app.logger.info("Serving the home page.")
    app.logger.info(f"Current directory: {os.getcwd()}")
    app.logger.info(f"Templates directory contents: {os.listdir('templates')}")
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({"response": "Please provide a message."})

        program_info = handle_query(user_message)
        if program_info.startswith("Sorry"):
            response_text = call_openai_api(user_message)
        else:
            response_text = program_info

        return jsonify({"response": response_text})
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"response": f"An error occurred: {str(e)}"})

def handle_query(user_message):
    program_name = extract_program_name(user_message)
    query_type = extract_query_type(user_message)

    if not program_name:
        return "Sorry, I couldn't find any information about this program."

    program_info = find_program_info(program_name)

    if not program_info:
        return f"Sorry, I couldn't find any information about the program '{program_name}'."

    if 'deadline' in query_type.lower():
        return f"For {program_info['Degree']}:\n" + \
               f"Winter semester - Recommended start: {program_info.get('Application_deadline_Winter_semester_recommended_start', 'N/A')}, " + \
               f"Deadline for students requiring an entry visa: {program_info.get('Application_deadline_Winter_semester_entry_visa_required', 'N/A')}, " + \
               f"Deadline for students not requiring an entry visa: {program_info.get('Application_deadline_Winter_semester_no_entry_visa_required', 'N/A')}, " + \
               f"Early application deadline: {program_info.get('Application_deadline_Winter_semester_early_application_deadline', 'N/A')}.\n" + \
               f"Summer semester - Closing date: {program_info.get('Application_deadline_Summer_semester_closing_date', 'N/A')}, " + \
               f"Deadline for students requiring an entry visa: {program_info.get('Application_deadline_Summer_semester_entry_visa_required', 'N/A')}."
    elif 'tuition' in query_type.lower():
        return f"The tuition fees per semester for the {program_info['Degree']} are {program_info.get('Tuition_fees_per_semester_in_EUR', 'N/A')}."
    elif 'language' in query_type.lower():
        return f"The teaching language for the {program_info['Degree']} is {program_info.get('Teaching_language', 'N/A')}."
    elif 'scholarship' in query_type.lower():
        return f"Scholarship details for {program_info['Degree']}:\n" + \
               f"{program_info.get('Scholarship_details', 'No scholarship details available.')}"
    else:
        return f"I have found the following information about {program_info['Degree']}:\n" + \
               f"Languages: {program_info.get('Languages', 'N/A')}\n" + \
               f"Duration: {program_info.get('Programme_duration', 'N/A')}\n" + \
               f"Starting: {program_info.get('Beginning', 'N/A')}\n" + \
               f"Tuition Fees: {program_info.get('Tuition_fees_per_semester_in_EUR', 'N/A')}\n" + \
               f"Scholarship: {program_info.get('Scholarship_details', 'No scholarship details available.')}"

def call_openai_api(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that provides information about graduate programs."},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message["content"].strip()

def extract_program_name(user_message):
    for program in programs:
        if program["Degree"].lower() in user_message.lower():
            return program["Degree"]
    return None

def extract_query_type(user_message):
    query_keywords = ['deadline', 'tuition', 'language', 'scholarship']
    for keyword in query_keywords:
        if keyword in user_message.lower():
            return keyword
    return 'general'

if __name__ == '__main__':
    app.run(debug=True)
