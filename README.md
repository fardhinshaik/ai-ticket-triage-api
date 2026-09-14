# AI-Driven IT Ticket Triage API 🚀

A robust, enterprise-grade Python REST API microservice that automates IT operations by processing unstructured user complaints. It utilizes Generative AI for entity extraction, fortified with advanced fault tolerance, rate limiting, and a zero-data-loss fallback architecture.

## 🏗️ Architecture Flow

**Primary Route (Healthy System):**
`User` ➡️ `Flask-Limiter` ➡️ `Flask /triage` ➡️ `Groq LLM API` ➡️ `MySQL Connection Pool` ➡️ `Analytics Dashboard`

**Disaster Recovery Route (Outage Handling):**
`Groq AI Timeout` ➡️ `Exponential Backoff` ➡️ `Python Keyword Fallback` ➡️ `MySQL Down` ➡️ `Dead-Letter Queue (.csv) + Emergency Webhook (webhook.site)`

## ✨ Core Features

* **AI Entity Extraction:** Converts natural language (e.g., "I spilled coffee on my laptop") into structured JSON via zero-shot prompting.
* **Security & Traffic Control:** Defends against DDoS attacks and API rate abuse using `Flask-Limiter` (configured for 10 requests/minute per endpoint).
* **High-Availability & Fault Tolerance:** Implements strict timeouts and exponential backoff loops for external LLM calls. If the AI goes offline, the system gracefully degrades to a hardcoded Python keyword-routing algorithm.
* **Zero-Data-Loss Database Logic:** Utilizes a `MySQLConnectionPool` for optimized server load. If the database crashes, tickets are instantly routed to a local Dead-Letter Queue (`dead_letter_queue.csv`) and an emergency alert webhook is fired.
* **Real-Time Analytics:** Custom `GET` endpoints aggregate SQL data to track operational bottlenecks and hardware failure rates.

## 🛠️ Tech Stack

* **Backend:** Python 3.12, Flask, REST APIs, Flask-Limiter, Requests
* **Database:** MySQL, `mysql-connector-python` (Connection Pooling)
* **AI/LLM:** Groq API (`openai/gpt-oss-20b` open-source model)
* **Automation:** Webhooks (currently utilizing `webhook.site` for real-time alert monitoring)
* **Environment:** `python-dotenv` for credential security

## 📸 Endpoints & Previews

### 1. Data Processing (`POST /triage`)
*Validates input, calls AI for categorization, and persists to MySQL. If MySQL is down, returns a `202 Accepted` and queues the data locally.*
[INSERT POSTMAN SCREENSHOT HERE]

### 2. Operational Analytics (`GET /analytics`)
*Aggregates data to show real-time ticket distributions and bottlenecks.*
[INSERT BROWSER ANALYTICS SCREENSHOT HERE]

### 3. Dead-Letter Queue & Webhook Alerts
*Captures lost data during database outages and triggers automated alerts.*
[INSERT WEBHOOK.SITE / CSV SCREENSHOT HERE]

## 🧠 Prompt Engineering

The system utilizes a strict zero-shot prompt to guarantee predictable JSON outputs, bypassing the need for complex output parsers:
> *"You are an IT Support AI. Extract the Category (Hardware, Software, Network, Access), Urgency (Low, Medium, High), and the specific Hardware name (or 'None'). Output strictly in JSON format without markdown."*

## 🚀 How to Run Locally

### 1. Clone the repository and install dependencies:
```bash
git clone <your-repo-url>
cd "AI-Driven IT Ticket Triage API"
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```
### 2. Configure Environment Variables:
Create a `.env` file in the root directory and add your secure credentials:
```env
GROQ_API_KEY=your_groq_api_key_here
MYSQL_PASSWORD=your_mysql_password_here
```
### 3. Setup the MySQL Database:
Create a database named `ticket_triage` and a table named `tickets`:

```sql
CREATE DATABASE ticket_triage;
USE ticket_triage;
CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    raw_complaint TEXT NOT NULL,
    category VARCHAR(50),
    urgency VARCHAR(20),
    extracted_hardware VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
### 4. Run the Server:
```bash
python app.py
```
### 5. Seed the Database (Optional):
Use the included testing script to simulate traffic and test the API rate limiter.

```bash
python seed.py
```
🔮 Future Enhancements
Workflow Automation (n8n): Transition the emergency webhooks from webhook.site to an n8n pipeline to trigger automated Slack or Gmail alerts for the on-call engineering team.

Unit Testing (pytest): Implement automated test suites to mock the Groq API and database connections, validating the fallback logic seamlessly in CI/CD pipelines.

Containerization (Docker): Package the application and its dependencies into a Docker container for standardized, cloud-agnostic deployment.