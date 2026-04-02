from flask import Blueprint, request, jsonify
from flask_login import login_required
import json, os

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
MISTRAL_MODEL   = 'mistral-large-latest'
MISTRAL_URL     = 'https://api.mistral.ai/v1/chat/completions'

SYSTEM_PROMPT = """You are a form builder AI. When given a description of a form, respond ONLY with a valid JSON object — no explanation, no markdown, no code blocks, no backticks.

The JSON must follow this exact structure:
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
          "placeholder": "Optional placeholder"
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

For radio/checkbox/dropdown add: "options": ["Option 1", "Option 2", "Option 3"]
For rating add: "max_rating": 5
For scale add: "scale_max": 10

Rules:
- Field IDs must be unique: f_1, f_2, f_3... across ALL pages
- Page IDs: page_1, page_2...
- Use 1 page for simple forms, 2-4 pages for complex forms
- Pick theme colors matching the topic:
    education/academic = blue (#003366 header, #0066CC accent)
    health/medical = green (#134E5E header, #2D6A4F accent)
    events = purple (#4a00e0 header, #8e2de2 accent)
    corporate = dark navy (#0F2027 header, #2980B9 accent)
    general/feedback = default (#1A1A2E header, #FF8C00 accent)
- Make forms practical and complete with relevant questions
- Return ONLY raw JSON, absolutely nothing else"""


def call_mistral(messages):
    try:
        import requests as req_lib
    except ImportError:
        raise RuntimeError("requests library not installed. Run: pip install requests")

    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not set in .env")

    headers = {
        'Authorization': f'Bearer {MISTRAL_API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    payload = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }

    resp = req_lib.post(MISTRAL_URL, headers=headers, json=payload, timeout=30)

    if resp.status_code != 200:
        raise RuntimeError(f"Mistral API error {resp.status_code}: {resp.text[:400]}")

    return resp.json()['choices'][0]['message']['content']


def parse_form_json(raw):
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
    data = request.get_json()
    prompt = (data or {}).get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    if not MISTRAL_API_KEY:
        return jsonify({'error': 'MISTRAL_API_KEY not set in .env file'}), 500

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"Create a form for: {prompt}"}
    ]

    try:
        raw = call_mistral(messages)
        form_data = parse_form_json(raw)
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
    data = request.get_json()
    prompt  = (data or {}).get('prompt', '').strip()
    current = (data or {}).get('current_form', {})
    if not prompt or not current:
        return jsonify({'error': 'Missing prompt or current form'}), 400
    if not MISTRAL_API_KEY:
        return jsonify({'error': 'MISTRAL_API_KEY not set in .env file'}), 500

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content":
            f"Here is an existing form:\n{json.dumps(current, indent=2)}\n\n"
            f"User instruction: {prompt}\n\n"
            f"Modify the form and return the complete updated form JSON."}
    ]

    try:
        raw = call_mistral(messages)
        form_data = parse_form_json(raw)
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