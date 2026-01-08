from drugs.services.active_resolver import resolve_active_ingredients
from drugs.services.pubchem import get_smiles_from_pubchem


def resolve_smiles_for_medication(med_name: str) -> list[str]:
    """
    Resolve SMILES for a medication name:
    1) ActiveIngredients in DB
    2) PubChem fallback
    """
    smiles_list = []

    active_ingredients = resolve_active_ingredients(med_name)

    for ai in active_ingredients:
        if ai.smiles:
            smiles_list.append(ai.smiles)

    # PubChem fallback
    if not smiles_list:
        smiles = get_smiles_from_pubchem(med_name)
        if smiles:
            smiles_list.append(smiles)

    return smiles_list
