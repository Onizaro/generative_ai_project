import requests
import json

# --- NETWORK CONFIGURATION ---
COUNCIL_MEMBERS = [
    {"name": "Agent_Llama3", "url": "http://127.0.0.1:11434/api/generate", "model": "llama3"},
    {"name": "Agent_Mistral", "url": "http://127.0.0.1:11434/api/generate", "model": "mistral"},
    {"name": "Agent_Qwen2.5:7b", "url": "http://127.0.0.1:11434/api/generate", "model": "qwen2.5:7b"}
]

# The Chairman must run as a separate service on a dedicated machine
CHAIRMAN = {
    "name": "Chairman_Phi3",
    "url": "http://127.0.0.1:11434/api/generate",
    "model": "phi3"
}

def call_local_llm(url, model, prompt):
    """Sends a REST API request to a local Ollama instance."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        # Timeout increased to 300s to prevent 'Read timed out' errors during local inference
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status() 
        return response.json().get("response")
    except Exception as e:
        return f"Technical Error: {e}"

# --- STAGE 1: FIRST OPINIONS ---
def stage_1_opinions(user_query):
    """Each LLM in the council generates an answer independently."""
    print("\n--- Stage 1: Collecting Opinions ---")
    responses = []
    for member in COUNCIL_MEMBERS:
        print(f"Querying {member['name']}...")
        ans = call_local_llm(member['url'], member['model'], user_query)
        responses.append({"author": member['name'], "content": ans})
    return responses

# --- STAGE 2: REVIEW & RANKING (Anonymized) ---
def stage_2_review(user_query, original_responses):
    """Models anonymously review and rank each other's answers."""
    print("\n--- Stage 2: Review and Ranking ---")
    reviews = []
    for reviewer in COUNCIL_MEMBERS:
        # Prepare anonymized list of other members' responses 
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
        
        print(f"{reviewer['name']} is reviewing the responses...")
        review_text = call_local_llm(reviewer['url'], reviewer['model'], prompt_review)
        reviews.append({"reviewer": reviewer['name'], "review": review_text})
    return reviews

# --- STAGE 3: CHAIRMAN FINAL ANSWER ---
def stage_3_chairman(user_query, responses, reviews):
    """The Chairman synthesizes all outputs into a final response."""
    print("\n--- Stage 3: Chairman Synthesis ---")
    
    full_context = f"Question: {user_query}\n\n"
    full_context += "Council Responses:\n"
    for r in responses:
        full_context += f"- {r['content']}\n"
    
    full_context += "\nMember Reviews:\n"
    for rev in reviews:
        full_context += f"- {rev['review']}\n"
    
    prompt_chairman = f"""
    You are the Chairman of the LLM Council. Here are the deliberations:
    {full_context}
    Synthesize all the above into a single, comprehensive, and accurate final response for the user.
    """
    
    return call_local_llm(CHAIRMAN['url'], CHAIRMAN['model'], prompt_chairman)

# --- EXECUTION ---
if __name__ == "__main__":
    query = "very briefly, What are the advantages of a distributed system for LLMs?"
    
    # Stage 1: Opinions 
    first_opinions = stage_1_opinions(query)
    
    # Stage 2: Review 
    all_reviews = stage_2_review(query, first_opinions)
    
    # Stage 3: Final Synthesis 
    final_output = stage_3_chairman(query, first_opinions, all_reviews)
    
    print("\n================ FINAL ANSWER ================")
    print(final_output)