from Bio import Entrez, Medline

def search_pubmed(query: str, max_results: int = 5):
    """
    Searches PubMed for a given query and returns a list of article details.
    """
    # Always tell NCBI who you are
    Entrez.email = "test@example.com"
    
    # Search PubMed and get a list of PMIDs
    handle = Entrez.esearch(db="pubmed", term=query, retmax=str(max_results))
    record = Entrez.read(handle)
    handle.close()
    id_list = record["IdList"]

    if not id_list:
        return []

    # Fetch the details for those PMIDs
    handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
    records = list(Medline.parse(handle))
    handle.close()

    articles = []
    for rec in records:
        articles.append({
            "pmid": rec.get("PMID", ""),
            "title": rec.get("TI", "No Title Found"),
            "abstract": rec.get("AB", "No Abstract Found"),
            "authors": rec.get("AU", [])
        })
    return articles
