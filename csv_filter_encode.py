import pandas as pd

def csv_filter(input_csv_path, output_csv_path):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(input_csv_path)

    # Define the rules for 'securityTitle'
    df['securityTitle'] = df['securityTitle'].map(lambda x: 1 if 'Common Stock' in x
                                                   else 2 if 'Restricted Stock' in x
                                                   else 3 if 'option' in x
                                                   else 4)

    # Delete specified columns
    df.drop(columns=['transactionFormType', 'equitySwapInvolved', 'edgar.link',
                     'firmCIK', 'firmTicker', 'isOther', 'otherText', 'documentType',
                     'notSubjectToSection16', 'footnotes', 'natureOfOwnership',
                     'executiveName', 'ownerAddress1', 'ownerAddress2', 'ownerCity',
                     'ownerState', 'ownerZipCode', 'conversionOrExercisePrice',
                     'exerciseDate', 'expirationDate', 'underlyingSecurityTitle',
                     'underlyingSecurityShares'], inplace=True, errors='ignore')

    # TransactionCode encoding
    df['transactionCode'] = df['transactionCode'].map({'P': 1, 'S': 2, 'A': 3}).fillna(4)

    # TransactionPricePerShare adjustments
    df['transactionPricePerShare'] = df['transactionPricePerShare'].replace({0: -1, '': -1})

    # TransactionAcquiredDisposedCode encoding
    df['transactionAcquiredDisposedCode'] = df['transactionAcquiredDisposedCode'].map({'D': 1, 'A': 2}).fillna(3)

    # DirectOrIndirectOwnership filtering and column deletion
    df = df[df['directOrIndirectOwnership'] == 'D']
    df.drop(columns=['directOrIndirectOwnership'], inplace=True)

    # Table encoding
    df['table'] = df['table'].map(lambda x: 1 if 'Non-Derivative Securities' in x
                                  else 2 if 'Derivative Securities' in x
                                  else print(f"Warning: 'table' contains unexpected value {x}"))

    # FirmName encoding based on modal value
    modal_firm_name = df['firmName'].mode()[0]
    df['firmName'] = df['firmName'].apply(lambda x: 1 if x == modal_firm_name else 2)

    # ExecutiveCIK encoding
    executive_cik_counts = df['executiveCIK'].value_counts()
    executive_cik_mapping = {cik: i+1 for i, cik in enumerate(executive_cik_counts.index) if executive_cik_counts[cik] >= 4}
    df['executiveCIK'] = df['executiveCIK'].map(executive_cik_mapping).fillna(0)

    def convert_bool_columns(df, column_names):
        for column in column_names:
            # Ensure the column exists to avoid KeyError
            if column in df.columns:
                # Convert booleans to integers directly
                df[column] = df[column].astype(str).str.upper().map({'TRUE': 1, 'FALSE': 0}).fillna(df[column])

    # List of columns to convert
    bool_columns = ['isDirector', 'isOfficer', 'isTenPercentOwner']

    # Apply the conversion
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
        elif 'president' in title_lower:  # This comes after checking for VP to avoid mismatch
            return 3
        elif any(word in title_lower for word in ['cmo', 'medical', 'therapeutics', 'science', 'chief scientific officer']):
            return 5
        elif any(word in title_lower for word in ['chief operating officer', 'coo', 'chief strategy officer']):
            return 6
        elif 'business' in title_lower or 'administrative' in title_lower or 'marketing' in title_lower or 'commercial' in title_lower:
            return 7
        else:
            return 8

    # Apply the revised function to 'officerTitle'
    df['officerTitle'] = df['officerTitle'].apply(encode_officer_title)

    if 'documentType' in df.columns:
        df = df[df['documentType'].isin(['4', 'four'])]
        df.drop(columns=['documentType'], inplace=True)
    else:
        print("Warning: 'documentType' column not found, so not double checking form type.")

    # Other columns warning and deletion
    expected_columns = {'securityTitle', 'transactionDate', 'transactionCode',
                        'transactionShares', 'transactionPricePerShare',
                        'transactionAcquiredDisposedCode', 'sharesOwnedFollowingTransaction',
                        'table', 'firmName', 'executiveCIK', 'isDirector', 'isOfficer',
                        'isTenPercentOwner', 'officerTitle', 'periodOfReport',
                        'dateOfOriginalSubmission'}
    for column in df.columns:
        if column not in expected_columns:
            print(f"Warning: Deleting unexpected column {column}")
            df.drop(columns=[column], inplace=True)

    # Write the modified DataFrame to a new CSV file
    df.to_csv(output_csv_path, index=False)
    print("CSV filtering and encoding completed successfully.")




csv_filter("BLUE_data.csv", "BLUE_data_filtered.csv")
