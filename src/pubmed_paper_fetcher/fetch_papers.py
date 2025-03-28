import requests
import csv
import argparse
import re
from typing import List, Dict, Optional

# PubMed API Endpoints
PUBMED_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
DETAILS_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Function to fetch research paper IDs from PubMed
def fetch_paper_ids(query: str) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": 10,
        "retmode": "json"
    }
    response = requests.get(PUBMED_API_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])

# Function to fetch research paper details
def fetch_paper_details(paper_ids: List[str]) -> List[Dict]:
    if not paper_ids:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(paper_ids),
        "retmode": "json"
    }
    response = requests.get(DETAILS_API_URL, params=params)
    response.raise_for_status()
    data = response.json()

    papers = []
    
    for paper_id in paper_ids:
        paper_data = data.get("result", {}).get(paper_id, {})
        if isinstance(paper_data, dict):  # Ensure it's a dictionary
            papers.append(paper_data)

    return papers

# Function to identify non-academic authors
def identify_non_academic_authors(authors: List[Dict]) -> List[Dict]:
    non_academic = []
    for author in authors:
        affiliation = author.get("affiliation", "")
        if affiliation and not re.search(r"university|college|institute|lab", affiliation, re.IGNORECASE):
            non_academic.append({
                "name": author.get("name"),
                "affiliation": affiliation
            })
    return non_academic

# Function to write results to CSV
def write_to_csv(results: List[Dict], filename: str):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["PubmedID", "Title", "Publication Date", "Non-academic Authors", "Company Affiliations", "Corresponding Author Email"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

# Main CLI function
def main():
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed with non-academic authors.")
    parser.add_argument("query", type=str, help="Search query for PubMed.")
    parser.add_argument("-f", "--file", type=str, help="Output CSV filename.")
    args = parser.parse_args()
    
    paper_ids = fetch_paper_ids(args.query)
    if not paper_ids:
        print("No papers found.")
        return
    
    papers = fetch_paper_details(paper_ids)
    results = []
    
    for paper in papers:
        if not isinstance(paper, dict):  # Ensure paper is a dictionary
            continue

        authors = paper.get("authors", [])
        non_academic_authors = identify_non_academic_authors(authors)
        
        results.append({
            "PubmedID": paper.get("uid"),
            "Title": paper.get("title", "N/A"),
            "Publication Date": paper.get("pubdate", "N/A"),
            "Non-academic Authors": ", ".join([a["name"] for a in non_academic_authors]) or "N/A",
            "Company Affiliations": ", ".join([a["affiliation"] for a in non_academic_authors]) or "N/A",
            "Corresponding Author Email": paper.get("corresponding_author", "N/A")
        })
    
    if args.file:
        write_to_csv(results, args.file)
        print(f"Results saved to {args.file}")
    else:
        for res in results:
            print(res)

if __name__ == "__main__":
    main()
