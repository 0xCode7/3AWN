import requests

PUBCHEM_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
    "compound/name/{name}/property/CanonicalSMILES,ConnectivitySMILES/JSON"
)


def get_smiles_from_pubchem(drug_name: str) -> str | None:
    try:
        url = PUBCHEM_URL.format(name=drug_name)
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return None

        data = response.json()
        props = data["PropertyTable"]["Properties"][0]

        # Prefer Canonical, fallback to Connectivity
        return props.get("CanonicalSMILES") or props.get("ConnectivitySMILES")

    except (KeyError, IndexError, ValueError):
        return None
