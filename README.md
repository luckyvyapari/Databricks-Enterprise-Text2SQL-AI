

<p align="center">
   <img src="images/Data%20bricks%20genie.jpeg" alt="Databricks Genie SQL Chatbot" width="600"/>
</p>

# Databricks-Enterprise-Text2SQL-AI

<p align="center">
   <b>Enterprise-Ready Text2SQL AI Chatbot for Databricks Genie</b><br>
   <i>Ask questions in natural language, get instant SQL and analytics from your Databricks data warehouse.</i>
</p>

---

## Step-by-step guide — from zero to working chatbot


## Folder Structure

```
databricks_genie_chatbot/
│
├── config/
│   └── .env.example        ← Copy this → rename to .env → fill in values
│
├── src/
│   └── genie_api.py        ← All Databricks API calls live here
│
├── ui/
│   └── app.py              ← Streamlit chatbot UI
│
└── requirements.txt        ← Python packages needed
```

---

## PART 1 — Databricks Setup (do this first, in your browser)

### Step 1 — Sign up and log in

1. Go to **https://www.databricks.com**
2. Click **Get Started Free** or **Try Databricks**
3. Choose your cloud provider — **Azure**, **AWS**, or **GCP**
4. Sign up with your email and complete registration
5. You will land on your **Databricks workspace homepage**

> You get **~40 free credits** when you sign up. Use them carefully.

---

### Step 2 — Load data into the Catalog

Your Genie chatbot needs data to work on.
We will use the **NYC Taxi sample data** — it is already inside Databricks.

1. In the left sidebar, click **Catalog**
2. Click **Create Catalog** → name it `demo` → click **Create**
3. Inside `demo`, click **Create Schema** → name it `taxi` → click **Create**
4. Now load the sample data:
   - Click on your `taxi` schema
   - Click **Create → Table**
   - Choose **Upload file** OR use the sample data path below

**Using sample data that already exists in Databricks:**

Open a new Notebook (Workspace → Create → Notebook) and run:

```python
# Copy sample NYC Taxi data into your catalog
spark.sql("CREATE TABLE IF NOT EXISTS demo.taxi.trips AS SELECT * FROM samples.nyctaxi.trips")
print("Table created!")
```

5. Run the cell — wait for it to finish
6. Go back to Catalog → `demo` → `taxi` — you should see the `trips` table

---

### Step 3 — Create a Genie Space

1. In the left sidebar, scroll down and click **Genie**
2. Click **New Genie Space**
3. In the **Select Tables** search box, type `trips`
4. Select `demo.taxi.trips`
5. Click **Create**

Your Genie Space is created. Now **fine-tune it** so answers are accurate.

---

### Step 4 — Fine-tune the Genie Space (MANDATORY)

**4a — Add a description**

1. Inside your Genie Space, click the **Settings** (gear) icon
2. In the **Description** field, type:
   ```
   This space answers analytical questions about New York City taxi trips.
   Data includes pickup/dropoff zones, fare amounts, trip distances,
   payment types, and timestamps from 2016.
   ```
3. Click **Save**

**4b — Add column descriptions**

1. Inside your Genie Space, click the **Data** tab
2. Click on each column name and add a description:

| Column | Description to add |
|---|---|
| `tpep_pickup_datetime` | Date and time when the passenger was picked up |
| `tpep_dropoff_datetime` | Date and time when the passenger was dropped off |
| `passenger_count` | Number of passengers in the taxi |
| `trip_distance` | Trip distance in miles |
| `pickup_zip` | ZIP code where the trip started |
| `dropoff_zip` | ZIP code where the trip ended |
| `fare_amount` | Base fare charged in US dollars |
| `tip_amount` | Tip amount in US dollars |
| `total_amount` | Total amount charged including all fees |
| `payment_type` | Payment method — 1=Credit card, 2=Cash, 3=No charge |

3. Click **Save** after each column

**4c — Add example SQL questions**

1. Click the **Instructions** tab
2. In the **SQL Queries** section, click **Add Query**
3. Add these examples:

```sql
-- Example 1: Total trips
SELECT COUNT(*) AS total_trips FROM demo.taxi.trips

-- Example 2: Average fare
SELECT ROUND(AVG(fare_amount), 2) AS avg_fare FROM demo.taxi.trips

-- Example 3: Top pickup zones
SELECT pickup_zip, COUNT(*) AS trips
FROM demo.taxi.trips
GROUP BY pickup_zip
ORDER BY trips DESC
LIMIT 10
```

4. Click **Save**

---

### Step 5 — Copy your Genie Space ID

1. With your Genie Space open, look at the **browser URL**
2. It will look like:
   ```
   https://adb-1234567890.azuredatabricks.net/genie/spaces/01abc123def456?o=789
   ```
3. Copy the part between the **last `/`** and the **`?`**
   ```
   01abc123def456   ← this is your GENIE_SPACE_ID
   ```
4. Save this somewhere — you will need it in the `.env` file

---

### Step 6 — Get your Host URL

1. Look at the same browser URL
2. Copy everything from `https://` up to and including `.net` (or `.com`)
   ```
   https://adb-1234567890.azuredatabricks.net   ← this is your DATABRICKS_HOST
   ```
3. Do **NOT** include anything after `.net`

---

### Step 7 — Generate your Access Token

1. Click your **profile icon** (top right corner of Databricks)
2. Click **Settings**
3. In the left menu, click **Developer**
4. Under **Access Tokens**, click **Manage**
5. Click **Generate New Token**
6. In the **Comment** field type: `genie-chatbot`
7. Leave the **Lifetime** as default (or set 90 days)
8. Click **Generate**
9. **COPY THE TOKEN NOW** — you cannot see it again after closing this dialog
   ```
   dapi1a2b3c4d5e6f7g8h9i0j   ← this is your DATABRICKS_TOKEN
   ```

> ⚠️ Never share this token. Never commit it to GitHub.

---

## PART 2 — Local Machine Setup

### Step 8 — Install Python packages

Open your terminal (Command Prompt, PowerShell, or Mac/Linux terminal):

```bash
# Navigate into the project folder
cd databricks_genie_chatbot
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

---

### Step 9 — Create your .env file

1. Go into the `config/` folder
2. Make a **copy** of `.env.example`
3. Rename the copy to `.env`
4. Open `.env` in any text editor and fill in your three values:

```bash
DATABRICKS_HOST=https://adb-1234567890.azuredatabricks.net
DATABRICKS_TOKEN=dapi1a2b3c4d5e6f7g8h9i0j
GENIE_SPACE_ID=01abc123def456
CHATBOT_NAME=NYC Taxi Analytics Assistant
```

5. Save the file

> ⚠️ Make sure the filename is exactly `.env` — not `.env.txt` or `env`.

---

### Step 10 — Test the connection (quick check)

Open a Python terminal inside the project folder and run:

```python
# Quick connection test — run this in terminal
python -c "
import sys, os
sys.path.insert(0, '.')
from src.genie_api import validate_credentials, ask_genie

ok, err = validate_credentials()
if not ok:
    print('FAIL:', err)
else:
    print('Credentials OK — testing Genie...')
    result = ask_genie('How many rows are in the dataset?')
    if result['status'] == 'ok':
        print('SUCCESS!')
        print('Answer:', result['answer'])
        print('SQL:', result['sql'])
    else:
        print('GENIE ERROR:', result['error'])
"
```

**Expected output:**
```
Credentials OK — testing Genie...
SUCCESS!
Answer: The dataset contains 21,932 trips.
SQL: SELECT COUNT(*) AS total_trips FROM demo.taxi.trips
```

If you see an error, check the error message and fix the relevant `.env` value.

---

### Step 11 — Run the chatbot

```bash
# From inside the databricks_genie_chatbot folder:
streamlit run ui/app.py
```

Your browser will open automatically at **http://localhost:8501**

You will see:
- A chat interface where you can type questions
- A sidebar showing your connection status
- Example question buttons to click
- Each answer shows the SQL Genie wrote

---

## PART 3 — What Each File Does

### `config/.env`
Stores your three secret credentials. Never commit this to GitHub.
Always add `config/.env` to your `.gitignore`.

### `src/genie_api.py`
All Databricks API logic. Three functions inside:
- `validate_credentials()` — checks that all three values are present
- `ask_genie(question)` — sends the question, polls for answer, returns result
- `_extract(msg)` — pulls the answer text and SQL out of the API response

### `ui/app.py`
The Streamlit chatbot UI. Calls `ask_genie()` when the user submits a question.
Shows the answer and the SQL Genie wrote in an expandable panel.

---

## Common Errors and Fixes

| Error | Cause | Fix |
|---|---|---|
| `Missing in .env file` | `.env` file not created or wrong filename | Create `config/.env` from `.env.example` and fill in all three values |
| `Authentication failed (401)` | Token is wrong or expired | Go to Settings → Developer → Manage Tokens → Generate a new one |
| `Genie Space not found (404)` | Space ID is wrong | Open Genie Space in browser, re-copy the ID from the URL |
| `Cannot connect to host` | Host URL is wrong or has a typo | Copy the URL exactly up to `.com` or `.net` only |
| `Genie did not respond in 90s` | No SQL Warehouse attached | Go to Genie Space → Settings → Compute → attach Starter Warehouse |
| `No answer returned` | Column descriptions missing | Add descriptions to all columns in Genie Space → Data tab |

---

## How the API Flow Works (3 steps)

```
Your question
     │
     ▼
POST /api/2.0/genie/spaces/{SPACE_ID}/start-conversation
     │  sends: { "content": "your question" }
     │  returns: conversation_id + message_id
     │
     ▼
GET  /api/2.0/genie/spaces/{SPACE_ID}/conversations/{conv_id}/messages/{msg_id}
     │  poll every 2 seconds until status == "COMPLETED"
     │
     ▼
Parse response → extract answer text + SQL query
     │
     ▼
Show in terminal or Streamlit UI
```

---

## Next Steps After This Works

Once the chatbot is running, try these improvements:

1. **Add your own data** — upload a CSV file to a Volume or Table and point the Genie Space at it
2. **Add more Genie Spaces** — one for each topic (sales, customer, operations)
3. **Build the Medium project** — add LangGraph + Supervisor to route between multiple Genie Spaces automatically
4. **Add MLflow logging** — track every question, answer, and SQL query for observability

---

## .gitignore (add this to your project root)

```
config/.env
__pycache__/
*.pyc
.DS_Store
```
