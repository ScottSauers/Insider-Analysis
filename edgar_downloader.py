from sec_edgar_downloader import Downloader
import datetime

# Replace with your details
company_name = "YourCompanyName"
email_address = "your.email@example.com"
download_folder = "edgar"  # Optional; specify if you want to download files to a specific location

# Initialize the downloader
dl = Downloader(company_name, email_address, download_folder)

# Parameters for downloading Form 4 filings
form_type = "4"
ticker_or_cik = "AAPL"  # Example for Apple Inc.; replace with the ticker or CIK of your interest
limit = 10  # Adjust the limit as needed; set to None to download all available filings
after = "2019-01-01"  # YYYY-MM-DD format; adjust as needed
before = datetime.date.today().strftime("%Y-%m-%d")  # Downloads up to the most recent filings
include_amends = True  # Whether to include amended filings
download_details = True  # Download human-readable and parseable filing detail documents

# Download the filings
number_of_filings_downloaded = dl.get(form=form_type, ticker_or_cik=ticker_or_cik, 
                                      limit=limit, after=after, before=before, 
                                      include_amends=include_amends, download_details=download_details)

print(f"Number of Form 4 filings downloaded: {number_of_filings_downloaded}")
