import time
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import pooling  # PHASE 1: Connection Pooling
import requests
import json
import os
from dotenv import load_dotenv
from flask_limiter import Limiter  # PHASE 1: Rate Limiting
from flask_limiter.util import get_remote_address
import csv
from datetime import datetime

# Load the environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# --- PHASE 1: RATE LIMITING CONFIGURATION ---
# This protects your API from DDoS attacks and saves your Groq free tier
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")         

# --- PHASE 1: CONNECTION POOLING CONFIGURATION ---
# Instead of opening/closing a new connection for every single request,
# we create a "pool" of 5 connections that get reused efficiently.
# --- PHASE 1: CONNECTION POOLING CONFIGURATION ---
dbconfig = {
    "host": "localhost",
    "user": "root",          
    "password": MYSQL_PASSWORD,  
    "database": "ticket_triage"
}

db_pool = None
try:
    # Try to build the pool on startup
    db_pool = pooling.MySQLConnectionPool(
        pool_name="triage_pool",
        pool_size=5,
        **dbconfig
    )
    print("Database pool initialized successfully.")
except Exception as e:
    # If the DB is down on startup, don't crash the app! Just log a warning.
    print(f"WARNING: Database pool failed to initialize on startup: {e}")

def get_db_connection():
    # When a route asks for a connection, check if the pool exists
    if db_pool is None:
        raise Exception("Database connection pool is offline.")
    return db_pool.get_connection()

def call_ai_api(text):
    """Calls Groq API to classify the IT ticket with exponential backoff and timeouts."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are an IT support classifier. 
    Read the user complaint and return ONLY a valid JSON object with exactly three keys:
    - "Category" (e.g., Hardware, Software, Network, Access)
    - "Urgency" (Low, Medium, High)
    - "Hardware" (Extract the hardware name if mentioned, otherwise "None")
    Do not output any introductory text, markdown blocks, or explanations. Only output the JSON dictionary."""

    payload = {
        "model": "openai/gpt-oss-20b", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.0 
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Added a 4-second timeout. If Groq doesn't answer, we drop the connection.
            response = requests.post(url, headers=headers, json=payload, timeout=4)
            
            # If Groq is down or rate limits us, trigger the retry loop
            if response.status_code != 200:
                print(f"Groq API Error (Attempt {attempt + 1}): {response.status_code}")
                time.sleep(2 ** attempt) # Waits 1s, then 2s, then 4s
                continue
                
            response_data = response.json()
            ai_text = response_data['choices'][0]['message']['content'].strip()
            ai_text = ai_text.replace("```json", "").replace("```", "").strip()
            
            return json.loads(ai_text)
            
        except requests.exceptions.Timeout:
            print(f"AI API Timeout (Attempt {attempt + 1})")
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"AI API Error (Attempt {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
            
    # PHASE 2 FALLBACK: If all 3 retries fail, seamlessly degrade to default routing
    print("All AI retries failed. Triggering Graceful Degradation Fallback...")
    return {"Category": "Unknown", "Urgency": "Medium", "Hardware": "Unknown"}

@app.route('/triage', methods=['POST'])
@limiter.limit("10 per minute") # PHASE 1: Protects this specific endpoint
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

    # 2. Hardcoded Python Logic 
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

    except Exception as db_error:
        print(f"CRITICAL DATABASE ERROR: {db_error}")
        
        # PHASE 3: Dead-Letter Queue (Save to local file so data isn't lost)
        with open("dead_letter_queue.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now(), raw_text, category, urgency, hardware, str(db_error)])
            
        # PHASE 3: Emergency Webhook Alert
        # You can easily point this URL to a Catch Webhook node in n8n to instantly
        # trigger an automated workflow that alerts you on Slack/Email.
        webhook_url = "https://webhook.site/a83b3b47-7d66-41ee-91b5-a00f750b4f54"
        webhook_payload = {
            "alert": "Database Offline",
            "error_details": str(db_error),
            "recovered_ticket": raw_text
        }
        
        try:
            # Fire the webhook with a short timeout so it doesn't hang the system
            requests.post(webhook_url, json=webhook_payload, timeout=2)
        except:
            print("Failed to dispatch emergency webhook.")

        # Still return a 202 Accepted so the user's frontend knows the ticket was caught
        return jsonify({
            "message": "Ticket safely queued locally due to database outage.",
            "structured_data": {"category": category, "urgency": urgency, "hardware": hardware}
        }), 202

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Generates a real-time analytics report of IT tickets."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category")
        category_data = dict(cursor.fetchall())
        
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
        cursor = conn.cursor(dictionary=True) 
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