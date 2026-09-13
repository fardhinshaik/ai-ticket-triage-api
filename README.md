# AI-Driven IT Ticket Triage API 🚀

A Python-based REST API microservice that automates IT operations by processing unstructured user complaints, utilizing Generative AI for entity extraction, and generating real-time analytics. 

## 🏗️ Architecture Flow
**User** ➡️ `Flask /triage` ➡️ `Groq LLM API` ➡️ `MySQL Database` ➡️ `/analytics Dashboard`

## ✨ Features
* **AI Entity Extraction:** Converts natural language (e.g., "I spilled coffee on my laptop") into structured JSON.
* **Fault-Tolerant Routing:** Custom Python fallback logic assigns "High" urgency to emergency keywords even if the AI API fails.
* **Complete CRUD Capabilities:** RESTful endpoints to create (`POST`), read (`GET`), and analyze ticket data.
* **Input Validation & Error Handling:** Prevents blank or malformed data from reaching the database.

## 🛠️ Tech Stack
* **Backend:** Python 3.12, Flask, REST APIs
* **Database:** MySQL, `mysql-connector-python`
* **AI/LLM:** Groq API (`openai/gpt-oss-20b` open-source model)
* **Environment:** `python-dotenv` for credential security

## 📸 Endpoints & Previews

### 1. Data Processing (`POST /triage`)
*Validates input, calls AI for categorization, and persists to MySQL.*
[INSERT POSTMAN SCREENSHOT HERE]

### 2. Operational Analytics (`GET /analytics`)
*Aggregates data to show real-time ticket distributions and bottlenecks.*
[INSERT BROWSER ANALYTICS SCREENSHOT HERE]

### 3. Database View
[INSERT MYSQL WORKBENCH SCREENSHOT HERE]

## 🧠 Prompt Engineering
The system utilizes a strict zero-shot prompt to guarantee predictable JSON outputs:
> *"You are an IT Support AI. Extract the Category (Hardware, Software, Network, Access), Urgency (Low, Medium, High), and the specific Hardware name (or 'None'). Output strictly in JSON format without markdown."*

## 🚀 How to Run Locally

1. **Clone the repo and install dependencies:**
   ```bash
   git clone <your-repo-url>
   cd "AI-Driven IT Ticket Triage API"
   pip install -r requirements.txt