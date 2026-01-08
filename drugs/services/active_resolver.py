from drugs.models import Drug, ActiveIngredient

def resolve_active_ingredients(med_name: str):
    """
    Returns list of ActiveIngredient objects
    """
    drug = Drug.objects.filter(name__iexact=med_name).first()

    if drug:
        return list(drug.active_ingredients.all())

    # fallback: maybe med_name is active itself
    ai = ActiveIngredient.objects.filter(name__iexact=med_name).first()
    return [ai] if ai else []
