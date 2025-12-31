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
- Phi-3

Each model generates its own response to the same user query.

### Chairman LLM
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
- Reviews focus on accuracy and insight.
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
```

### 3. Install Python dependencies
```
pip install requests
```

### 4. Running the Project
```
python main.py
```
The program will query each council LLM , run the review stage , and generate a final synthesized answer via the Chairman. Depending on your configuration, it can take a few minutes to finalize, ~10/12 min for me.

---

Improvements Over Original Repository 
- Local-First: Removed all cloud-based API dependencies (OpenRouter/OpenAI).
- Architecture: Implemented a distributed-ready REST architecture.
- Strict Separation: Explicit separation of the Chairman role from the Council.
- Transparency: Allows inspection of intermediate model outputs.

---

Generative AI Usage Statement 
- Tools Used: Gemini 3 pro
- Purpose: Code refactoring assistance and documentation writing.
