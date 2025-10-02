#This code takes an spreadsheet input file with ChemSpider links for each chemical, and  webscrapes each chemical's page to generate an output file with chemical descriptors for each chemical.
#This code was specifically used to generate the spreadsheet for the commonly exposed PFAS.
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import csv

def extract_first_number(value): #Function to extract first number from a string 
    match = re.search(r"[-+]?\d*\.\d+|\d+", value)
    return match.group(0) if match else ''

def scrape_properties(url):
    headers = { #This specifies the User-Agent part of the HTTP request
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'
    }
    try: #This process locates the numbers within the database
        response = requests.get(url, headers=headers) 
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            properties = {}
            rows = soup.find_all('tr')
            for row in rows:
                title_tag = row.find('td', class_='prop_title')
                value_tag = row.find('td', class_='prop_value_nowrap') or row.find('td', class_='prop_value')
                if title_tag and value_tag:
                    title = title_tag.get_text(strip=True)
                    value = value_tag.get_text(strip=True)
                    cleaned_value = extract_first_number(value)
                    properties[title] = cleaned_value
            return properties
        else:
            print(f"Failed to fetch: {url}, Status Code: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching URL: {url}, {e}")
        return {}

def main():
    input_file = r"C:\Users\samue\Downloads\CommonlyExposedPFASInput.csv" #Same ligands for estrogen receptor alpha and beta for this model
    output_file = r"C:\Users\samue\Downloads\CommonlyExposedPFASOutput.csv"

    data = pd.read_csv(input_file)

    print("Columns in input file:", data.columns)

    expected_columns = ['ChemSpider Link', 'CASRN', 'TRI Chemical Name', 'Alpha Docking Score ', 'Beta Docking Score '] #Checks for and requires these columns
    missing_columns = [col for col in expected_columns if col not in data.columns]

    if missing_columns: #For debugging
        print(f"Missing columns: {missing_columns}")
        raise KeyError(f"The following columns are missing in the input file: {missing_columns}")

    data = data.dropna(subset=['ChemSpider Link'])
    urls = data['ChemSpider Link'].tolist()

    all_properties = {}
    all_titles = set()

    for url in urls:
        properties = scrape_properties(url)
        all_properties[url] = properties
        all_titles.update(properties.keys())

    all_titles = sorted(all_titles)

    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        header = expected_columns + list(all_titles)
        writer.writerow(header)

        for idx, row in data.iterrows():
            url = row['ChemSpider Link']
            props = all_properties.get(url, {})
            data_row = [row.get(col, '') for col in expected_columns] + \
                       [props.get(title, '') for title in all_titles]
            writer.writerow(data_row)

    print(f"All done, file saved at: {output_file}")
    return output_file

output_file_path = main()
print(f"Output file saved at: {output_file_path}")