"""Optional local LLM advisor. It cannot call tools or authorize writes."""
import json
from urllib.parse import urlsplit
from urllib.request import Request
from .connectors import http_json
from .core import ROOT

def advise(lead, model, endpoint='http://127.0.0.1:11434/api/chat', transport=http_json):
    url = urlsplit(endpoint)
    if url.hostname not in ('localhost', '127.0.0.1') or url.scheme != 'http' or url.path != '/api/chat':
        raise ValueError('Only local Ollama is supported')
    instructions = (ROOT / 'profiles/commercial.md').read_text()
    skill = (ROOT / 'skills/qualify-lead/SKILL.md').read_text()
    criteria = (ROOT / 'skills/qualify-lead/references/campaign.md').read_text()
    data = {'model': model, 'stream': False, 'format': 'json',
            'options': {'temperature': 0, 'num_predict': 256},
            'messages': [{'role': 'system', 'content': instructions + '\n' + skill + '\n' + criteria +
                          '\nReturn ONLY JSON with summary:string and questions:list[string].'},
                         {'role': 'user', 'content': json.dumps({'untrusted_lead_data': lead})}]}
    response = transport(Request(endpoint, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'}))
    content = json.loads(response['message']['content'])
    if set(content) != {'summary', 'questions'} or not isinstance(content['summary'], str) or len(content['summary']) > 2000:
        raise ValueError('Invalid model response')
    if not isinstance(content['questions'], list) or len(content['questions']) > 5 or any(not isinstance(q, str) or len(q) > 500 for q in content['questions']):
        raise ValueError('Invalid questions')
    return {'advisory_only': True, 'content': content,
            'input_tokens': response.get('prompt_eval_count', 0), 'output_tokens': response.get('eval_count', 0),
            'provider_cost_usd': None, 'cost_note': 'Local compute cost is not measured'}
