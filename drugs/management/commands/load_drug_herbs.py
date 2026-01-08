import csv
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from drugs.models import Drug, ActiveIngredient, DrugAlternative
from drugs.utils.parsing import parse_active_ingredients


CHUNK_SIZE = 5000


class Command(BaseCommand):
    help = "FAST load drugs, active ingredients, and alternatives from drug_herbs.csv"

    def handle(self, *args, **kwargs):
        csv_path = Path(settings.BASE_DIR) / "drugs" / "data" / "drug_herbs.csv"
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)

        self.stdout.write("📥 Preloading DB caches...")

        # ---- preload caches ----
        drug_cache = {d.name: d for d in Drug.objects.all()}
        ai_cache = {a.name: a for a in ActiveIngredient.objects.all()}
        alt_cache = set(
            DrugAlternative.objects.values_list("drug__name", "substitute")
        )

        self.stdout.write(
            f"Drugs: {len(drug_cache)}, "
            f"ActiveIngredients: {len(ai_cache)}, "
            f"Alternatives: {len(alt_cache)}"
        )

        with open(csv_path, encoding="utf-8") as f:
            total = sum(1 for _ in f) - 1

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            new_drugs = []
            new_ais = []
            new_m2m = []
            new_alts = []

            for row in tqdm(reader, total=total, desc="Importing", ncols=120):
                # ---------------- Drug ----------------
                drug_name = row["Drug_Name"].strip().lower()
                if not drug_name:
                    continue

                drug = drug_cache.get(drug_name)
                if not drug:
                    drug = Drug(name=drug_name)
                    drug_cache[drug_name] = drug
                    new_drugs.append(drug)

                # ---------------- Active Ingredients ----------------
                raw_ai = row.get("Active_Ingredients") or row.get("Active_Ingredient")
                for ai_name in parse_active_ingredients(raw_ai):
                    ai = ai_cache.get(ai_name)
                    if not ai:
                        ai = ActiveIngredient(name=ai_name)
                        ai_cache[ai_name] = ai
                        new_ais.append(ai)

                    new_m2m.append((drug_name, ai_name))

                # ---------------- Drug Alternative ----------------
                sub = row.get("substitute", "").strip().lower()
                if sub:
                    key = (drug_name, sub)
                    if key not in alt_cache:
                        alt_cache.add(key)
                        alt = DrugAlternative(
                            drug_id=None,  # will be set after saving drugs
                            substitute=sub,
                            match_score=row.get("Match_Score") or None,
                            drug_class=row.get("Drug_Class") or "",
                            atc_code=row.get("ATC_Code") or "",
                            herbal_alternatives=row.get("Herbal_Alternatives") or "",
                        )
                        alt._drug_name = drug_name  # temp storage
                        new_alts.append(alt)

                # ---------------- Flush ----------------
                if len(new_drugs) >= CHUNK_SIZE:
                    self._flush(
                        new_drugs, new_ais, new_m2m, new_alts,
                        drug_cache, ai_cache
                    )
                    new_drugs.clear()
                    new_ais.clear()
                    new_m2m.clear()
                    new_alts.clear()

            # final flush
            self._flush(
                new_drugs, new_ais, new_m2m, new_alts,
                drug_cache, ai_cache
            )

        self.stdout.write(self.style.SUCCESS("✅ FAST import completed"))

    def _flush(self, drugs, ais, m2m, alts, drug_cache, ai_cache):
        with transaction.atomic():
            # ---- bulk create drugs & ingredients ----
            Drug.objects.bulk_create(drugs, ignore_conflicts=True)
            ActiveIngredient.objects.bulk_create(ais, ignore_conflicts=True)

            # ---- refresh IDs ----
            for d in Drug.objects.filter(name__in=[d.name for d in drugs]):
                drug_cache[d.name] = d
            for a in ActiveIngredient.objects.filter(name__in=[a.name for a in ais]):
                ai_cache[a.name] = a

            # ---- bulk M2M ----
            through = Drug.active_ingredients.through
            through.objects.bulk_create(
                [
                    through(
                        drug_id=drug_cache[d].id,
                        activeingredient_id=ai_cache[a].id
                    )
                    for d, a in m2m
                ],
                ignore_conflicts=True
            )

            # ---- fix FK then bulk create alternatives ----
            for alt in alts:
                alt.drug_id = drug_cache[alt._drug_name].id
                del alt._drug_name

            DrugAlternative.objects.bulk_create(
                alts, ignore_conflicts=True
            )
