import requests
from bs4 import BeautifulSoup

# SEC EDGAR base URL for browsing
base_url = 'https://www.sec.gov/cgi-bin/browse-edgar'

# Correct CIK for Microsoft and the desired Form Type
cik_number = '789019'  # Microsoft's CIK without leading zeros
form_type = '4'  # Targeting only Form 4 filings

# Headers to mimic web browser access, with a declared user-agent
headers = {
    'User-Agent': 'Sample Company Name AdminContact@samplecompanydomain.com',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}

# Parameters for the GET request
params = {
    'action': 'getcompany',
    'CIK': cik_number,
    'type': form_type,
    'dateb': '',
    'owner': 'include',
    'output': 'atom',
    'start': 0,
    'count': 100
}

response = requests.get(base_url, headers=headers, params=params)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'lxml')
    entries = soup.find_all('entry')
    for entry in entries:
        accession_number = entry.find('accession-number').text
        filing_href = f"https://www.sec.gov/Archives/edgar/data/{cik_number}/{accession_number.replace('-', '')}/{accession_number}.txt"
        print(f"Link to Form 4 filing (.txt): {filing_href}")
else:
    print(f"Failed to fetch data, status code: {response.status_code}")
