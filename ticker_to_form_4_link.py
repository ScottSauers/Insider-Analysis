import requests
from bs4 import BeautifulSoup

# Set the CIK number and form type you're interested in
cik_number = '789019'  # Corrected CIK for Microsoft, without leading zeros
form_type = '4'

# SEC EDGAR base URL for browsing
base_url = 'https://www.sec.gov/cgi-bin/browse-edgar'

# Headers to mimic web browser access
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
    'owner': 'exclude',
    'output': 'atom',
    'start': 0,
    'count': 10 #however many you want
}

# Loop to handle pagination and fetch filings
while True:
    response = requests.get(base_url, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        entries = soup.find_all('entry')

        if not entries:
            break  # No more entries

        for entry in entries:
            # Extract the accession number
            accession_number = entry.find('accession-number').text
            # Correctly format the URL to include dashes in the accession number
            filing_txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik_number}/{accession_number.replace('-', '')}/{accession_number}.txt"
            print(f"Link to Form 4 filing (.txt): {filing_txt_url}")

        # Update 'start' for pagination
        params['start'] += len(entries)
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
        break
