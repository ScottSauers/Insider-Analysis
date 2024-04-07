import requests
from bs4 import BeautifulSoup
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import re
import numpy as np
import json
import os
import time


def encode(ticker, dates):
    if not os.path.exists('insider_data'):
        os.makedirs('insider_data')

    if not os.path.exists("sec_form_4"):
        os.makedirs("sec_form_4", exist_ok=True)


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
                #print(item)
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
        if '<TYPE>424B' in linkRequest:
            # The filing is Form 424B, skip processing
            print(f"Excluded Form 424B filing at {link}")
            return None
        elif '<TYPE>425' in linkRequest:
            # The filing is Form 425, skip processing
            print(f"Excluded Form 425 filing at {link}")
            return None
        else:
            text = clean_text_xml(linkRequest)
            #print(text)
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
                #print(link)
            #print(data)

            filename = os.path.join("sec_form_4", link.replace("https://", "").replace("/", "_").replace(".", "_").rsplit(".", 1)[0] + ".csv")

            # Save the 'data' DataFrame to a CSV file using the generated filename.
            data.to_csv(filename, index=False)

            print(f"Data saved to CSV file: {filename}")
            return(data)



    def csv_filter(input_csv_path, output_csv_path):
        # Load the CSV file into a pandas DataFrame
        try:
            df = pd.read_csv(input_csv_path)
            if df.empty:
                print("The input CSV file is empty. No processing needed.")
                return
        except pd.errors.EmptyDataError:
            print("No columns to parse.")
            return
        except FileNotFoundError:
            print(f"The file {input_csv_path} does not exist.")
            return

        df['0_gift_comp_vesting_1_other'] = df.apply(
            lambda row: 0 if row['transactionCode'] in ['A', 'D', 'G', 'W']
            or ('footnotes' in df.columns and any(keyword in str(row.get('footnotes', '')).lower()
                for keyword in ["vesting", "vest ", "vest.", "vest,", "401(k)", "401k"]))
            else 1,
            axis=1
        )



        # FirmName encoding based on modal value
        if not df.empty and 'firmName' in df.columns:
            if df['firmName'].nunique() == 1:
                modal_firm_name = df['firmName'].mode()[0]
                df['firmName'] = df['firmName'].apply(lambda x: 1 if x == modal_firm_name else 2)
        else:
            if 'firmName' not in df.columns:
                print(f"firmName not in columms: {df.columns}")
            else:
                print(f"The DataFrame is empty. Full DataFrame structure:\n{df}")


        # Define the rules for 'securityTitle'
        df['securityTitle'] = df['securityTitle'].map(lambda x: 1 if 'Common Stock' in x
                                                    else 2 if 'Restricted Stock' in x
                                                    else 3 if 'option' in x
                                                    else 4)

        # TransactionAcquiredDisposedCode encoding
        df['transactionAcquiredDisposedCode'] = df['transactionAcquiredDisposedCode'].map({'D': 1, 'A': 2}).fillna(3)


        df['sharesOwnedPrecedingTransaction'] = df.apply(
            lambda row: row['sharesOwnedFollowingTransaction'] + row['transactionShares']
            if row['transactionAcquiredDisposedCode'] == 1
            else row['sharesOwnedFollowingTransaction'] - row['transactionShares'],
            axis=1
        )

        # Calculate the change in ownership
        df['changeInOwnership'] = (df['sharesOwnedFollowingTransaction'] - df['sharesOwnedPrecedingTransaction']) / df['sharesOwnedFollowingTransaction']

        # Fill infinite values (if any) due to division by zero with NaN, then replace NaN with -1
        df['changeInOwnership'] = df['changeInOwnership'].replace([np.inf, -np.inf], np.nan)
        df['changeInOwnership'] = df['changeInOwnership'].fillna(0)
        df['sharesOwnedPrecedingTransaction'] = df['sharesOwnedPrecedingTransaction'].fillna(-1)
        df['transactionShares'] = df['transactionShares'].fillna(-1)

        #print("Change in Ownership:", df['changeInOwnership'].to_string(), "Shares Owned Following Transaction:", df['sharesOwnedFollowingTransaction'].to_string(), "Shares Owned Preceding Transaction:", df['sharesOwnedPrecedingTransaction'].to_string())




        # Create a new column for adjusted transactionShares based on transactionAcquiredDisposedCode
        df['adjusted_transactionShares'] = df.apply(
            lambda row: row['transactionShares'] if row['transactionAcquiredDisposedCode'] == 2 else -row['transactionShares'],
            axis=1
        )


        # TransactionPricePerShare adjustments
        df['transactionPricePerShare'] = df['transactionPricePerShare'].replace({0: -1, '': -1}).fillna(-1)

        #df.apply(lambda row: print(row['transactionPricePerShare']), axis=1)

        # Now calculate total_dollar_amount considering conditions for -1 and NaN/None in transactionPricePerShare or transactionShares
        df['total_dollar_amount'] = df.apply(
            lambda row: -1 if (row['transactionPricePerShare'] == -1 or
                            row['transactionShares'] == -1 or
                            pd.isnull(row['transactionPricePerShare']) or
                            pd.isnull(row['transactionShares']) or
                            pd.isna(row['transactionPricePerShare']) or
                            pd.isna(row['transactionShares']))
                        else row['adjusted_transactionShares'] * row['transactionPricePerShare'],
            axis=1
        )




        # Delete specified columns
        df.drop(columns=['transactionFormType', 'equitySwapInvolved', 'edgar.link',
                        'firmCIK', 'firmTicker', 'isOther', 'otherText', 'documentType',
                        'notSubjectToSection16', 'footnotes', 'natureOfOwnership',
                        'executiveName', 'ownerAddress1', 'ownerAddress2', 'ownerCity',
                        'ownerState', 'ownerZipCode', 'conversionOrExercisePrice',
                        'exerciseDate', 'expirationDate', 'underlyingSecurityTitle',
                        'underlyingSecurityShares', 'transactionCode', 'table',
                        'sharesOwnedFollowingTransaction', 'adjusted_transactionShares'], inplace=True, errors='ignore')

        # TransactionCode encoding
        #df['transactionCode'] = df['transactionCode'].map({'P': 1, 'S': 2, 'A': 3}).fillna(4)

        df.drop(columns=['directOrIndirectOwnership'], inplace=True, errors='ignore')


        # Table encoding
        #df['table'] = df['table'].map(lambda x: 1 if 'Non-Derivative Securities' in x
        #                            else 2 if 'Derivative Securities' in x
        #                            else print(f"Warning: 'table' contains unexpected value {x}"))

        # ExecutiveCIK encoding
        executive_cik_counts = df['executiveCIK'].value_counts()
        executive_cik_mapping = {cik: i+1 for i, cik in enumerate(executive_cik_counts.index) if executive_cik_counts[cik] >= 4}
        df['executiveCIK'] = df['executiveCIK'].map(executive_cik_mapping).fillna(0)


        def convert_bool_columns(df, column_names):
            for column in column_names:
                if column in df.columns:
                    # First, handle numeric values directly to avoid conversion to string and back
                    df[column] = df[column].apply(lambda x: 1 if str(x).strip().upper() in ['1', 'TRUE'] else 0 if str(x).strip().upper() in ['0', 'FALSE', '2'] else x)
                    df[column] = pd.to_numeric(df[column], errors='coerce').fillna(0)
        bool_columns = ['isDirector', 'isOfficer', 'isTenPercentOwner']

        convert_bool_columns(df, bool_columns)

        def encode_officer_title(title): #elif is better than mapping
            if pd.isnull(title):
                return 8
            title_lower = title.lower()
            if 'cfo' in title_lower or 'chief financial officer' in title_lower:
                return 1
            elif 'ceo' in title_lower or 'chief executive officer' in title_lower:
                return 2
            elif 'vice president' in title_lower or 'vp' in title_lower:
                return 4
            elif 'president' in title_lower or 'COB' in title_lower:  # This comes after checking for VP to avoid mismatch
                return 3
            elif any(word in title_lower for word in ['cmo', 'medical', 'therapeutics', 'science', 'chief scientific officer']):
                return 5
            elif any(word in title_lower for word in ['chief operating officer', 'coo', 'chief strategy officer']):
                return 6
            elif 'business' in title_lower or 'administrative' in title_lower or 'marketing' in title_lower or 'commercial' in title_lower:
                return 7
            else:
                return 8


        if 'officerTitle' not in df.columns:
            df['officerTitle'] = 'N/A'


        # Apply the function to 'officerTitle'
        df['officerTitle'] = df['officerTitle'].apply(encode_officer_title)


        if 'documentType' in df.columns:
            df = df[df['documentType'].isin(['4', 'four'])]
            df.drop(columns=['documentType'], inplace=True)
        else:
            print("Warning: 'documentType' column not found, so not double checking form type.")

        # Other columns warning and deletion
        expected_columns = {'securityTitle', 'transactionDate', 'transactionCode',
                            'transactionShares', 'transactionPricePerShare',
                            'transactionAcquiredDisposedCode', 'sharesOwnedPrecedingTransaction',
                            'firmName', 'executiveCIK', 'isDirector', 'isOfficer',
                            'isTenPercentOwner', 'officerTitle', 'periodOfReport',
                            'dateOfOriginalSubmission', '0_gift_comp_vesting_1_other',
                            'changeInOwnership', 'total_dollar_amount'}
        for column in df.columns:
            if column not in expected_columns:
                print(f"Warning: Deleting unexpected column {column}")
                df.drop(columns=[column], inplace=True)

        df = df.rename(columns={
            'securityTitle': 'securityTitle_1_common_2_restricted_3_options',
            'transactionAcquiredDisposedCode': 'transaction_1_Disposed_2_Acquired',
            #'table': '1_Non_2_Derivative',
            'executiveCIK': 'person_ID',
            'isDirector': '1_isDirector',
            'isOfficer': '1_isOfficer',
            'isTenPercentOwner': '1_isTenPercentOwner',
            'officerTitle': 'officerTitle_low_is_important'
        })

        # Write the modified DataFrame to a new CSV file
        df.to_csv(output_csv_path, index=False)
        print("CSV filtering and encoding completed successfully.")

    def ticker_to_encoded_csv(ticker, dates):
        cik = ticker_to_cik(ticker)
        print(f"The CIK is: {cik}")

        links = get_links(cik, dates)
        total_links = len(links)
        print(f"Processing {total_links} filings...")

        all_data = pd.DataFrame()  # Initialize an empty DataFrame to hold all data

        for index, link in enumerate(links):
            i = 0
            while True:
                try:
                    print(f"Trying {link}...")
                    filename = os.path.join("sec_form_4", link.replace("https://", "").replace("/", "_").replace(".", "_").rsplit(".", 1)[0] + ".csv")

                    if os.path.exists(filename):
                        data = pd.read_csv(filename)
                        print(f"Loaded {link} from existing file.")
                    else:
                        data = parse_345(link)

                    # Concatenate the current data DataFrame with the new one, aligning on columns and adding new ones as needed
                    all_data = pd.concat([all_data, data], ignore_index=True, sort=False)

                    percent_complete = ((index + 1) / total_links) * 100
                    print(f"{index + 1} completed; percent Complete: {percent_complete:.2f}%")

                    break
                except:
                    i += 5
                    print(f"Failed to get sec data from {link}. Is it in XML format?")
                    print(f"Waiting {i} seconds before retrying...")
                    time.sleep(i*0.0001)
                    if i > 0:
                        break

        csv_filename = f"insider_data/{ticker}_data.csv"
        all_data.to_csv(csv_filename, index=False)
        print(f"Raw data saved to insider_data/{csv_filename}")

        input_csv_path = csv_filename
        output_csv_path = f"insider_data/{ticker}_encoded_data.csv"
        csv_filter(input_csv_path, output_csv_path)
        print(f"Encoded data saved to {output_csv_path}")

    #ticker = "CRSP"
    #dates = "2014-2024"
    ticker_to_encoded_csv(ticker, dates)