import requests
import time

URL = 'http://localhost:8080/api/v1/dags'
for i in range(20):
    try:
        response = requests.get(URL, auth=('airflow', 'airflow'), timeout=2)
        if response.status_code == 200:
            dags = response.json().get('dags', [])
            print('✓ DAGs loaded:')
            for dag in dags:
                print(f"  • {dag['dag_id']}")
            break
    except:
        time.sleep(1)
else:
    print('✗ Could not connect to Airflow')
