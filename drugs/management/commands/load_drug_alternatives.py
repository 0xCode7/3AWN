# drugs/management/commands/load_drug_alternatives.py
import pandas as pd
import os
from django.core.management.base import BaseCommand
from drugs.models import Drug, DrugAlternative


class Command(BaseCommand):
    help = "Load drug alternatives and herbal alternatives from CSV"

    def handle(self, *args, **kwargs):
        # absolute path based on project root
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'drug_herbs.csv')
        df = pd.read_csv(csv_path)


        for _, row in df.iterrows():
            drug_name = row["Drug_Name"].strip()
            substitute = row["substitute"].strip()
            active_ingredient = row["Active_Ingredient"].strip()
            atc_code = row.get("ATC_Code", "")
            match_score = row.get("Match_Score", None)
            drug_class = row.get("Drug_Class", "")
            herbs = row.get("Herbal_Alternatives", "")

            drug, _ = Drug.objects.get_or_create(
                name=drug_name,
                defaults={"active_ingredient": active_ingredient}
            )

            herbs_list = [h.strip() for h in herbs.split(",")] if pd.notna(herbs) else []

            DrugAlternative.objects.update_or_create(
                drug=drug,
                substitute=substitute,
                defaults={
                    "match_score": match_score,
                    "drug_class": drug_class,
                    "atc_code": atc_code,
                    "herbal_alternatives": ",".join(herbs_list)
                }
            )

        self.stdout.write(self.style.SUCCESS("Drug alternatives loaded successfully!"))
