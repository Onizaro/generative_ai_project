from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime
import time
import threading
from collections import defaultdict
import re
import tiktoken

app = Flask(__name__)

# --- NETWORK CONFIGURATION ---
COUNCIL_MEMBERS = [
    {"name": "Agent_Llama3", "url": "http://127.0.0.1:11434/api/generate", "model": "llama3", "color": "#ff6b6b"},
    {"name": "Agent_Mistral", "url": "http://127.0.0.1:11434/api/generate", "model": "mistral", "color": "#4ecdc4"},
    {"name": "Agent_Qwen2.5:7b", "url": "http://127.0.0.1:11434/api/generate", "model": "qwen2.5:7b", "color": "#ffe66d"}
]

CHAIRMAN = {
    "name": "Chairman_Phi3",
    "url": "http://127.0.0.1:11434/api/generate",
    "model": "phi3",
    "color": "#a8dadc"
}

# --- MONITORING DATA ---
model_status = {}
model_metrics = defaultdict(lambda: {
    "total_requests": 0,
    "total_latency": 0,
    "avg_latency": 0,
    "last_request_time": None,
    "tokens_generated": 0,
    "errors": 0,
    "status": "idle"
})

for member in COUNCIL_MEMBERS + [CHAIRMAN]:
    model_status[member['model']] = {
        "status": "unknown",
        "last_check": None,
        "available": False,
        "name": member['name'],
        "color": member['color']
    }

# Cache for deliberations
deliberation_cache = {}

def estimate_tokens(text):
    """Estimation of tokens."""
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)

def check_model_health(url, model):
    """Check if a model is available via Ollama API."""
    try:
        # Use Ollama's tags endpoint to check model availability
        base_url = url.replace('/api/generate', '')
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.ok:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            # Check if model exists (handle both 'model' and 'model:tag' formats)
            available = any(model in m or m.startswith(model.split(':')[0]) for m in model_names)
            return {
                "available": available,
                "status": "available" if available else "not_found",
                "last_check": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "available": False,
            "status": "unavailable",
            "last_check": datetime.now().isoformat(),
            "error": str(e)
        }
    
    return {
        "available": False,
        "status": "error",
        "last_check": datetime.now().isoformat()
    }

def call_local_llm(url, model, prompt, track_metrics=True):
    """Sends a REST API request to a local Ollama instance with metrics tracking."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    start_time = time.time()
    
    try:
        # Update status to running
        if track_metrics:
            model_metrics[model]["status"] = "running"
        
        response = requests.post(url, json=payload, timeout=600)
        response.raise_for_status()
        
        end_time = time.time()
        latency = end_time - start_time
        
        result = response.json()
        response_text = result.get("response", "")
        
        # Track metrics
        if track_metrics:
            tokens = estimate_tokens(response_text)
            model_metrics[model]["total_requests"] += 1
            model_metrics[model]["total_latency"] += latency
            model_metrics[model]["avg_latency"] = (
                model_metrics[model]["total_latency"] / model_metrics[model]["total_requests"]
            )
            model_metrics[model]["last_request_time"] = datetime.now().isoformat()
            model_metrics[model]["tokens_generated"] += tokens
            model_metrics[model]["status"] = "idle"
        
        return {
            "success": True,
            "response": response_text,
            "latency": round(latency, 2),
            "tokens": estimate_tokens(response_text)
        }
        
    except Exception as e:
        if track_metrics:
            model_metrics[model]["errors"] += 1
            model_metrics[model]["status"] = "error"
        
        return {
            "success": False,
            "response": f"Technical Error: {e}",
            "latency": 0,
            "tokens": 0,
            "error": str(e)
        }

def stage_1_opinions(user_query):
    """Each LLM in the council generates an answer independently."""
    responses = []
    prompt = f"""
    You are a domain expert participating in a council.

    User question:
    {user_query}

    Instructions:
    - Provide a clear, technically accurate answer.
    - Focus on reasoning, not verbosity.
    - Do NOT reference other agents.
    - Do NOT speculate beyond established knowledge.

    Structure your response as:
    1. Core answer (2–4 sentences)
    2. Key points (bullet list, max 5 items)
    """
    for member in COUNCIL_MEMBERS:
        result = call_local_llm(member['url'], member['model'], prompt)
        responses.append({
            "author": member['name'],
            "model": member['model'],
            "content": result["response"],
            "timestamp": datetime.now().isoformat(),
            "latency": result["latency"],
            "tokens": result["tokens"],
            "color": member["color"],
            "success": result["success"]
        })
    return responses

def stage_2_review(user_query, original_responses):
    """Models anonymously review and rank each other's answers."""
    reviews = []
    for reviewer in COUNCIL_MEMBERS:
        others_work = ""
        for i, resp in enumerate(original_responses):
            others_work += f"\nResponse {i+1}: {resp['content']}\n"
        
        prompt_review = f"""
        User Query: {user_query}
        
        You are given EXACTLY {len(original_responses)} responses.
        They are labeled Response 1 to Response {len(original_responses)}.

        IMPORTANT RULES:
        - Do NOT invent additional responses.
        - Do NOT reference any response number other than those provided.
        - Evaluate ONLY the responses shown below.

        Responses:
        {others_work}

        Task:
        Provide a concise critique and ranking of the responses based on accuracy and insight.
        """
        
        result = call_local_llm(reviewer['url'], reviewer['model'], prompt_review)
        reviews.append({
            "reviewer": reviewer['name'],
            "model": reviewer['model'],
            "review": result["response"],
            "timestamp": datetime.now().isoformat(),
            "latency": result["latency"],
            "tokens": result["tokens"],
            "color": reviewer["color"],
            "success": result["success"]
        })
    return reviews

def stage_3_chairman(user_query, responses, reviews):
    """The Chairman synthesizes all outputs into a final response."""
    full_context = f"Question: {user_query}\n\n"
    full_context += "Council Responses:\n"
    for r in responses:
        full_context += f"- {r['content']}\n"
    
    full_context += "\nMember Reviews:\n"
    for rev in reviews:
        full_context += f"- {rev['review']}\n"
    
    prompt_chairman = f"""
    You are the Chairman of an expert LLM council.

    User question:
    {user_query}

    You are given:
    1. A brief summary of multiple expert responses (3–5 sentences each)
    2. Peer reviews evaluating accuracy and insight

    Your task:
    - Identify the top 3–5 key points
    - Resolve contradictions using the reviews
    - Produce a single concise final answer

    Rules:
    - Do NOT mention the council, agents, or reviews
    - Do NOT invent new information
    - Maximum: 2 paragraphs, ~200 words

    Final answer structure:
    - Direct answer (1 paragraph)
    - Key takeaways (3–5 bullets)

    Council material summary:
    {full_context}
    """
    
    result = call_local_llm(CHAIRMAN['url'], CHAIRMAN['model'], prompt_chairman)
    
    return {
        "chairman": CHAIRMAN['name'],
        "model": CHAIRMAN['model'],
        "final_answer": result["response"],
        "timestamp": datetime.now().isoformat(),
        "latency": result["latency"],
        "tokens": result["tokens"],
        "color": CHAIRMAN["color"],
        "success": result["success"]
    }

# --- ROUTES ---

@app.route('/')
def index():
    """Main page with the interface."""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check health status of all models."""
    results = {}
    for member in COUNCIL_MEMBERS + [CHAIRMAN]:
        health = check_model_health(member['url'], member['model'])
        model_status[member['model']].update(health)
        results[member['model']] = {
            **model_status[member['model']],
            "metrics": dict(model_metrics[member['model']])
        }
    return jsonify(results)

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get performance metrics for all models."""
    metrics = {}
    for model_name, data in model_metrics.items():
        metrics[model_name] = dict(data)
    return jsonify(metrics)

@app.route('/api/council/stage1', methods=['POST'])
def run_stage1():
    """Stage 1: Generate initial opinions."""
    data = request.json
    user_query = data.get('query', '')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        stage1_data = stage_1_opinions(user_query)
        deliberation_cache[user_query] = {'stage1': stage1_data}
        
        return jsonify({
            "success": True,
            "stage": 1,
            "data": stage1_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/council/stage2', methods=['POST'])
def run_stage2():
    """Stage 2: Generate reviews."""
    data = request.json
    user_query = data.get('query', '')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        cache = deliberation_cache.get(user_query, {})
        stage1_data = cache.get('stage1', [])
        
        if not stage1_data:
            return jsonify({"error": "Stage 1 not completed"}), 400
        
        stage2_data = stage_2_review(user_query, stage1_data)
        deliberation_cache[user_query]['stage2'] = stage2_data
        
        return jsonify({
            "success": True,
            "stage": 2,
            "data": stage2_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/council/stage3', methods=['POST'])
def run_stage3():
    """Stage 3: Generate final synthesis."""
    data = request.json
    user_query = data.get('query', '')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        cache = deliberation_cache.get(user_query, {})
        stage1_data = cache.get('stage1', [])
        stage2_data = cache.get('stage2', [])
        
        if not stage1_data or not stage2_data:
            return jsonify({"error": "Previous stages not completed"}), 400
        
        stage3_data = stage_3_chairman(user_query, stage1_data, stage2_data)
        
        return jsonify({
            "success": True,
            "stage": 3,
            "data": stage3_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Background heartbeat monitoring
def heartbeat_monitor():
    """Continuously monitor model health."""
    while True:
        try:
            for member in COUNCIL_MEMBERS + [CHAIRMAN]:
                health = check_model_health(member['url'], member['model'])
                model_status[member['model']].update(health)
        except Exception as e:
            print(f"Heartbeat monitor error: {e}")
        time.sleep(30)  # Check every 30 seconds

# Start background monitoring
monitor_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
monitor_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
