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

import bs4
import urllib.parse
from io import BytesIO

def call_openrouter(sys_prompt, user_prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "arcee-ai/trinity-large-preview:free",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
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
        raise Exception(f"AI API error: {response.text}")
    return response.json()["choices"][0]["message"]["content"]


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
    data = request.json
    tweet_url = data.get('url', '')
    if not tweet_url:
        return jsonify({"error": "No Twitter URL provided"}), 400

    tweet_id = tweet_url.strip('/').split('/')[-1].split('?')[0]
    username = ""
    try:
        parts = urllib.parse.urlparse(tweet_url).path.strip('/').split('/')
        if len(parts) > 0:
            username = parts[0]
    except:
        username = "Unknown"

    tweet_text = data.get('tweet_text', "")
    if not tweet_text:
        tweet_text = f"Tweet by user {username} with ID {tweet_id}"

    try:
        sys_prompt = (
            "You are an expert fact-checker and digital forensics analyst. "
            "You are evaluating a claim associated with a Twitter URL or tweet content. "
            "CRITICAL INSTRUCTIONS: "
            "1. Start with 'YES.' if verified correct, 'NO.' if incorrect/misleading, or 'PARTIAL.' if uncertain context. "
            "2. Explain your reasoning with high precision. Analyze the credibility of the specific twitter username/ecosystem, known misinformation networks, and the actual claim text provided. "
            "3. Conclude with a 'Source:' section."
        )
        user_prompt = f"Critically fact-check this tweet. Background information: Profile: @{username}. Tweet text/URL context: {tweet_text}"
        ai_message = call_openrouter(sys_prompt, user_prompt)
        return jsonify({"success": True, "analysis": ai_message, "original_text": tweet_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/article', methods=['POST'])
def analyze_article():
    data = request.json
    url = data.get('url', '')
    if not url:
        return jsonify({"error": "No Article URL provided"}), 400

    article_text = "Content could not be fetched. Relying on context."
    try:
        h = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        
        session = requests.Session()
        # Ensure we follow redirects (like from Google News)
        r = session.get(url, headers=h, timeout=15, allow_redirects=True)
        final_url = r.url
        
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        
        # If it's still a Google redirect page, try to grab the URL from the 'Refresh' meta tag
        if "google.com" in final_url or "news.google.com" in final_url:
            meta_refresh = soup.find('meta', attrs={'http-equiv': 'Refresh'})
            if meta_refresh:
                content = meta_refresh.get('content', '')
                if 'url=' in content.lower():
                    next_url = content.split('url=')[-1].split('URL=')[-1].strip()
                    if next_url:
                        r = session.get(next_url, headers=h, timeout=15, allow_redirects=True)
                        final_url = r.url
                        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        
        paragraphs = soup.find_all('p')
        content = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
        if not content and soup.title:
            content = "No paragraph text found. Possibly behind a paywall or cookie banner."
            
        if len(content) > 3000:
            content = content[:3000] + "..."
            
        article_text = f"Analyzed URL: {final_url}\nTitle: {soup.title.string if soup.title else 'Unknown'}\nContent: {content}"
    except Exception as e:
        article_text = f"URL Context Analysis: {url} - Error: {str(e)}"

    try:
        sys_prompt = (
            "You are a strict, objective journalistic fact-checker. You are analyzing real-time news articles from various sources. "
            "Your job is to determine if the core claim or reporting in the article is factually true, false, or heavily biased. "
            "1. Start with exactly 'YES.', 'NO.', or 'PARTIAL.' "
            "   - 'YES.' if the reporting is factually accurate and represents real, verifiable news. "
            "   - 'NO.' if the article spreads misinformation, lies, or completely fabricated news. "
            "   - 'PARTIAL.' if it contains extreme bias, misleading headlines, or unverified claims. "
            "2. Provide a simple 1 or 2 sentence explanation of your verdict, pointing out if the source is credible or if the claims are debunked. "
            "3. Conclude with 'Source: Real-time Article Analysis'."
        )
        user_prompt = f"Critically fact-check this news article snippet:\n\n{article_text}"
        ai_message = call_openrouter(sys_prompt, user_prompt)
        return jsonify({"success": True, "analysis": ai_message, "original_text": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/image', methods=['POST'])
def analyze_image():
    if 'file' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No image provided"}), 400
    
    try:
        from PIL import Image
        import warnings
        warnings.simplefilter('ignore', Image.DecompressionBombWarning)
        
        img = Image.open(BytesIO(file.read()))
        format_info = img.format
        mode = img.mode
        size = img.size
        exif_info = "No explicit EXIF metadata found."
        
        if hasattr(img, '_getexif') and img._getexif():
            exif_info = "EXIF Data Present (Camera/Software parameters embedded)."
            
        sys_prompt = (
            "You are a direct and simple digital image analyst. The system has extracted metadata from an image file uploaded by a user for fact-checking. "
            "You cannot see the image, but must analyze its characteristics to determine its authenticity. "
            "1. Start with exactly 'YES.', 'NO.', or 'PARTIAL.' regarding its likely authenticity. "
            "2. Give a very simple, single-sentence explanation. Just say if the image appears to be original, or if it seems manipulated/fake, just state that it is likely created or manipulated by AI/editing software. Do not use complex forensic terms."
            "3. Conclude with 'Source: Image Metadata Scan'."
        )
        user_prompt = (
            f"Image Data:\n"
            f"Filename: {file.filename}\n"
            f"Dimensions: {size[0]}x{size[1]}\n"
            f"Color Mode: {mode}\n"
            f"Encoding: {format_info}\n"
            f"Metadata Status: {exif_info}\n\n"
            f"Tell me simply: is this image original, or is it likely a fake/manipulated/AI image?"
        )
        ai_message = call_openrouter(sys_prompt, user_prompt)
        return jsonify({"success": True, "analysis": ai_message, "original_text": file.filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/video', methods=['POST'])
def analyze_video():
    if request.is_json:
        data = request.json
        video_url = data.get('url', '')
        if not video_url:
            return jsonify({"error": "No video URL provided"}), 400
        
        try:
            sys_prompt = (
                "You are a strict video verification assistant checking a social media video link. Here is your ONLY rule: "
                "A video is considered MANIPULATED/FAKE *only* if it is 100% fully generated by AI (like OpenAI Sora, Runway, etc.). "
                "All other videos, even if edited, clipped, or heavily compressed, MUST be considered REAL. "
                "1. If it is a real video (even an edited one), start with 'YES.' and say 'This is a real video.' "
                "2. If it is a fully AI-generated video, start with 'NO.' and say 'This video is fully generated by AI.' "
                "3. Keep your explanation to exactly 1 sentence."
            )
            user_prompt = (
                f"Video Link Context:\nURL: {video_url}\n\n"
                f"Is the video at this link a real captured video, or is it fully generated by AI?"
            )
            ai_message = call_openrouter(sys_prompt, user_prompt)
            return jsonify({"success": True, "analysis": ai_message, "original_text": video_url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if 'file' not in request.files:
        return jsonify({"error": "No video uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No video provided"}), 400

    try:
        file.seek(0, 2)
        fsize = file.tell()
        sys_prompt = (
            "You are a strict video verification assistant checking a video file. Here is your ONLY rule: "
            "A video is considered MANIPULATED/FAKE *only* if it is 100% fully generated by AI (like OpenAI Sora, Runway, etc.). "
            "All other videos, even if edited, clipped, or heavily compressed, MUST be considered REAL. "
            "1. If the telemetry data points to a real camera-captured video (even an edited one), start with 'YES.' and say 'This is a real video.' "
            "2. If the telemetry data points to a fully AI-generated video, start with 'NO.' and say 'This video is fully generated by AI.' "
            "3. Keep your explanation to exactly 1 sentence."
        )
        user_prompt = (
            f"Video File Data:\n"
            f"Filename: {file.filename}\n"
            f"File Size: {fsize / 1024 / 1024:.2f} MB\n"
            f"Is this a real captured video, or is it fully generated by AI?"
        )
        ai_message = call_openrouter(sys_prompt, user_prompt)
        return jsonify({"success": True, "analysis": ai_message, "original_text": file.filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Running on port 5000 as configured in the frontend script.js
    app.run(port=5000, debug=True)
