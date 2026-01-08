import csv
from django.conf import settings
from pathlib import Path
from django.core.management.base import BaseCommand
from drugs.models import ActiveIngredient
from tqdm import tqdm


class Command(BaseCommand):
    help = "Seed ActiveIngredient from DDI dataset (drug1/drug2 + smiles)"

    def handle(self, *args, **kwargs):
        csv_path = Path(settings.BASE_DIR) / "drugs" / "data" / "active_smiles.csv"

        self.stdout.write("📥 Reading Active Ingredients...")

        # count rows (for tqdm)
        with open(csv_path, encoding="utf-8") as f:
            total = sum(1 for _ in f) - 1

        batch = []
        BATCH_SIZE = 5000

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in tqdm(reader, total=total, desc="Seeding ActiveIngredients", ncols=100):
                pairs = [
                    (row["drug1_name"], row["smiles1"]),
                    (row["drug2_name"], row["smiles2"]),
                ]

                for name, smiles in pairs:
                    name = name.strip().lower()
                    smiles = smiles.strip()

                    if not name or not smiles:
                        continue

                    batch.append(
                        ActiveIngredient(
                            name=name,
                            smiles=smiles
                        )
                    )

                if len(batch) >= BATCH_SIZE:
                    ActiveIngredient.objects.bulk_create(
                        batch,
                        ignore_conflicts=True
                    )
                    batch.clear()

        if batch:
            ActiveIngredient.objects.bulk_create(
                batch,
                ignore_conflicts=True
            )

        self.stdout.write(self.style.SUCCESS("✅ ActiveIngredient seeded from DDI dataset"))
