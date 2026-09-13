from flask import Flask, request, jsonify
import mysql.connector
import requests
import json
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")         


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          
        password=MYSQL_PASSWORD,  
        database="ticket_triage"
    )

def call_ai_api(text):
    """Calls Groq API to classify the IT ticket using a strict prompt."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # This is the "Prompt Engineering" you will talk about in the interview
    system_prompt = """You are an IT support classifier. 
    Read the user complaint and return ONLY a valid JSON object with exactly three keys:
    - "Category" (e.g., Hardware, Software, Network, Access)
    - "Urgency" (Low, Medium, High)
    - "Hardware" (Extract the hardware name if mentioned, otherwise "None")
    Do not output any introductory text, markdown blocks, or explanations. Only output the JSON dictionary."""

    payload = {
        "model": "openai/gpt-oss-20b",  # Updated active model!
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.0 
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        print("GROQ RESPONSE:", response_data)
        # Extract the text from the AI response
        ai_text = response_data['choices'][0]['message']['content'].strip()
        ai_text = ai_text.replace("```json", "").replace("```", "").strip()
        
        # Parse it into a Python dictionary
        return json.loads(ai_text)
    except Exception as e:
        print("AI API Error:", e)
        # Fallback if API fails
        return {"Category": "Unknown", "Urgency": "Medium", "Hardware": "Unknown"}

@app.route('/triage', methods=['POST'])
def triage_ticket():
    data = request.get_json()
    raw_text = data.get("complaint", "")
    
    if not raw_text or len(raw_text.strip()) < 5:
        return jsonify({"error": "Invalid input. Complaint must be at least 5 characters long."}), 400

    # 1. AI structuring
    ai_result = call_ai_api(raw_text)
    category = ai_result.get("Category", "Unknown")
    urgency = ai_result.get("Urgency", "Low")
    hardware = ai_result.get("Hardware", "None")

    # 2. Hardcoded Python Logic (Overrides AI for safety - interviewers love this)
    critical_keywords = ["cracked", "spilled water", "dead", "smoke", "broken"]
    if any(word in raw_text.lower() for word in critical_keywords):
        urgency = "High"

    # 3. Save to MySQL
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO tickets (raw_complaint, category, urgency, extracted_hardware) VALUES (%s, %s, %s, %s)"
        val = (raw_text, category, urgency, hardware)
        cursor.execute(sql, val)
        conn.commit()
        ticket_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Ticket processed successfully",
            "ticket_id": ticket_id,
            "structured_data": {"category": category, "urgency": urgency, "hardware": hardware}
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Generates a real-time analytics report of IT tickets."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Get breakdown by Category
        cursor.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category")
        category_data = dict(cursor.fetchall())
        
        # 2. Get breakdown by Urgency
        cursor.execute("SELECT urgency, COUNT(*) FROM tickets GROUP BY urgency")
        urgency_data = dict(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "report_type": "IT Operations Analytics",
            "total_tickets_processed": sum(category_data.values()),
            "category_breakdown": category_data,
            "urgency_breakdown": urgency_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/tickets', methods=['GET'])
def get_recent_tickets():
    """Returns the 20 most recent tickets."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # Returns rows as dictionaries
        cursor.execute("SELECT id, raw_complaint, category, urgency, extracted_hardware, created_at FROM tickets ORDER BY id DESC LIMIT 20")
        tickets = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"recent_tickets": tickets}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Returns a single ticket by its ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, raw_complaint, category, urgency, extracted_hardware, created_at FROM tickets WHERE id = %s", (ticket_id,))
        ticket = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if ticket:
            return jsonify({"ticket": ticket}), 200
        return jsonify({"error": "Ticket not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
if __name__ == '__main__':
    app.run(debug=True, port=5000)