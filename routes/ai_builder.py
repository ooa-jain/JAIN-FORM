from flask import Blueprint, request, jsonify
from flask_login import login_required
import json, os, time

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
MISTRAL_MODEL   = 'mistral-small-latest'
MISTRAL_URL     = 'https://api.mistral.ai/v1/chat/completions'

SYSTEM_PROMPT = """You are a form builder AI. Respond ONLY with valid JSON — no explanation, no markdown, no backticks.

JSON structure:
{
  "title": "Form Title",
  "description": "Brief description",
  "pages": [
    {
      "id": "page_1",
      "title": "Page 1",
      "fields": [
        {
          "id": "f_1",
          "type": "short_text",
          "label": "Question label",
          "help": "",
          "required": true,
          "placeholder": "Optional"
        }
      ]
    }
  ],
  "theme": {
    "bg_color": "#F8F9FA",
    "header_color": "#1A1A2E",
    "accent_color": "#FF8C00",
    "text_color": "#212529",
    "card_color": "#FFFFFF",
    "font": "DM Sans",
    "cover_image": "",
    "button_text": "Submit"
  },
  "settings": {
    "is_published": false,
    "show_progress": true,
    "confirmation_message": "Thank you for your response!",
    "redirect_url": "",
    "notify_email": "",
    "notify_on_submit": false
  }
}

Field types: short_text, long_text, number, email, phone, radio, checkbox, dropdown, date, time, rating, scale, file, header, divider
For radio/checkbox/dropdown add: "options": ["Option 1", "Option 2"]
For rating add: "max_rating": 5
For scale add: "scale_max": 10

Rules:
- Field IDs unique: f_1, f_2... across ALL pages
- Page IDs: page_1, page_2...
- Keep forms to 8-12 fields max (shorter = faster response)
- Return ONLY raw JSON"""


def call_mistral(messages):
    try:
        import requests as req_lib
    except ImportError:
        raise RuntimeError("requests library not installed. Run: pip install requests")

    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not set in .env file")

    headers = {'Authorization': f'Bearer {MISTRAL_API_KEY}', 'Content-Type': 'application/json'}
    payload = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2000,
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
                raise RuntimeError(f"Mistral API error {resp.status_code}: {resp.text[:300]}")
        except req_lib.exceptions.Timeout:
            if attempt < 2:
                time.sleep(3)
                continue
            raise RuntimeError(
                "Request timed out. Mistral may be overloaded. "
                "Try a shorter/simpler prompt and click Generate again."
            )
        except req_lib.exceptions.ConnectionError:
            raise RuntimeError("Cannot connect to Mistral API. Check your internet connection.")

    raise RuntimeError("Failed after 3 attempts. Please try again.")


def parse_json(raw):
    raw = raw.strip()
    if raw.startswith('```'):
        lines = raw.split('\n')
        raw = '\n'.join(lines[1:])
        if raw.endswith('```'):
            raw = raw[:-3]
    return json.loads(raw.strip())


@ai_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    if not MISTRAL_API_KEY:
        return jsonify({'error': 'MISTRAL_API_KEY not set in .env file'}), 500

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"Create a form for: {prompt[:400]}"}
    ]
    try:
        raw = call_mistral(messages)
        form_data = parse_json(raw)
        form_data.setdefault('settings', {
            'is_published': False, 'show_progress': True,
            'confirmation_message': 'Thank you for your response!',
            'redirect_url': '', 'notify_email': '', 'notify_on_submit': False
        })
        return jsonify({'success': True, 'form': form_data})
    except json.JSONDecodeError as e:
        return jsonify({'error': f'AI returned invalid JSON: {str(e)}'}), 500
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/improve', methods=['POST'])
@login_required
def improve():
    data = request.get_json() or {}
    prompt  = data.get('prompt', '').strip()
    current = data.get('current_form', {})
    if not prompt or not current:
        return jsonify({'error': 'Missing prompt or current form'}), 400
    if not MISTRAL_API_KEY:
        return jsonify({'error': 'MISTRAL_API_KEY not set in .env file'}), 500

    # Trim to avoid large payloads
    trimmed = {
        'title': current.get('title',''),
        'pages': [{'id': p.get('id'), 'title': p.get('title'), 'fields': p.get('fields',[])}
                  for p in current.get('pages',[])],
        'theme': current.get('theme', {}),
        'settings': current.get('settings', {})
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content":
            f"Existing form:\n{json.dumps(trimmed)}\n\n"
            f"Instruction: {prompt[:300]}\n\n"
            f"Return the complete updated form JSON."}
    ]
    try:
        raw = call_mistral(messages)
        form_data = parse_json(raw)
        form_data.setdefault('settings', current.get('settings', {
            'is_published': False, 'show_progress': True,
            'confirmation_message': 'Thank you for your response!',
            'redirect_url': '', 'notify_email': '', 'notify_on_submit': False
        }))
        return jsonify({'success': True, 'form': form_data})
    except json.JSONDecodeError as e:
        return jsonify({'error': f'AI returned invalid JSON: {str(e)}'}), 500
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500