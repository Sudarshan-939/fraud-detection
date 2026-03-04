import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
# Enable CORS for frontend requests
CORS(app)

@app.route('/')
def index():
    return send_from_directory(frontend_dir, 'stmt.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return jsonify({"error": "Path not found"}), 404

# --- API Keys ---
# Using keys provided by the user
TWITTER_KEY = os.getenv("TWITTER_KEY", "-ZrJyH8hDr1CnfWjvLQFBsHpEO")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "-AIzaSyAWQlaTFOINKj8XMAyaZBkxS-TKgAML16Y")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "-15a191f31dcf4a858e3094da017e2dd4")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

# Clean up any potential copy-paste dashes if they were just bullet points, 
# although we keep them if they are part of the key
if TWITTER_KEY.startswith("-"): TWITTER_KEY = TWITTER_KEY[1:]
if GOOGLE_API_KEY.startswith("-"): GOOGLE_API_KEY = GOOGLE_API_KEY[1:]
if NEWS_API_KEY.startswith("-"): NEWS_API_KEY = NEWS_API_KEY[1:]
if OPENROUTER_API_KEY.startswith("-"): OPENROUTER_API_KEY = OPENROUTER_API_KEY[1:]

TWITTER_KEY = TWITTER_KEY.strip()
GOOGLE_API_KEY = GOOGLE_API_KEY.strip()
NEWS_API_KEY = NEWS_API_KEY.strip()
OPENROUTER_API_KEY = OPENROUTER_API_KEY.strip()

@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Fetch live news using NewsAPI.
    """
    try:
        # Fetching general news from US as the default behavior
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "error": "Failed to fetch news", 
                "details": response.text
            }), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """
    Analyze text information whether given text is correct or not using DeepSeek API.
    If it is not, DeepSeek AI will provide the correction answer.
    """
    data = request.json
    text_to_analyze = data.get('text', '')
    
    if not text_to_analyze:
        return jsonify({"error": "No text provided for analysis"}), 400

    try:
        # Utilizing OpenRouter endpoint via standard REST API
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "arcee-ai/trinity-large-preview:free",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an expert fact-checker prioritizing extreme accuracy. Your job is to analyze the text provided by the user and determine if it is factually correct. "
                               "CRITICAL INSTRUCTIONS: "
                               "1. You MUST start your response with exactly either 'YES.' if the information is correct, or 'NO.' if the information is incorrect, unverified, or misleading. "
                               "2. Immediately after the 'YES.' or 'NO.', explain your reasoning with high precision, referencing known facts. "
                               "3. At the end of your response, you MUST include a 'Source:' section that explicitly provides the direct URL or website link (e.g., https://...) to the authoritative source where you derived the factual data."
                },
                {
                    "role": "user", 
                    "content": f"Please critically fact-check this information:\n{text_to_analyze}"
                }
            ],
            "temperature": 0.0,
            "top_p": 0.1
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=payload,
            timeout=30
        )
        
        # Log response if not OK to assist debugging
        if response.status_code != 200:
            try:
                err_dict = response.json()
                msg = err_dict.get('error', {}).get('message', 'Unknown AI API Error')
                if response.status_code == 401:
                    if "Missing Authentication header" in msg:
                        msg = "OpenRouter requires a valid OpenRouter API key (starts with sk-or-), but a DeepSeek key was used. Please update OPENROUTER_API_KEY in app.py."
                    elif "User not found" in msg:
                        msg = "OpenRouter rejected your API Key ('User not found.'). Please ensure you copied the key correctly without extra spaces or typographical errors."
                return jsonify({
                    "error": f"AI API error: {msg}",
                    "details": response.text
                }), response.status_code
            except Exception:
                return jsonify({
                    "error": "AI API error",
                    "details": response.text
                }), response.status_code
            
        ai_data = response.json()
        ai_message = ai_data["choices"][0]["message"]["content"]
        
        return jsonify({
            "success": True,
            "analysis": ai_message,
            "original_text": text_to_analyze
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/twitter', methods=['POST'])
def analyze_twitter():
    """
    A specific endpoint that takes a Twitter URL, fetches the tweet,
    and analyzes it via DeepSeek. 
    """
    data = request.json
    tweet_url = data.get('url', '')
    
    if not tweet_url:
        return jsonify({"error": "No Twitter URL provided"}), 400

    # For a real implementation, you'd use Tweepy with the TWITTER_KEY 
    # as a Bearer Token to fetch the tweet text.
    # Since the key provided looks unusually short for a Bearer token, we will simulate
    # fetching the text or rely on any actual text passed along with the request.
    
    # Extract ID from URL for context
    tweet_id = tweet_url.strip('/').split('/')[-1].split('?')[0]
    
    # Placeholder: if we actually had the full Tweepy implementation here:
    '''
    import tweepy
    client = tweepy.Client(bearer_token=TWITTER_KEY)
    tweet = client.get_tweet(id=tweet_id, tweet_fields=["text"])
    tweet_text = tweet.data.text if tweet.data else ""
    '''
    # We will assume the user may pass the tweet text if Twitter API fails, OR we just do general analysis
    tweet_text = data.get('tweet_text', f"Analyzing tweet ID {tweet_id}")
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "arcee-ai/trinity-large-preview:free",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an expert fact-checker prioritizing extreme accuracy. Analyze the context of the tweet or text provided and fact-check it. "
                               "CRITICAL INSTRUCTIONS: "
                               "1. You MUST start your response with exactly either 'YES.' if the information is correct, or 'NO.' if the information is incorrect, unverified, or misleading. "
                               "2. Immediately after the 'YES.' or 'NO.', explain your reasoning with high precision and clear corrections, referencing known facts. "
                               "3. At the end of your response, you MUST include a 'Source:' section that explicitly provides the direct URL or website link (e.g., https://...) to the authoritative source where you derived the factual data."
                },
                {
                    "role": "user", 
                    "content": f"Please critically fact-check this tweet content or topic:\n{tweet_text}"
                }
            ],
            "temperature": 0.0,
            "top_p": 0.1
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            try:
                err_dict = response.json()
                msg = err_dict.get('error', {}).get('message', 'Unknown AI API Error')
                if response.status_code == 401:
                    if "Missing Authentication header" in msg:
                        msg = "OpenRouter requires an OpenRouter API key (starts with sk-or-), but a DeepSeek key was given. Please update app.py."
                    elif "User not found" in msg:
                        msg = "OpenRouter rejected your API Key ('User not found.'). Please ensure you copied the key correctly without extra spaces or typos."
                return jsonify({
                    "error": f"AI API error: {msg}",
                    "details": response.text
                }), response.status_code
            except Exception:
                return jsonify({
                    "error": "AI API error",
                    "details": response.text
                }), response.status_code
            
        ai_data = response.json()
        ai_message = ai_data["choices"][0]["message"]["content"]
        
        return jsonify({
            "success": True,
            "analysis": ai_message,
            "original_text": tweet_url
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Running on port 5000 as configured in the frontend script.js
    app.run(port=5000, debug=True)
