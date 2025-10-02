#This code takes the top 1000 Dockers and outputs only the ones with links on ChemSpider in a new spreadsheet. This was used to generate datasets for both top PFAS binder models.
import requests
from bs4 import BeautifulSoup
import pandas as pd

def search_chemspider_link(cas_number):
    search_url = f"https://legacy.chemspider.com/Search.aspx?q={cas_number}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200: #Check if server response is successful (=200)
        soup = BeautifulSoup(response.text, 'html.parser')
        result_message = soup.find('h3', id="ctl00_ctl00_ContentSection_ContentPlaceHolder1_ResultStatementControl1_plhCountMessage")
        if result_message and "Found 1 result" in result_message.text: #Checks if the result message indicates exactly one result found
            return response.url
        else:
            print(f"No single result found for {cas_number}, or the result message was not found.")
    return None

def process_chemicals(input_file, output_file):
    df = pd.read_excel(input_file)
    new_data = []

    for index, row in df.iterrows():
        chemspider_link = search_chemspider_link(row['CASRN'])
        if chemspider_link: #Checks if a valid ChemSpider link is found and adds it to the new spreadsheet
            new_row = {
                'CASRN': row['CASRN'],
                'Name': row['Name'],
                'SMILES': row['SMILES'],
                'Docking Score':row['Docking Score'],
                'ChemSpider Link': chemspider_link
            }
            new_data.append(new_row)
            print(f"Added {row['CASRN']} with link: {chemspider_link}")
        else:
            print(f"ChemSpider link not found for {row['CASRN']}.")

    if new_data:
        results_df = pd.DataFrame(new_data)
        results_df.to_excel(output_file, index=False)
        print(f"Data saved to {output_file}")
    else:
        print("No valid ChemSpider links found for any chemicals; no file saved.")

process_chemicals(r'C:\Users\samue\Downloads\PFASDatabaseTop1000Binders.xlsx', "PFASWithChemSpiderLinks.xlsx")