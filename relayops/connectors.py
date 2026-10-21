"""Narrow adapters. Credentials are supplied by the operator, never by an LLM."""
import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

def http_json(request):
    with urlopen(request, timeout=20) as response:
        return json.load(response)

class GoogleSheets:
    def __init__(self, spreadsheet_id, token, transport=http_json):
        if not re.fullmatch(r'[A-Za-z0-9_-]+', spreadsheet_id) or not token:
            raise ValueError('Spreadsheet ID and OAuth access token required')
        self.base = 'https://sheets.googleapis.com/v4/spreadsheets/' + spreadsheet_id + '/values/'
        self.token, self.transport = token, transport
    def _request(self, range_name, body=None):
        url = self.base + quote(range_name, safe='')
        headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'}
        if body is None:
            return self.transport(Request(url, headers=headers))
        return self.transport(Request(url + '?valueInputOption=RAW', data=json.dumps({'values': body}).encode(), headers=headers, method='PUT'))
    def export_summary(self, results):
        values = [['lead_id', 'status', 'reason', 'input_hash']]
        values += [[r['id'], r['status'], r['reason'], r['input_hash']] for r in results]
        area = 'RelayOps!A1:D' + str(len(values))
        self._request(area, values)
        if self._request(area).get('values', []) != values:
            raise RuntimeError('Read-back differs from intended write')
        return {'rows_verified': len(values) - 1, 'range': area}
