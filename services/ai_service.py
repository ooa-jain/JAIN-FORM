import json
import os
import time
import requests

MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
MISTRAL_MODEL   = 'mistral-small-latest'
MISTRAL_URL     = 'https://api.mistral.ai/v1/chat/completions'

def call_mistral(messages, temperature=0.3, max_tokens=2000, response_format=None):
    """Utility to call Mistral AI with automatic retries and JSON modes."""
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY is not set in environment configurations.")

    headers = {
        'Authorization': f'Bearer {MISTRAL_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    if response_format:
        payload["response_format"] = response_format

    for attempt in range(3):
        try:
            resp = requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
            elif resp.status_code == 429:
                time.sleep(3)
                continue
            else:
                raise RuntimeError(f"Mistral API returned error {resp.status_code}: {resp.text[:300]}")
        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(2)
                continue
            raise RuntimeError("Mistral API requests timed out.")
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            raise RuntimeError(f"Mistral connection error: {str(e)}")

    raise RuntimeError("Failed to communicate with Mistral AI after 3 attempts.")

def parse_json(raw_text):
    """Cleans up markdown formatting and parses raw JSON outputs."""
    raw = raw_text.strip()
    if raw.startswith('```'):
        lines = raw.split('\n')
        raw = '\n'.join(lines[1:])
        if raw.endswith('```'):
            raw = raw[:-3]
    return json.loads(raw.strip())

def summarize_responses(form, responses):
    """Processes responses to extract insights, sentiment scores, and recommendations."""
    if not MISTRAL_API_KEY:
        # Graceful fallback mock
        return {
            "insights": ["Collected valuable community submissions.", "Consistent engagement across most form fields."],
            "sentiment": {"label": "Neutral", "score": 75, "explanation": "No API key configured for deep sentiment parsing."},
            "trends": ["Participants shared balanced feedback."],
            "recommendations": ["Optimize fields with higher text inputs."]
        }

    # Prepare response snippets for token limit safety
    submissions_sample = []
    for r in responses[:30]: # sample first 30 responses
        answers = {}
        for page in form.get('pages', []):
            for field in page.get('fields', []):
                val = r.get('data', {}).get(field['id'], '')
                if val:
                    answers[field['label']] = val
        submissions_sample.append(answers)

    system_prompt = (
        "You are an expert research analyst. Review the form questions and user responses, "
        "and respond ONLY with a valid JSON containing: "
        "insights (list of strings), sentiment (object with label [Positive, Negative, Neutral], "
        "score [0-100], and explanation), trends (list of strings), recommendations (list of strings)."
    )
    user_prompt = f"Form: {form['title']}\nDescription: {form.get('description','')}\nSubmissions:\n{json.dumps(submissions_sample[:20])}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        raw = call_mistral(messages, response_format={"type": "json_object"})
        return parse_json(raw)
    except Exception as e:
        print(f"Error in summarize_responses: {e}")
        return {
            "insights": ["Failed to extract AI insights.", str(e)],
            "sentiment": {"label": "Neutral", "score": 50, "explanation": "Error during analysis parsing."},
            "trends": [],
            "recommendations": ["Please check your Mistral API settings."]
        }

def generate_marketing_assets(form, responses, asset_type):
    """Generates blog drafts, Twitter threads, or newsletters based on form answers."""
    if not MISTRAL_API_KEY:
        return f"### AI Content Engine Draft\n\nThis is a mock placeholder. Mistral API is not configured. Form: {form['title']}"

    summary = summarize_responses(form, responses)
    
    prompts = {
        'blog_post': "Write a compelling, professional blog post reporting the key findings of this survey. Use clear headers and formatting.",
        'newsletter': "Write an engaging email newsletter campaigns sharing the survey results with our subscribers. Keep the tone warm and conversational.",
        'social_thread': "Create a viral Twitter/X social thread (5-8 tweets) presenting these insights. Use relevant hook lines and emojis.",
        'insight_report': "Write a formal, comprehensive analytical insight report outlining background, findings, and strategic takeaways."
    }
    
    instruction = prompts.get(asset_type, prompts['insight_report'])
    system_prompt = "You are a professional content creator. Write detailed, high-quality copy in clean Markdown. Respond ONLY with the markdown text."
    user_prompt = f"Survey findings: {json.dumps(summary)}\nOriginal form title: {form['title']}\nInstructions: {instruction}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        return call_mistral(messages, temperature=0.7, max_tokens=1500)
    except Exception as e:
        return f"Failed to generate content: {str(e)}"

def moderate_text(text):
    """Detects spam, toxic vocabulary, abuse, or prompt injections."""
    if not MISTRAL_API_KEY:
        return {"is_flagged": False, "reason": "No moderation filter active", "confidence": 1.0}

    system_prompt = (
        "Analyze the text for toxicity, explicit/inappropriate content, obvious spam link insertions, or abusive terms. "
        "Respond ONLY with a valid JSON: {\"is_flagged\": true/false, \"reason\": \"text explaining reason\", \"confidence\": 0.0-1.0}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Text to analyze: {text[:1000]}"}
    ]

    try:
        raw = call_mistral(messages, temperature=0.1, response_format={"type": "json_object"})
        return parse_json(raw)
    except Exception as e:
        print(f"Moderation error: {e}")
        return {"is_flagged": False, "reason": f"Moderation service error: {e}", "confidence": 0.5}
