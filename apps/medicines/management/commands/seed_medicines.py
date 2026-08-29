"""Populate the catalogue with sample medicines.

The proposal's pilot validation plan (section 6.3) calls for sample pharmacy data.
This gives the catalogue enough realistic rows to exercise search, category filtering
and pagination without hand-typing them, and makes the module demonstrable.

Usage::

    py -3.13 manage.py seed_medicines
    py -3.13 manage.py seed_medicines --flush
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.medicines.models import Medicine

U = Medicine.Unit

# (name, generic_name, strength, category, manufacturer, unit, prescription_required)
SAMPLE_MEDICINES = [
    ("Crocin Advance", "Paracetamol", "500 mg", "Analgesic", "GSK", U.TABLET, False),
    ("Dolo 650", "Paracetamol", "650 mg", "Analgesic", "Micro Labs", U.TABLET, False),
    ("Combiflam", "Ibuprofen + Paracetamol", "400 mg", "Analgesic", "Sanofi", U.TABLET, False),
    ("Brufen", "Ibuprofen", "400 mg", "Analgesic", "Abbott", U.TABLET, False),
    ("Augmentin 625", "Amoxicillin + Clavulanic acid", "625 mg", "Antibiotic", "GSK", U.TABLET, True),
    ("Azithral 500", "Azithromycin", "500 mg", "Antibiotic", "Alembic", U.TABLET, True),
    ("Ciplox 500", "Ciprofloxacin", "500 mg", "Antibiotic", "Cipla", U.TABLET, True),
    ("Monocef", "Ceftriaxone", "1 g", "Antibiotic", "Aristo", U.INJECTION, True),
    ("Pan 40", "Pantoprazole", "40 mg", "Antacid", "Alkem", U.TABLET, True),
    ("Omez", "Omeprazole", "20 mg", "Antacid", "Dr Reddy's", U.CAPSULE, False),
    ("Digene", "Antacid gel", "170 ml", "Antacid", "Abbott", U.SYRUP, False),
    ("Allegra 120", "Fexofenadine", "120 mg", "Antihistamine", "Sanofi", U.TABLET, False),
    ("Cetzine", "Cetirizine", "10 mg", "Antihistamine", "GSK", U.TABLET, False),
    ("Montair LC", "Montelukast + Levocetirizine", "10 mg", "Respiratory", "Cipla", U.TABLET, True),
    ("Asthalin", "Salbutamol", "100 mcg", "Respiratory", "Cipla", U.DROPS, True),
    ("Glycomet 500", "Metformin", "500 mg", "Antidiabetic", "USV", U.TABLET, True),
    ("Januvia", "Sitagliptin", "50 mg", "Antidiabetic", "MSD", U.TABLET, True),
    ("Telma 40", "Telmisartan", "40 mg", "Cardiovascular", "Glenmark", U.TABLET, True),
    ("Ecosprin 75", "Aspirin", "75 mg", "Cardiovascular", "USV", U.TABLET, True),
    ("Atorva 10", "Atorvastatin", "10 mg", "Cardiovascular", "Zydus", U.TABLET, True),
    ("Shelcal 500", "Calcium + Vitamin D3", "500 mg", "Supplement", "Torrent", U.TABLET, False),
    ("Zincovit", "Multivitamin + Zinc", "", "Supplement", "Apex", U.TABLET, False),
    ("Neurobion Forte", "Vitamin B complex", "", "Supplement", "Merck", U.TABLET, False),
    ("Betadine", "Povidone iodine", "5%", "Antiseptic", "Win-Medicare", U.OINTMENT, False),
    ("Soframycin", "Framycetin", "1%", "Antiseptic", "Sanofi", U.OINTMENT, False),
    ("ORS Powder", "Oral rehydration salts", "21.8 g", "Electrolyte", "FDC", U.SACHET, False),
    ("Benadryl", "Diphenhydramine", "100 ml", "Cough", "Johnson & Johnson", U.SYRUP, False),
    ("Ascoril LS", "Levosalbutamol + Ambroxol", "100 ml", "Cough", "Glenmark", U.SYRUP, True),
]


class Command(BaseCommand):
    help = "Create sample medicines for development and demos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete every existing medicine before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            deleted, _ = Medicine.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing medicine(s)."))

        created = 0
        for name, generic, strength, category, manufacturer, unit, rx in SAMPLE_MEDICINES:
            _, was_created = Medicine.objects.get_or_create(
                name=name,
                strength=strength,
                manufacturer=manufacturer,
                defaults={
                    "generic_name": generic,
                    "category": category,
                    "unit": unit,
                    "prescription_required": rx,
                },
            )
            created += was_created

        skipped = len(SAMPLE_MEDICINES) - created
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} medicine(s); {skipped} already present. "
                f"Catalogue now holds {Medicine.objects.count()}."
            )
        )
