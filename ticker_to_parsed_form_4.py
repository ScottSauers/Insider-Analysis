import requests
from bs4 import BeautifulSoup
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import re
import numpy as np
import json

def ticker_to_cik(ticker):
    file_path = "company_tickers.json"  # Assuming the file is in the current directory
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Iterate over each entry in the "data" list to find the matching ticker and exchange
        for entry in data["data"]:
            if entry[2] == ticker and entry[3] == "Nasdaq":
                return entry[0]  # Return the CIK number if found for NASDAQ listed company
    except Exception as e:
        return f"Error: {str(e)}"
    return "Ticker not found or not listed on Nasdaq"


def get_links(cik_number, dates):
    base_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
    form_type = '4'  # Form 4 filings
    headers = {
        'User-Agent': 'Sample Company Name AdminContact@samplecompanydomain.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    params = {
        'action': 'getcompany',
        'CIK': cik_number,
        'type': form_type,
        'dateb': '',
        'owner': 'include',
        'output': 'atom',
    }

    links = []
    start = 0
    entries_per_page = 100

    if '-' in dates:
        start_year, end_year = map(int, dates.split('-'))
    else:
        start_year = end_year = int(dates)

    while True:
        params['start'] = start
        params['count'] = entries_per_page
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml-xml')
            entries = soup.find_all('entry')
            if not entries:
                break

            for entry in entries:
                accession_number = entry.find('accession-number').text
                year_part = accession_number.split('-')[1]
                # Adjust the century based on the year part's first digit
                year = int("19" + year_part if year_part.startswith('9') else "20" + year_part)

                if start_year <= year <= end_year:
                    filing_href = f"https://www.sec.gov/Archives/edgar/data/{cik_number}/{accession_number.replace('-', '')}/{accession_number}.txt"
                    links.append(filing_href)

            start += entries_per_page
        else:
            print(f"Failed to fetch data, status code: {response.status_code}")
            break

    return links


def parse_345(link):

    def clean_text_xml(file):
        page = file.split("\\n")
        cleanedPage = ""
        counter = 0
        documentStart = re.compile('\<XML\>')
        documentEnd = re.compile('\<\/XML\>')
        for line in page:
            if counter == 0:
                if documentStart.search(line) is not None:
                    counter = counter + 1
                else:
                    continue
            else:
                if documentEnd.search(line) is not None:
                    counter = 0
                else:
                    cleanedPage = cleanedPage + line + " "

        cleanedPage = bs(cleanedPage, "xml")
        return(cleanedPage)

    def get_identity(text):

        counter = 0
        infoList = list()

        issuer = text.find("issuer")
        if issuer.find("issuerCik") is not None:
            infoList.append(["firmCIK", issuer.find("issuerCik").text.strip()])
        if issuer.find("issuerName") is not None:
            infoList.append(["firmName", issuer.find("issuerName").text.strip()])
        if issuer.find("issuerTradingSymbol") is not None:
            infoList.append(["firmTicker", issuer.find("issuerTradingSymbol").text.strip()])

        owner = text.find("reportingOwnerId")
        if owner.find("rptOwnerCik") is not None:
            infoList.append(["executiveCIK", owner.find("rptOwnerCik").text.strip()])
        if owner.find("rptOwnerName") is not None:
            infoList.append(["executiveName", owner.find("rptOwnerName").text.strip()])

        address = text.find("reportingOwnerAddress")
        if address.find("rptOwnerStreet1") is not None:
            infoList.append(["ownerAddress1", address.find("rptOwnerStreet1").text.strip()])
        if address.find("rptOwnerStreet2") is not None:
            infoList.append(["ownerAddress2", address.find("rptOwnerStreet2").text.strip()])
        if address.find("rptOwnerCity") is not None:
            infoList.append(["ownerCity", address.find("rptOwnerCity").text.strip()])
        if address.find("rptOwnerState") is not None:
            infoList.append(["ownerState", address.find("rptOwnerState").text.strip()])
        if address.find("rptOwnerZipCode") is not None:
            infoList.append(["ownerZipCode", address.find("rptOwnerZipCode").text.strip()])

        relationship = text.find("reportingOwnerRelationship")
        if relationship.find("isDirector") is not None:
            infoList.append(["isDirector", relationship.find("isDirector").text.strip()])
        if relationship.find("isOfficer") is not None:
            infoList.append(["isOfficer", relationship.find("isOfficer").text.strip()])
        if relationship.find("isTenPercentOwner") is not None:
            infoList.append(["isTenPercentOwner", relationship.find("isTenPercentOwner").text.strip()])
        if relationship.find("isOther") is not None:
            infoList.append(["isOther", relationship.find("isOther").text.strip()])
        if relationship.find("officerTitle") is not None:
            infoList.append(["officerTitle", relationship.find("officerTitle").text.strip()])
        if relationship.find("otherText") is not None:
            infoList.append(["otherText", relationship.find("otherText").text.strip()])

        if text.find("documentType") is not None:
            infoList.append(["documentType", text.find("documentType").text.strip()])
        if text.find("periodOfReport") is not None:
            infoList.append(["periodOfReport", text.find("periodOfReport").text.strip()])
        if text.find("notSubjectToSection16") is not None:
            infoList.append(["notSubjectToSection16", text.find("notSubjectToSection16").text.strip()])
        if text.find("dateOfOriginalSubmission") is not None:
            infoList.append(["dateOfOriginalSubmission", text.find("dateOfOriginalSubmission").text.strip()])


        dataDict = dict()
        for item in infoList:
            dataDict[item[0]] = item[1]

        data = pd.DataFrame.from_dict([dataDict])
        return(data)

    def get_transaction_row(transaction):
        infoTransaction = list()

        if transaction.find("securityTitle") is not None:
            infoTransaction.append(["securityTitle", transaction.find("securityTitle").text.strip()])
        if transaction.find("transactionDate") is not None:
            infoTransaction.append(["transactionDate", transaction.find("transactionDate").text.strip()])
        if transaction.find("conversionOrExercisePrice") is not None:
            infoTransaction.append(["conversionOrExercisePrice", transaction.find("conversionOrExercisePrice").text.strip()])

        if transaction.find("transactionCoding") is not None:
            trnsctnCoding = transaction.find("transactionCoding")
            if trnsctnCoding.find("transactionFormType") is not None:
                infoTransaction.append(["transactionFormType", trnsctnCoding.find("transactionFormType").text.strip()])
            if trnsctnCoding.find("transactionCode") is not None:
                infoTransaction.append(["transactionCode", trnsctnCoding.find("transactionCode").text.strip()])
            if trnsctnCoding.find("equitySwapInvolved") is not None:
                infoTransaction.append(["equitySwapInvolved", trnsctnCoding.find("equitySwapInvolved").text.strip()])  

        if transaction.find("transactionAmounts") is not None:
            trnsctnAmounts = transaction.find("transactionAmounts")
            if trnsctnAmounts.find("transactionShares") is not None:
                infoTransaction.append(["transactionShares", trnsctnAmounts.find("transactionShares").text.strip()])
            if trnsctnAmounts.find("transactionPricePerShare") is not None:
                infoTransaction.append(["transactionPricePerShare", trnsctnAmounts.find("transactionPricePerShare").text.strip()])
            if trnsctnAmounts.find("transactionAcquiredDisposedCode") is not None:
                infoTransaction.append(["transactionAcquiredDisposedCode", trnsctnAmounts.find("transactionAcquiredDisposedCode").text.strip()])

        if transaction.find("exerciseDate") is not None:
            infoTransaction.append(["exerciseDate", transaction.find("exerciseDate").text.strip()])
        if transaction.find("expirationDate") is not None:
            infoTransaction.append(["expirationDate", transaction.find("expirationDate").text.strip()])

        if transaction.find("underlyingSecurity") is not None:
            trnsctnUnderlying = transaction.find("underlyingSecurity")
            if trnsctnUnderlying.find("underlyingSecurityTitle") is not None:
                infoTransaction.append(["underlyingSecurityTitle", trnsctnUnderlying.find("underlyingSecurityTitle").text.strip()])
            if trnsctnUnderlying.find("underlyingSecurityShares") is not None:
                infoTransaction.append(["underlyingSecurityShares", trnsctnUnderlying.find("underlyingSecurityShares").text.strip()])

        if transaction.find("sharesOwnedFollowingTransaction") is not None:
            infoTransaction.append(["sharesOwnedFollowingTransaction", transaction.find("sharesOwnedFollowingTransaction").text.strip()])
        if transaction.find("directOrIndirectOwnership") is not None:
            infoTransaction.append(["directOrIndirectOwnership", transaction.find("directOrIndirectOwnership").text.strip()])
        if transaction.find("natureOfOwnership") is not None:
            infoTransaction.append(["natureOfOwnership", transaction.find("natureOfOwnership").text.strip()])

        return(infoTransaction)

    def get_non_derivative_table(text):
        tableNonDerivative = text.find_all(re.compile(r"nonDerivativeTransaction|nonDerivativeHolding"))
        infoNonTable = list()
        for transaction in tableNonDerivative:
            transactionDict = dict()
            infoTransaction = get_transaction_row(transaction)

            for item in infoTransaction:
                transactionDict[item[0]] = item[1]

            transactionDict["table"] = "I: Non-Derivative Securities"
            infoNonTable.append(pd.DataFrame.from_dict([transactionDict]))
        if len(infoNonTable) > 0:
            data = pd.concat(infoNonTable, sort = False, ignore_index = True)
        else:
            data = pd.DataFrame()
        return(data)

    def get_derivative_table(text):
        tableDerivative = text.find_all(re.compile(r"derivativeTransaction|derivativeHolding"))
        infoTable = list()
        for transaction in tableDerivative:
            infoTransaction = get_transaction_row(transaction)
            transactionDict = dict()
            for item in infoTransaction:
                transactionDict[item[0]] = item[1]
            transactionDict["table"] = "II: Derivative Securities"
            infoTable.append(pd.DataFrame.from_dict([transactionDict]))

        if len(infoTable) > 0:
            data = pd.concat(infoTable, sort = False, ignore_index = True)
        else:
            data = pd.DataFrame()

        return(data)


    linkRequest = str(requests.get(link, headers={'User-Agent': 'Mozilla'}).content)
    #print(linkRequest[:5000])
    if '<TYPE>424B' not in linkRequest:
        text = clean_text_xml(linkRequest)
        identityData = get_identity(text)
        dataNonTable = get_non_derivative_table(text)
        dataDerivativeTable = get_derivative_table(text)
        identityData["edgar.link"] = link
        dataNonTable["edgar.link"] = link
        dataDerivativeTable["edgar.link"] = link

        data  = pd.concat([dataNonTable,dataDerivativeTable], sort = False, ignore_index = True)
        data = pd.merge(data, identityData, on = "edgar.link")

        if text.find("footnotes") is not None:
            data["footnotes"] = text.find("footnotes").text
        return(data)
    else:
        # The filing is Form 424B2, skip processing
        print(f"Excluded Form 424B2 filing at {link}")
        return None


def ticker_to_csv(ticker, dates):
    cik = ticker_to_cik(ticker)
    print(f"The CIK is: {cik}")

    links = get_links(cik, dates)
    total_links = len(links)
    print(f"Processing {total_links} filings...")

    all_data = pd.DataFrame()  # Initialize an empty DataFrame to hold all data

    for index, link in enumerate(links):
        print(f"Trying {link}...")
        data = parse_345(link)  # Assume this returns a DataFrame

        # Concatenate the current data DataFrame with the new one, aligning on columns and adding new ones as needed
        all_data = pd.concat([all_data, data], ignore_index=True, sort=False)

        percent_complete = ((index + 1) / total_links) * 100
        print(f"{index + 1} completed; percent Complete: {percent_complete:.2f}%")

    csv_filename = f"{ticker}_data.csv"
    all_data.to_csv(csv_filename, index=False)
    print(f"Data saved to {csv_filename}")



ticker = "PACB"
dates = "2014-2024"
ticker_to_csv(ticker, dates)
