#This code creates a new spreadsheet with ChemSpider links for each chemical using each chemical's CASRN. This was used to prepare each spreadsheet for web-scraping.
import requests
from bs4 import BeautifulSoup
import pandas as pd

def search_chemspider_link(cas_number):
    search_url = f"https://legacy.chemspider.com/Search.aspx?q={cas_number}"
    headers = {'User-Agent': 'Mozilla/5.0'} #Only uses Mozilla
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        result_message = soup.find('h3', id="ctl00_ctl00_ContentSection_ContentPlaceHolder1_ResultStatementControl1_plhCountMessage")

        if result_message and "Found 1 result" in result_message.text: #Returns the chemical's link if it exists for the chemical's CASRN
            return response.url
        else:
            print(f"No single result found for {cas_number}, or the result message was not found.")
    return None

def process_chemicals(input_file, output_file):
    data = pd.read_csv(input_file)

    if 'ChemSpyder Link' not in data.columns:
        data['ChemSpyder Link'] = None

    for index, row in data.iterrows(): #Puts each link in spreadsheet
        cas_number = row['CASRN']
        if pd.notna(cas_number):
            chemspider_link = search_chemspider_link(cas_number)
            if chemspider_link:
                data.at[index, 'ChemSpyder Link'] = chemspider_link
                print(f"Added {cas_number} with link: {chemspider_link}")
            else:
                print(f"ChemSpider link not found for {cas_number}.")

    data.to_csv(output_file, index=False)
    print(f"Processed data saved to {output_file}")

input_file_path = r"C:\Users\samue\Downloads\CommonlyExposedPFASLinks.csv"
output_file_path = r"C:\Users\samue\Downloads\CommonlyExposedPFASFinal.csv"

process_chemicals(input_file_path, output_file_path)

