#This code reads the ChemSpider link from a CSV file and uses it to webscrape the SMILES value for each molecule, and adds it to a new .csv file. This code was used to prepare molecules for conversion from their SMILES form in the spreadsheet to individual .pdb files for each PFAS ligand.
import pandas as pd
import requests
from bs4 import BeautifulSoup

def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

def scrape_smiles(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            smiles_tag = soup.find('span', id="ctl00_ctl00_ContentSection_ContentPlaceHolder1_RecordViewDetails_rptDetailsView_ctl00_moreDetails_WrapControl2") #Looks for specific code where chemical properties are stored
            if smiles_tag:
                return smiles_tag.get_text(strip=True) #Looks for SMILES
            else:
                print(f"SMILES not found on page: {url}")
                return None
        else: 
            print(f"Failed to fetch URL: {url} (Status Code: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def main():
    input_file = r"C:\Users\samue\Downloads\QSARCommonlyExposedSMILESInput.csv"
    output_file = r"C:\Users\samue\Downloads\QSARCommonlyExposedSMILESOutput.csv"

    data = load_data(input_file)

    data['SMILES'] = None

    for idx, row in data.iterrows():
        url = row.get('ChemSpider Link')
        if pd.notna(url) and url.startswith("http"):
            smiles = scrape_smiles(url) #Gets scraped SMILES value
            data.at[idx, 'SMILES'] = smiles #Updates spreadsheet at specific cell under the SMILES column with the scraped value
        else:
            print(f"Invalid URL at index {idx}: {url}")

    data.to_csv(output_file, index=False)
    print(f"Scraped SMILES data saved to {output_file}")

if __name__ == "__main__":
    main()

