**Work Allocation** 

|**Hate Severity**<br>**Level**|**Moderator Verdict**|**Platform**<br>**Enforcement**|**Technical API**<br>**Action**|
|---|---|---|---|
|**Clean / False**<br>**Positive**|Disagree with AI|**No action**|Mark message<br>resolved in DB.|
|**Mild / Borderline**|Mild Hate /<br>Profanity|**Send Warning DM**<br>**/ Reply**|Call POST /2/tweets<br>(Reply) or POST<br>/2/dm_events.|
|**Moderate Hate**|Hate Speech|**Hide/Remove**<br>**Comment + DM**|Call DELETE<br>/2/tweets/:id +<br>warning DM.|
|**Severe / Harsh**|Violent Threat /<br>Severe Hate|**Delete Comment +**<br>**Issue Strike**|Call DELETE<br>/2/tweets/:id + log<br>user strike.|



### **Updated 4-Person Role Division** 

#### **Member 1: AI Specialist (Categorization & Multi-Class Model)** 

- **Main Job:** Builds and trains the AI model to detect **and categorize** hate speech into specific severity levels. 

- **Technical Tasks:** 

- Clean and preprocess incoming tweet text (hashtags, @mentions, lowercasing, links). 

- Train the BiLSTM model on a multi-class dataset ( _Clean_ , _Mild/Profanity_ , _Moderate Hate_ , _Severe Threat_ ). 

- Expose an inference endpoint that returns both the **Category** and the **Confidence Score** (e.g., {"category": "Severe Hate", "confidence": 0.92}). 

- **Literature Review Contribution:** Writes the survey section on _Multi-class Hate Speech Categorization using Neural Networks (BiLSTM, BERT, CNNs)_ . 

#### **Member 2: CSP Specialist (Priority & Workload Router)** 

- **Main Job:** Writes the routing logic that distributes flagged Twitter comments to human moderators fairly and efficiently. 

- **Technical Tasks:** 

- Implement constraint rules in Python (python-constraint or OR-Tools). 

- **Capacity Constraints:** Keep moderator daily load under $X$ active reviews to prevent fatigue. 

- **Severity Priority Rules:** Ensure **Severe/Harsh** comments bypass normal wait queues and go directly to the first available Senior Moderator. 

- **Language/Topic Matching:** Match slang or specific dialects to moderators tagged with those skills. 

- **Literature Review Contribution:** Writes the survey section on _Constraint Optimization and Dynamic Scheduling in Content Moderation Workflows_ . 

#### **Member 3: Backend & Twitter API Integration Engineer (The Pipeline)** 

- **Main Job:** Connects Twitter/X to the database and runs the automated enforcement actions. 

- **Technical Tasks:** 

- Set up Twitter API v2 integration using tweepy or standard HTTP clients. 

- Build endpoints to fetch reply comments under tweets. 

- Implement enforcement actions: send automated warning replies (POST /2/tweets), warning DMs (POST /2/dm_events), or delete offending comments (DELETE /2/tweets/:id) when triggered by a moderator. 

- Maintain database tables for Tweets, Users, Warnings, Strike_Logs, and Moderator_Assignments. 

- **Literature Review Contribution:** Writes the survey section on _System Architecture, API Orchestration, and Automated Platform Enforcement_ . 

#### **Member 4: Frontend Developer & Lead Report Author (The Dashboard & Storyteller)** 

- **Main Job:** Builds the moderator web interface and coordinates the final research document. 

- **Technical Tasks:** 

- Design the Moderator Dashboard (React, Streamlit, or HTML/Tailwind) displaying incoming Twitter comments, AI confidence, and hate category tags. 

- Include interactive moderation control buttons: **[Approve]** , **[Warn User]** , **[Delete Comment]** , or **[Severe Strike]** . 

- Create architectural flowcharts, UI mockups, and live demo recording setups. 

- **Literature Review Contribution:** Collects research sections from Members 1–3, formats the report, and creates the primary **Comparative Analysis Matrix** contrasting traditional moderation vs. your hybrid system. 

### **Summary of Team Tasks** 

Member 1 (AI) ──► Classifies text severity (Clean / Mild / Severe) Member 2 (CSP) ──► Priority-routes severe tweets to free moderators Member 3 (Backend) ──► Connects Twitter API (Fetches tweets, Deletes/Warns) Member 4 (Frontend) ──► Displays tweets on UI & Compiles Literature Report 

Here is a breakdown of the 4 roles in simple, everyday language: 

### **Member 1: The AI Specialist (The "Detector")** 

- **In Simple Terms:** This person builds the AI brain that reads tweets and figures out if they contain hate speech and how bad it is. 

- **What They Do:** 

- Teaches the AI model using a dataset of messages so it learns the difference between 

clean text, mild profanity, and severe threats. 

- Gives each comment a score and a category (e.g., _"Mild Hate with 85% certainty"_ or _"Severe Threat with 95% certainty"_ ). 

- **Paper Contribution:** Writes the report section on how previous researchers built AI models to detect hate speech, and where those models struggle. 

### **Member 2: The CSP Logic Specialist (The "Traffic Controller")** 

- **In Simple Terms:** This person writes the smart rules that decide _which_ human moderator gets _which_ flagged comment. 

- **What They Do:** 

- Sets up capacity limits so no moderator gets overwhelmed with too many tasks at once. 

- Writes priority rules: if the AI finds a **Severe/Harsh** comment, this role's code skips the normal queue and instantly pushes it to an available moderator. 

- **Paper Contribution:** Writes the report section on how task-scheduling algorithms and smart rules help manage workload fairly. 

### **Member 3: The Backend & Twitter API Developer (The "Bridge & Enforcer")** 

- **In Simple Terms:** This person connects Twitter/X to your system and handles the automatic actions when a comment is reviewed. 

- **What They Do:** 

- Connects the app to Twitter to automatically pull in reply comments. 

- Runs the actual enforcement based on the moderator's click: 

- If **Mild** : Automatically posts a warning reply or DM to the user on Twitter. 

- If **Harsh** : Calls Twitter’s system to **delete the tweet immediately** and logs a strike against the user. 

- Builds the database tables to save tweet IDs, user warning history, and strike logs. 

- **Paper Contribution:** Writes the report section on how software pipelines integrate social media APIs and run automated platform enforcement. 

### **Member 4: The Frontend Developer & Report Lead (The "Screen & Storyteller")** 

- **In Simple Terms:** This person builds the website screen that moderators use and pulls the whole research document together. 

- **What They Do:** 

- Builds the Moderator Dashboard—a clean website interface showing the flagged tweet, the AI category tag, and buttons like **[Warn User]** , **[Delete Tweet]** , or **[False Alarm]** . 

- Creates system diagrams and flowcharts showing how all 4 parts work together for the live project demo. 

- **Paper Contribution:** Collects the report sections written by Members 1, 2, and 3, formats the final document, and creates the main comparison table showing why your hybrid system works better than older methods. 

### **Quick Summary** 

|**Person**|**Role Title**|**Simple Role**|**Key Output**|
|---|---|---|---|



|**Member 1**|AI Specialist|Spots and<br>categorizes bad<br>tweets|Multi-class AI<br>model|
|---|---|---|---|
|**Member 2**|CSP Specialist|Routes tweets to<br>the right moderator|Smart assignment<br>rules|
|**Member 3**|Backend & Twitter<br>Dev|Connects Twitter &<br>executes<br>deletions/warnings|Twitter API pipeline<br>& Database|
|**Member 4**|Frontend & Report<br>Lead|Builds the review<br>dashboard &<br>compiles report|Moderator UI &<br>Literature<br>document|



**connect twitter to project ?** 

You don't need to send real warnings to random people on live Twitter. In fact, doing so would get your API key banned for spam and violate Twitter's Developer Policy. For a **college mini-project** , you handle this using a **Simulated Twitter Integration** (or a **Test/Sandbox Environment** ). This gives you the full technical experience of calling APIs without any real-world risk. 

### **How to Set Up the Twitter Connection Safe & Free** 

Instead of targeting live public users, you connect your app to Twitter using one of two practical approaches: 

#### **Option A: Test Account Sandbox (Recommended for Live Demo)** 

1. **Create Two Private Test Accounts:** 

- **Account A (Poster):** Posts sample tweets/comments (including test hate speech, sarcasm, and clean text). 

- **Account B (User):** Replies to Account A's tweets. 

2. **How your Backend works:** 

- Member 3's Python backend uses **Twitter API v2** (via the tweepy library) to read reply comments _only_ under Account A's posts. 

- When a moderator clicks **[Delete Comment]** on your dashboard, your backend calls the API DELETE /2/tweets/:id endpoint to erase Account B's test reply in real time. 

- When a moderator clicks **[Send Warning]** , your backend calls POST /2/tweets to post an automated reply back to Account B under that specific test thread. 

- **Why this works:** You perform **100% real API calls** , tweets actually disappear live on Twitter during your presentation, and no real users are spammed or harmed. 

#### **Option B: Mock/Simulated API Layer (Fallback without Twitter Developer Key)** 

If Twitter API rate limits or approval delays get in the way, build a **Mock Twitter Service** : 

1. **Local Database Stream:** Member 3 populates a database table with pre-collected tweets from a public dataset (like the _Davidson Hate Speech Dataset_ ). 

2. **Simulated Actions:** When the moderator clicks **[Send Warning]** or **[Delete]** : 

- The backend updates the database status: is_deleted = True or user_status = "Warned (DM Sent)". 

- The UI updates in real time, visually striking out or removing the comment from the screen. 

3. **Log Window:** Display an **"API Output Console"** at the bottom of your dashboard showing live JSON payloads: 

<mark>JSON</mark> 

<mark>[SIMULATED TWITTER API]</mark> 

<mark>POST https://api.twitter.com/2/tweets</mark> 

<mark>Payload: { "reply_to": "183610293", "text": "⚠ Warning: Your comment violated platform policies."</mark> ️ <mark>} Status: 200 OK</mark> 

### **How to Present This to Professors** 

During your project demo, explain your integration like this: 

_"To comply with social media safety guidelines and developer policies, our system operates on a dedicated_ **_Twitter Developer Test Sandbox_** _. The backend executes_ 

_authentic Twitter API v2 endpoints—including live tweet deletion and automated thread replies—targeting controlled test accounts rather than public users."_ 

This approach demonstrates solid technical architecture, proper API integration, and ethical software engineering. 

# **moderator for our project demo** 

In a real-world platform (like Twitter/X or Meta), the **moderators are paid human content reviewers** employed by the company or third-party Trust & Safety contractors. Their job is to read flagged posts and enforce platform policies. 

## <u>For your</u> **<u>college mini-project</u>** <u>, you simulate this setup using two</u> 

## <u>main roles:</u> 

### **1. In Your Project Demo (How to set it up)** 

When you present your project to professors or evaluators, you don't need real employees. Instead: 

- **Your Team Members = The Moderators:** During the live demo, one or two of your team members will log into the **Moderator Dashboard** (built by Member 4). 

- **The Workflow:** 

1. A sample Twitter reply comes in. 

2. The BiLSTM flags it and the CSP routes it to **"Moderator A"** . 

3. You (acting as Moderator A) look at the screen, read the tweet, and click **[Approve]** , **[Send Warning]** , or **[Delete Comment]** . 

### **2. In Your Project Report & System Architecture** 

In your documentation, describe the moderators as **Human Trust & Safety Agents** with different attributes: 

- **General Reviewers:** Handle basic, everyday flagged comments. 

- **Senior / Specialist Moderators:** Handle high-priority, severe threats or complex edge cases (e.g., regional slang or hate speech in specific languages). 

### **How the CSP Engine Uses Moderator Attributes** 

This is why your **CSP Engine (Member 2)** is so important. The system doesn't treat all moderators as identical. It tracks: 

1. **Active Workload / Capacity:** If Moderator 1 is reviewing 5 posts, the CSP routes the next post to Moderator 2. 

2. **Language / Regional Expertise:** If a tweet contains specific regional slang, the CSP routes it to a moderator tagged with that language skill. 

3. **Seniority:** High-confidence, severe violent threats bypass junior queues and route directly to Senior Moderators. 

**MEMBER-1** 

Step-by-step breakdown of **Member 1’s role: The AI & NLP Specialist** . 

Member 1 is responsible for building the **AI brain** of the system. Their primary job is to take raw text from incoming tweets, process it, and train a deep learning model (a **BiLSTM** ) that determines whether the text contains hate speech, categorizes its severity, and assigns a confidence score. 

### **Overview of Member 1's Workflow** 

- [ Dataset Preparation ] ──► [ Text Preprocessing ] ──► [ Model Training (BiLSTM) ] ──► [ Inference API Endpoint ] 

### **Step-by-Step Implementation Guide** 

#### **Step 1: Dataset Collection & Categorization** 

- **Goal:** Obtain a labeled dataset of text messages/tweets to teach the AI model. 

- **How to do it:** 

1. Download an open-source dataset, such as the _Davidson Hate Speech Dataset_ or Kaggle’s _Twitter Hate Speech Dataset_ . 

2. Map the dataset labels into **4 distinct categories** : 

- 0: **Clean** (Normal, harmless text) 

- 1: **Mild / Profanity** (Rude words, mild insults, questionable sarcasm) 

- 2: **Moderate Hate** (Identity-based insults, slurs, targeted harassment) 

- 3: **Severe / Harsh** (Direct violence, dangerous incitement, explicit threats) 

#### **Step 2: Text Cleaning & Preprocessing** 

- **Goal:** Convert messy, raw tweet text into clean numbers that a machine learning model can understand. 

- **How to do it:** 

1. Write a Python function using libraries like re (Regular Expressions) and nltk or spacy to: ■ Remove URLs (https://...), user handles (@username), and special symbols. 

- Convert all text to lower case. 

- Strip extra spaces and emojis (or map emojis to text equivalents). 

2. **Tokenization:** Break sentences into individual words. 

3. **Padding & Sequence Conversion:** Convert words into numerical IDs using Keras’s Tokenizer and ensure every input sentence has the exact same fixed length using pad_sequences. 

#### **Step 3: Building & Training the BiLSTM Model** 

- **Goal:** Build the Neural Network architecture that detects subtle text patterns. 

- **Why BiLSTM?** Standard Recurrent Neural Networks (RNNs) read text in one direction (left-to-right). A **Bidirectional LSTM (BiLSTM)** reads text in **both directions** (left-toright and right-to-left) at the same time, allowing it to capture context and nuance much better. 

- **How to do it:** 

1. Define the model architecture using TensorFlow/Keras: 

- **Embedding Layer:** Converts word IDs into dense vector representations. 

- **BiLSTM Layer:** Captures forward and backward context across the sequence. 

- **Dense / Dropout Layers:** Reduces overfitting and condenses learned features. 

- **Softmax Output Layer:** Outputs 4 probabilities corresponding to the 4 severity categories. 

2. Compile the model using categorical_crossentropy loss and the adam optimizer. 

3. Train the model (model.fit) on your training dataset across several epochs. 

#### **Step 4: Evaluating & Saving the Model** 

- **Goal:** Verify that the model is accurate and save it so the rest of the project team can use it. 

- **How to do it:** 

1. Test the model on unseen data and compute key performance metrics: **Accuracy, Precision, Recall, and F1-Score** . 

2. Save the trained model weights to disk (e.g., bilstm_model.h5 or model.keras) along with the saved tokenizer object (tokenizer.pkl). 

#### **Step 5: Exposing the Inference API Function** 

- **Goal:** Create a simple Python interface that Member 3 (Backend Developer) can call whenever a new tweet arrives from the Twitter API. 

- **How to do it:** 

1. Write a standalone Python function (e.g., predict_hate_speech(raw_text)). 

2. Inside this function: 

- Run the raw text through the cleaning and tokenization pipeline. 

- Pass the preprocessed tensor through the saved BiLSTM model. 

- Extract the predicted category name and highest confidence score. 

3. **Sample Output:** 

   - JSON 

{ 

"predicted_category": "Severe Hate", 

"confidence_score": 0.94, 

"flagged": true } 

### **Member 1's Literature Review Deliverable** 

Along with coding the model, Member 1 **<u>must write their assigned section</u>** of the research paper: 

- **Topic:** _Survey of Machine Learning and Deep Learning Techniques for Automated Hate Speech Classification_ . 

- **What to Write:** 

1. Summarize prior research papers that used Support Vector Machines (SVM), 

   - Convolutional Neural Networks (CNN), and Transformers (BERT) for text moderation. 

2. Explain the technical reasons why a **BiLSTM** was chosen for this project (e.g., its capability to process sequence context in both directions while being lighter to compute than massive Transformer models). 

3. Highlight common failure points of automated ML models (like false positives caused by sarcasm or regional slang) to justify why human moderators are required. 

**MEMBER-2** 

### **Member 2: The CSP Logic Specialist (The "Traffic Controller")** 

**Primary Goal:** Build the smart routing engine that takes flagged tweets from Member 1 and assigns them to available human moderators based on specific operational constraints. 

[ Flagged Tweet Received ] ──► [ Load Constraints & Mod Metadata ] ──► [ Run CSP Solver ] ──► [ Return Optimal Assignment ] 

#### **Step-by-Step Execution Plan:** 

1. **Define the CSP Components in Python:** 

- **Variables (V):** Unassigned flagged tweets waiting in queue {T1, T2, ..., Tn}. 

- **Domains (D):** Pool of available moderators {Mod1, Mod2, ..., Modk}. 

- **Attributes:** Assign properties to moderators (e.g., max_capacity = 5, languages = ["English", "Hindi", "Slang"], role = "Senior") and tweets (e.g., severity = "Severe", language = "Slang"). 

2. **Implement Constraint Rules using a Python Solver:** 

- Use libraries like python-constraint or Google OR-Tools. 

- **Workload Constraint:** Ensure no moderator exceeds their max active review count (e.g., Mod_i <= 5 active tasks) to prevent fatigue. 

- **Priority Constraint:** If a tweet is flagged as Severe/Harsh, force the solver to route it immediately to an available Senior Moderator, bypassing normal queues. 

- **Skill Matching:** Route tweets containing regional slang or specific dialects to moderators tagged with matching language skills. 

3. **Expose the Assignment Function:** 

- Write a clean python function: assign_moderator(tweet_id, severity_category, tweet_text) that runs the solver and returns the optimal moderator_id. 

4. **Member 2's Literature Survey Contribution:** 

- **Topic:** Survey of Constraint Optimization and Task-Scheduling Algorithms in Operational Workflows. 

- **What to Write:** Review literature on Constraint Satisfaction Problems (CSP), linear programming, and resource allocation. Contrast static FIFO (First-In, First-Out) queue assignment with dynamic constraint-based routing. 

**MEMBER-3** 

### **Member 3: Backend & Twitter API Engineer (The "Pipeline & Enforcer")** 

**Primary Goal:** Build the central REST API server, manage database storage, integrate Twitter/X API v2, and trigger automated enforcement actions when a moderator submits a decision. 

- [ Fetch Reply via Twitter API ] ──► [ Send to Member 1 AI & Member 2 CSP ] ──► [ Save to DB ] ──► [ Execute Tweet Delete/DM Action ] 

#### **Step-by-Step Execution Plan:** 

1. **Design & Build the SQL Database Schema:** 

- Set up PostgreSQL, MySQL, or SQLite tables: 

   - **Tweets:** id, tweet_id_str, text, ai_category, confidence_score, status. 

   - **Moderators:** id, name, active_load, max_capacity, role. 

   - **Actions_Log:** id, tweet_id, moderator_id, verdict, action_taken, timestamp. 

2. **Connect the Twitter API v2 (Test Account Sandbox):** 

- Use Python’s tweepy package to fetch reply comments under a controlled test post. 

3. **Build the Central Web Server (Flask / FastAPI):** 

- Create the main orchestrator endpoints: 

   - **POST /api/ingest-tweet:** Receives a tweet → calls Member 1’s AI script → if flagged, calls Member 2’s CSP solver → saves assignment to DB. 

   - **POST /api/moderator-action:** Accepts moderator decisions (Approve, Warn, or Delete). 

4. **Implement Automated Platform Enforcement:** 

- When a moderator submits Delete, call Twitter API DELETE /2/tweets/:id to remove the reply live from the test thread. 

- When a moderator submits Warn, call Twitter API POST /2/tweets to post an automated warning reply under the thread. 

5. **Member 3's Literature Survey Contribution:** 

- **Topic:** Survey of Social Media Content Moderation Systems and Automated Platform Enforcement Pipelines. 

- **What to Write:** Research architectural standards in social media platforms, API ratelimiting handling, active learning data pipelines, and security considerations when executing automated deletion policies. 

**MEMBER-4** 

### **Member 4: Frontend Developer & Lead Report Author (The "Screen & Storyteller")** 

**Primary Goal:** Build the web interface used by human moderators, map out architectural diagrams, and lead the compilation of the final literature review document. 

[ Read Assigned Tweet on UI ] ──► [ View AI Category & Score ] ──► [ Click Action Button ] ──► [ Compile Research Report ] 

#### **Step-by-Step Execution Plan:** 

1. **Build the Moderator Dashboard (React, Streamlit, or HTML/Tailwind + JS):** 

- Design a clean interface displaying: 

- A queue table of assigned tweets. 

- The original tweet text, user handle, AI predicted severity tag, and confidence score. 

- Action buttons: [Approve / Clean], [Send Warning], and [Delete Tweet]. 

2. **Connect Dashboard to Member 3’s Backend:** 

- Write fetch requests to pull pending tasks from GET /api/moderator-queue/:moderator_id and send decisions to POST /api/moderator-action. 

3. **Create System Flowcharts & Visuals:** 

- Draw system sequence diagrams, data pipeline flowcharts, and database ER diagrams for the project report and demo presentation. 

4. **Member 4's Literature Survey Contribution (Lead Compiler):** 

- **Topic:** Comparative Analysis Matrix & System Synthesis. 

- **What to Write:** Collect research sections from Members 1, 2, and 3 into an IEEE/Academic paper format. Construct the primary Comparative Matrix Table contrasting traditional methods against your hybrid system: 

|**Aspect**|**Standalone AI**<br>**Models (SVM /**<br>**BiLSTM)**|**Pure FIFO Queue**<br>**Moderation**|**Our Hybrid**<br>**(BiLSTM + CSP +**<br>**Moderator)**|
|---|---|---|---|
|**Handling Sarcasm**<br>**& Context**|Poor (High False<br>Positives)|High (Human<br>Evaluated)|**High**(Assigned to<br>Human Reviewer)|
|**Workload**<br>**Optimization**|N/A (No human<br>routing)|Poor (Random /<br>FIFO overload)|**Optimal**<br>(Constraint-<br>balanced by CSP)|
|**Processing Speed**|Instant|Slow|**Fast Filter**+<br>**Prioritized**<br>**Escalation**|
|**Platform**<br>**Enforcement**|Automatic / High<br>Risk|Manual|**Human Verified +**<br>**API Automated**|



