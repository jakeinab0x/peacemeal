import csv
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from meals.models import FoodItem

class Command(BaseCommand):
    help = 'Import data from the nutrition dataset CSV into the FoodItem model.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=(
                Path(settings.BASE_DIR) 
                / 'meals' 
                / 'data'
                / 'cleaned_nutrition_dataset_per100g.csv'
            ),
            type=Path,
        )

    def handle(self, *args, **options):
        csv_file_path = options['file']

        if not csv_file_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        imported = 0

        with csv_file_path.open(newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                name = row['food_normalized'].strip()

                if not name:
                    self.stderr.write(self.style.WARNING("Skipping row with empty normalized food name."))
                    continue

                _, created = FoodItem.objects.get_or_create(
                    name=name,
                    defaults={
                        "carbs": Decimal(row["Carbohydrates (g per 100g)"]),
                        "sugars": Decimal(row["Sugars (g per 100g)"]),
                        "fibre": Decimal(row["Dietary Fiber (g per 100g)"]),
                        "fat": Decimal(row["Fat (g per 100g)"]),
                        "protein": Decimal(row["Protein (g per 100g)"]),
                        "calcium": Decimal(row["Calcium (mg per 100g)"]),
                        "iron": Decimal(row["Iron (mg per 100g)"]),
                        "sodium": Decimal(row["Sodium (mg per 100g)"]),
                        "vitamin_c": Decimal(row["Vitamin C (mg per 100g)"]),
                        "vitamin_b11": Decimal(row["Vitamin B11 (mg per 100g)"]),
                        "kilocalories": Decimal(row["Calories (kcal per 100g)"]),
                    },
                )

                if created:
                    imported += 1
                    
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {imported} food items from {csv_file_path}"
            )
        )