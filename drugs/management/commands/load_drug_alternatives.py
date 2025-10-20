import os
import pandas as pd
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db import connection
from drugs.models import Drug, DrugAlternative

CHUNK_SIZE = 50000  # number of rows per chunk

class Command(BaseCommand):
    help = "Fast load drugs and alternatives from CSV using COPY with progress"

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "drug_herbs.csv"
        )
        self.stdout.write(f"Loading CSV in chunks: {csv_path}\n")

        total_rows = sum(1 for _ in open(csv_path)) - 1  # minus header
        self.stdout.write(f"Total rows in CSV: {total_rows}\n")

        # Step 1: Insert Drugs
        self.stdout.write("Inserting Drugs...")
        df_iter = pd.read_csv(csv_path, chunksize=CHUNK_SIZE)
        drug_names_seen = set()
        total_inserted_drugs = 0

        for chunk in tqdm(df_iter, total=(total_rows // CHUNK_SIZE + 1), ncols=120, colour="green", desc="Drugs"):
            chunk["Drug_Name"] = chunk["Drug_Name"].astype(str).str.strip()
            new_drugs = [name for name in chunk["Drug_Name"].unique() if name not in drug_names_seen]
            drug_names_seen.update(new_drugs)

            if new_drugs:
                with connection.cursor() as cursor:
                    values_str = ",".join(cursor.mogrify("(%s, %s)", (name, "")).decode("utf-8") for name in new_drugs)
                    cursor.execute(f"INSERT INTO drugs_drug (name, active_ingredient) VALUES {values_str} ON CONFLICT (name) DO NOTHING")
                total_inserted_drugs += len(new_drugs)

        self.stdout.write(f"Inserted {total_inserted_drugs} drugs.\n")

        # Step 2: Build drug cache
        drug_cache = {d.name: d.id for d in Drug.objects.all()}

        # Step 3: Insert DrugAlternatives
        self.stdout.write("Inserting DrugAlternatives...")
        df_iter = pd.read_csv(csv_path, chunksize=CHUNK_SIZE)
        total_alternatives = 0

        for chunk in tqdm(df_iter, total=(total_rows // CHUNK_SIZE + 1), ncols=120, colour="magenta", desc="Alternatives"):
            alternatives_data = []
            for _, row in chunk.iterrows():
                drug_id = drug_cache.get(str(row["Drug_Name"]).strip())
                if not drug_id:
                    continue

                herbs = str(row.get("Herbal_Alternatives", "")).strip()
                herbs_list = ",".join([h.strip() for h in herbs.split(",")]) if herbs else ""

                alternatives_data.append((
                    drug_id,
                    str(row["substitute"]).strip(),
                    row.get("Match_Score") if row.get("Match_Score") != "" else None,
                    str(row.get("Drug_Class", "")).strip(),
                    str(row.get("ATC_Code", "")).strip(),
                    herbs_list
                ))

            if alternatives_data:
                with connection.cursor() as cursor:
                    values_str = ",".join(
                        cursor.mogrify(
                            "(%s, %s, %s, %s, %s, %s)",
                            (drug_id, substitute, match_score, drug_class, atc_code, herbs_list)
                        ).decode("utf-8")
                        for drug_id, substitute, match_score, drug_class, atc_code, herbs_list in alternatives_data
                    )
                    cursor.execute(
                        f"INSERT INTO drugs_drugalternative "
                        f"(drug_id, substitute, match_score, drug_class, atc_code, herbal_alternatives) "
                        f"VALUES {values_str} ON CONFLICT DO NOTHING"
                    )
                total_alternatives += len(alternatives_data)

        self.stdout.write(f"Inserted {total_alternatives} DrugAlternatives.\n")

        # Step 4: Update active ingredients
        self.stdout.write("Updating active ingredients...")
        df_iter = pd.read_csv(csv_path, chunksize=CHUNK_SIZE)
        for chunk in tqdm(df_iter, total=(total_rows // CHUNK_SIZE + 1), ncols=120, colour="cyan", desc="Active Ingredients"):
            for _, row in chunk.iterrows():
                drug_id = drug_cache.get(str(row["Drug_Name"]).strip())
                active_ingredient = str(row.get("Active_Ingredient") or row.get("Active_Ingredients") or "").strip()
                if drug_id and active_ingredient:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE drugs_drug SET active_ingredient = %s WHERE id = %s",
                            [active_ingredient, drug_id]
                        )

        self.stdout.write(self.style.SUCCESS("✅ All drugs and alternatives loaded successfully!"))
