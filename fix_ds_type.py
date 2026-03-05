import requests
import json

auth = ('admin', 'admin')

r = requests.get('http://localhost:3000/api/search', auth=auth)
for db in r.json():
    uid = db.get('uid')
    if not uid:
        continue
    r2 = requests.get(f'http://localhost:3000/api/dashboards/uid/{uid}', auth=auth)
    if r2.status_code != 200:
        continue
    content = json.dumps(r2.json())
    fixed = content.replace('"type": "postgres"', '"type": "grafana-postgresql-datasource"')
    if fixed == content:
        print(uid, 'no change needed')
        continue
    d2 = json.loads(fixed)
    payload = {'dashboard': d2['dashboard'], 'overwrite': True, 'folderId': 0}
    r3 = requests.post('http://localhost:3000/api/dashboards/db', auth=auth, json=payload)
    print(uid, r3.status_code, r3.json().get('status'))

print('Done - now refresh Grafana with Ctrl+F5')
