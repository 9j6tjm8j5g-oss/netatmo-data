import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

  def do_GET(self):
    client_id = os.environ.get('NETATMO_CLIENT_ID')
    client_secret = os.environ.get('NETATMO_CLIENT_SECRET')
    refresh_token = os.environ.get('NETATMO_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
      self.send_response(500)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      error_msg = json.dumps(
          {'error': 'Missing environment variables on Vercel'}
      )
      self.wfile.write(error_msg.encode('utf-8'))
      return

    try:
      # Token erneuern
      token_url = 'https://api.netatmo.com/oauth2/token'
      payload = urllib.parse.urlencode({
          'grant_type': 'refresh_token',
          'refresh_token': refresh_token,
          'client_id': client_id,
          'client_secret': client_secret,
      }).encode('utf-8')

      req = urllib.request.Request(
          token_url, data=payload, method='POST'
      )
      with urllib.request.urlopen(req) as response:
        token_data = json.loads(response.read().decode('utf-8'))
        access_token = token_data.get('access_token')

      # Daten abrufen
      data_url = f'https://api.netatmo.com/api/getstationsdata?access_token={access_token}'
      with urllib.request.urlopen(data_url) as response:
        station_data = json.loads(response.read().decode('utf-8'))

      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      self.wfile.write(json.dumps(station_data).encode('utf-8'))

    except Exception as e:
      self.send_response(500)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
