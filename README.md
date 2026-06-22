# Fact-Checking & Fraud Detection API

A Flask-based backend service designed to detect fraud, verify claims, and perform digital forensic analysis. By leveraging OpenRouter API (`arcee-ai/trinity-large-preview:free`), NewsAPI, and basic image/video metadata checks, this tool helps users critically fact-check text, social media claims (Twitter), news articles, images, and videos.

---

## 🚀 Key Features

*   **Fact-Checking / Text Analysis**: Critically evaluate claims and facts, returning a precise `YES` or `NO` verdict along with reasoning and authoritative source links.
*   **Twitter/X Post Verification**: Fact-check social media claims, analyzing the tweet context and the credibility of the profile ecosystem.
*   **Article Analysis & Web Crawling**: Automatically fetch, parse, and verify the main content of online articles, even resolving Google News redirects.
*   **Real-time News Retrieval**: Fetch top general news headlines in real-time.
*   **Image Authenticity Scan**: Analyze uploaded image dimensions and EXIF metadata to identify potential AI generation or digital manipulation.
*   **Video Verification**: Scan video files or links to determine if they are fully AI-generated or captured with a real camera.

---

## 🛠️ Technology Stack

*   **Backend**: Python, Flask, Flask-CORS
*   **AI Integration**: OpenRouter API (`arcee-ai/trinity-large-preview:free`)
*   **Web Scraping / Crawling**: BeautifulSoup4 (`bs4`), Requests
*   **Digital Forensics / Media Scan**: Pillow (`PIL`)
*   **Testing**: Python requests and authentication verification scripts

---

## 📦 Setup & Installation

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system.

### 2. Clone the Repository
```bash
git clone <repository-url>
cd fraud-detection
```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
The application utilizes several third-party services. Configure the following environment variables on your system:

| Environment Variable | Description |
| :--- | :--- |
| `OPENROUTER_API_KEY` | **Required.** API key for OpenRouter to query the LLM. |
| `NEWS_API_KEY` | Key to fetch real-time news headlines via NewsAPI. |
| `TWITTER_KEY` | Optional key to access Twitter-related APIs. |
| `GOOGLE_API_KEY` | Optional Google API Key. |

> [!NOTE]
> If environment variables are not set, the server will fallback to preconfigured keys defined in [app.py](file:///c:/Users/ys770.SUNNY/OneDrive/Videos/Captures/fraud-detection/app.py).

---

## 📡 API Endpoints & Usage

### 1. Fact-Check Text
Analyze a raw text claim to determine if it is factually correct.

*   **Endpoint**: `/api/analyze`
*   **Method**: `POST`
*   **Content-Type**: `application/json`
*   **Request Payload**:
    ```json
    {
      "text": "The Earth is flat"
    }
    ```
*   **Response Payload**:
    ```json
    {
      "success": true,
      "original_text": "The Earth is flat",
      "analysis": "NO. The Earth is an oblate spheroid. This has been proven through satellite imagery, space exploration, and physics experiments.\n\nSource: https://www.nasa.gov"
    }
    ```

### 2. Fact-Check Twitter URL
Analyze a tweet's content and its poster's credibility.

*   **Endpoint**: `/api/twitter`
*   **Method**: `POST`
*   **Request Payload**:
    ```json
    {
      "url": "https://twitter.com/username/status/1234567890",
      "tweet_text": "Claim description or text if available"
    }
    ```

### 3. Fact-Check Article URL
Fetch article body text from a webpage and fact-check it.

*   **Endpoint**: `/api/article`
*   **Method**: `POST`
*   **Request Payload**:
    ```json
    {
      "url": "https://example.com/news-article"
    }
    ```

### 4. Real-time News
Fetch top general news headlines in the US.

*   **Endpoint**: `/api/news`
*   **Method**: `GET`

### 5. Verify Uploaded Image Authenticity
Check if an image file has EXIF metadata or details indicative of AI generation/manipulation.

*   **Endpoint**: `/api/image`
*   **Method**: `POST`
*   **Content-Type**: `multipart/form-data`
*   **Request Parameter**: `file` (binary image)

### 6. Verify Video (Link or Uploaded File)
Determine if a video is fully AI-generated or a real captured video.

*   **Endpoint**: `/api/video`
*   **Method**: `POST`
*   **Request (for link)**:
    *   **Content-Type**: `application/json`
    *   **Payload**: `{"url": "https://example.com/video.mp4"}`
*   **Request (for file upload)**:
    *   **Content-Type**: `multipart/form-data`
    *   **Parameter**: `file` (binary video)

---

## 🏃 Running the Application

To start the Flask development server (running on port `5000` by default):

```bash
python app.py
```

---

## 🧪 Testing Scripts

Several testing scripts are included in the repository to verify API operations and API key validation:

*   **[test.py](file:///c:/Users/ys770.SUNNY/OneDrive/Videos/Captures/fraud-detection/test.py) / [test_openrouter.py](file:///c:/Users/ys770.SUNNY/OneDrive/Videos/Captures/fraud-detection/test_openrouter.py)**: Quick scripts to test the `/api/analyze` endpoint against a running server.
*   **[test_auth.py](file:///c:/Users/ys770.SUNNY/OneDrive/Videos/Captures/fraud-detection/test_auth.py)**: Validates authentication setups and format configurations with OpenRouter.
*   **[test_key_direct.py](file:///c:/Users/ys770.SUNNY/OneDrive/Videos/Captures/fraud-detection/test_key_direct.py)**: Directly tests queries to OpenRouter's endpoint using the configured keys.
*   **[test_ds.py](file:///c:/Users/ys770.SUNNY/OneDrive/Videos/Captures/fraud-detection/test_ds.py)**: Evaluates a direct OpenRouter connection using specific key configurations.
