from django.core.management.base import BaseCommand
from drugs.models import Drug


class Command(BaseCommand):
    help = "Seed the Drug table with a larger set of sample brand drugs for each active ingredient (IN)"

    def handle(self, *args, **kwargs):
        sample_drugs = {
            "Paracetamol": [
                "Panadol", "Calpol", "Doliprane", "Crocin", "Tylenol",
                "Tempra", "Acetaminophen Generic", "Medinol"
            ],
            "Ibuprofen": [
                "Advil", "Brufen", "Nurofen", "Motrin", "Midol",
                "Genpril", "Ibuprin", "Nuprin"
            ],
            "Amoxicillin": [
                "Amoxil", "Moxatag", "Trimox", "Larotid", "Amoxicot"
            ],
            "Aspirin": [
                "Disprin", "Bayer", "Aspro", "Bufferin", "Ecotrin",
                "Anacin", "Zorprin"
            ],
            "Omeprazole": [
                "Losec", "Prilosec", "Zegerid", "Ocid", "Omez"
            ],
            "Metformin": [
                "Glucophage", "Fortamet", "Glumetza", "Riomet", "Obimet"
            ],
            "Atorvastatin": [
                "Lipitor", "Torvast", "Atorlip", "Sortis", "Tahor"
            ],
            "Losartan": [
                "Cozaar", "Losar", "Repace", "Arzaar", "Hyzaar"
            ],
            "Levothyroxine": [
                "Eltroxin", "Synthroid", "Euthyrox", "Eltroxin", "Levoxyl"
            ],
            "Loratadine": [
                "Claritine", "Alavert", "Clarityne", "Loridin", "Allerclear"
            ],
            "Simvastatin": [
                "Zocor", "Simlup", "Simcard", "Simvacor"
            ],
            "Clopidogrel": [
                "Plavix", "Clopilet", "Clavix", "Deplat"
            ],
            "Ciprofloxacin": [
                "Cipro", "Ciplox", "Cetraxal", "Proquin XR"
            ],
            "Azithromycin": [
                "Zithromax", "Azithral", "Azicip", "Sumamed"
            ],
            "Cetirizine": [
                "Zyrtec", "Cetzine", "Reactine", "Alleroff"
            ],
            "Furosemide": [
                "Lasix", "Frumil", "Diural", "Frusenex"
            ],
            "Salbutamol": [
                "Ventolin", "ProAir", "Proventil", "Asthalin"
            ],
            "Prednisone": [
                "Deltasone", "Meticorten", "Sterapred", "Prednicot"
            ],
            "Hydrochlorothiazide": [
                "Microzide", "Hydrodiuril", "HCTZ", "Oretic"
            ],
            "Warfarin": [
                "Coumadin", "Jantoven", "Marevan", "Warfilone"
            ]
        }

        created, skipped = 0, 0

        for ingredient, brands in sample_drugs.items():
            for brand in brands:
                obj, created_flag = Drug.objects.get_or_create(
                    name=brand,
                    defaults={"active_ingredient": ingredient}
                )
                if created_flag:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete ✅: {created} drugs created, {skipped} skipped."
        ))
