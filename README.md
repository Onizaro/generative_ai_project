# LLM Council – Local Distributed Deployment (Solo Project)

## Group Information
- Student Name: Nizar O.
- TD Group: CDOF3

- Project Type: Solo Project

---

## Project Overview
This project is a local implementation of the **LLM Council** concept inspired by Andrej Karpathy.

Instead of relying on a single Large Language Model (LLM), multiple local LLMs collaborate by:
1. Generating independent answers to a user query
2. Reviewing and critiquing each other’s responses anonymously
3. Synthesizing a final answer through a dedicated **Chairman LLM**

All models run **locally** using **Ollama**, without any cloud-based API.

---

## Architecture & Design

### Council Members
The system includes **three independent council LLMs**:
- Llama 3
- Mistral
- qwen2.5:7b

Each model generates its own response to the same user query.

### Chairman LLM
- Used model: phi3
- The Chairman is a **logically separated service**
- It does **not** participate in the first opinion stage
- It only synthesizes council responses and reviews


---

## Council Workflow

### Stage 1 – First Opinions
- Each council LLM independently answers the user query.
- Responses are collected and stored.

### Stage 2 – Review & Ranking
- Each LLM reviews anonymized responses from other members.
- Each LLM ranks the responses based on: accuracy and insight
- Model identities are hidden to avoid bias.

### Stage 3 – Chairman Final Answer
- The Chairman LLM receives:
  - All council responses
  - All peer reviews
- It synthesizes them into a single final answer.

---

## Technologies Used
- Python 3
- Ollama (local LLM inference)
- REST API communication
- Models:
  - llama3
  - mistral
  - phi3

---

## Setup & Installation

### 1. Install and Run Ollama 
Follow the instructions from the official website:
https://ollama.com

Then, run the App OR run:
```
ollama serve
```

### 2. Pull required models
```
ollama pull llama3
ollama pull mistral
ollama pull phi3
ollama pull qwen2.5:7b
```

### 3. Install Python dependencies
```
pip install -r requirements.txt
```

### 4. Running the Web App
```
python app.py
```
The program will query each council LLM , run the review stage , and generate a final synthesized answer via the Chairman. Depending on your configuration, it can take a few minutes to finalize, between 5 and 15 min for me.


---

## Generative AI Usage Statement 

- Tools Used: Gemini 3 pro and ChatGPT (free version)
- Purpose: Code refactoring assistance (clean code + commentary), model selection, prompt engineering and documentation writing.
---
- Tool Used: Claude (free version)
- Purpose: Help creating a graphical version of the initial code.

---

## Optional Enhancement Ideas (Bonus)
- Model health checks & heartbeat monitoring
- Token usage estimation
- Load and availability status per model

- Improved tab view:
  - Color-coded responses
  - Collapsible panels
  - Side-by-side comparison
  - Diff highlighting between outputs
- Model performance dashboard:
  - Latency per model and response-time tracking
  - Ranking results
  - Indicators for model status (running, idle, unavailable)
- Dark / Light mode UI
- Clear visualization of the council workflow (Stage 1 → Stage 3)



