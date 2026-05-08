from flask import Blueprint, request, jsonify
from flask_login import login_required
import json, os, time

ai_nl_bp = Blueprint('ai_newsletter', __name__, url_prefix='/ai')

MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
MISTRAL_MODEL   = 'mistral-small-latest'   # fastest model
MISTRAL_URL     = 'https://api.mistral.ai/v1/chat/completions'

NL_SYSTEM_PROMPT = """You are a newsletter designer. Respond ONLY with valid JSON, no markdown, no explanation.

JSON structure:
{"title":"Title","subtitle":"Subtitle","footer":"Footer · Unsubscribe","theme":{"header_color":"#1A1A2E","accent_color":"#FF8C00"},"blocks":[{"id":"b1","type":"heading","content":{"text":"Heading","level":"h2"}}]}

Block types (use 5-7 blocks max):
- heading: {"text":"text","level":"h2"}
- text: {"html":"<p>text</p>"}
- cta: {"text":"Click","url":"#","color":"#FF8C00"}
- divider: {}
- quote: {"text":"quote","author":"name"}
- 2col: {"left":"<p>left</p>","right":"<p>right</p>"}
- spacer: {"height":20}

Write real content. Keep response SHORT. Return only JSON."""


def call_mistral(messages):
    try:
        import requests as req_lib
    except ImportError:
        raise RuntimeError("pip install requests")

    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not set in .env")

    headers = {'Authorization': f'Bearer {MISTRAL_API_KEY}', 'Content-Type': 'application/json'}
    payload = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(3):
        try:
            resp = req_lib.post(MISTRAL_URL, headers=headers, json=payload, timeout=90)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
            elif resp.status_code == 429:
                time.sleep(5)
                continue
            else:
                raise RuntimeError(f"Mistral error {resp.status_code}: {resp.text[:200]}")
        except req_lib.exceptions.Timeout:
            if attempt < 2:
                time.sleep(3)
                continue
            raise RuntimeError(
                "Request timed out after 90s. Mistral may be overloaded. "
                "Try a shorter/simpler prompt and click Generate again."
            )
        except req_lib.exceptions.ConnectionError:
            raise RuntimeError("Cannot reach Mistral. Check internet connection.")

    raise RuntimeError("Failed after 3 attempts. Please try again.")


def parse_json(raw):
    raw = raw.strip()
    if raw.startswith('```'):
        raw = '\n'.join(raw.split('\n')[1:])
        raw = raw.rstrip('`').strip()
    return json.loads(raw)


@ai_nl_bp.route('/newsletter/generate', methods=['POST'])
@login_required
def generate_newsletter():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    if not MISTRAL_API_KEY:
        return jsonify({'error': 'MISTRAL_API_KEY not set in .env'}), 500

    messages = [
        {"role": "system", "content": NL_SYSTEM_PROMPT},
        {"role": "user",   "content": f"Newsletter topic: {prompt[:300]}"}
    ]
    try:
        raw = call_mistral(messages)
        nl = parse_json(raw)
        for i, b in enumerate(nl.get('blocks', []), 1):
            if not b.get('id'):
                b['id'] = f'b{i}'
        return jsonify({'success': True, 'newsletter': nl})
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({'error': f'Bad JSON from AI: {e}'}), 500
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_nl_bp.route('/newsletter/improve', methods=['POST'])
@login_required
def improve_newsletter():
    data = request.get_json() or {}
    prompt  = data.get('prompt', '').strip()
    current = data.get('current_newsletter', {})
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    if not MISTRAL_API_KEY:
        return jsonify({'error': 'MISTRAL_API_KEY not set in .env'}), 500

    trimmed = {'title': current.get('title',''), 'blocks': current.get('blocks',[])[:6]}
    messages = [
        {"role": "system", "content": NL_SYSTEM_PROMPT},
        {"role": "user",   "content": f"Newsletter: {json.dumps(trimmed)}\nInstruction: {prompt[:200]}\nReturn updated JSON."}
    ]
    try:
        raw = call_mistral(messages)
        nl = parse_json(raw)
        for i, b in enumerate(nl.get('blocks', []), 1):
            if not b.get('id'):
                b['id'] = f'b{i}'
        return jsonify({'success': True, 'newsletter': nl})
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({'error': f'Bad JSON from AI: {e}'}), 500
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500