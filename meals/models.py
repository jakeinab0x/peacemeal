from django.conf import settings
from django.db import models
from decimal import Decimal

# source: https://www.omnicalculator.com/conversion/grams-in-ml-converter
GRAMS_TO_ML = {
    'Milk': 0.9709,
    'Honey': 0.7042,
    'Olive Oil': 1.0893,
    'Sunflower Oil': 1.0417,
    'Vegetable Oil': 1.1236,
}

NUTRIENT_FIELDS = (
    'carbs', 'sugars', 'fibre', 'fat', 'protein',
    'calcium', 'iron', 'sodium', 'vitamin_c',
    'vitamin_b11', 'kilocalories'
)

class FoodItem(models.Model):
    '''
    A food item containing nutritional information that can be used as an `Ingredient` in a `Meal`.<br>
    Fields are structured to contain data from a Food Nutrition Database .csv file or JSON dump from the Kaggle API.<br>
    Each nutrional field represents the amount of that nutrient per 100g of the food item.
    '''
    name = models.CharField(max_length=100)
    carbs = models.DecimalField(max_digits=6, decimal_places=3) #dp needs changing if converting mg >> g
    sugars = models.DecimalField(max_digits=6, decimal_places=3)
    fibre = models.DecimalField(max_digits=6, decimal_places=3)
    fat = models.DecimalField(max_digits=6, decimal_places=3)
    protein = models.DecimalField(max_digits=6, decimal_places=3)
    calcium = models.DecimalField(max_digits=6, decimal_places=3)
    iron = models.DecimalField(max_digits=6, decimal_places=3)
    sodium = models.DecimalField(max_digits=6, decimal_places=3)
    vitamin_c = models.DecimalField(max_digits=6, decimal_places=3)
    vitamin_b11 = models.DecimalField(max_digits=6, decimal_places=3)
    kilocalories = models.DecimalField(max_digits=6, decimal_places=3)
    portion_size_g = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('100.0'))
    measurement_unit = models.CharField(max_length=20) # grams, ml, etc.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'carbs': float(self.carbs),
            'sugars': float(self.sugars),
            'fibre': float(self.fibre),
            'fat': float(self.fat),
            'protein': float(self.protein),
            'calcium': float(self.calcium),
            'iron': float(self.iron),
            'sodium': float(self.sodium),
            'vitamin_c': float(self.vitamin_c),
            'vitamin_b11': float(self.vitamin_b11),
            'kilocalories': float(self.kilocalories),
            'portion_size_g': float(self.portion_size_g),
            'measurement_unit': self.measurement_unit
        }

class Meal(models.Model):
    '''
    A meal that can be cooked via a `CookingEvent`. A `Meal` is a single adult portion:<br>
    - Each `Meal` can have many `Ingredient`s<br>
    - Each `Ingredient` can be used in many `Meal`s.
    '''
    name = models.CharField(max_length=100)
    description = models.TextField()
    food_items = models.ManyToManyField(FoodItem, through='Ingredient', related_name='meals')
    recipe = models.TextField()
    category = models.CharField(max_length=50, choices=[('Breakfast', 'Breakfast'), 
                                                        ('Lunch', 'Lunch'), 
                                                        ('Dinner', 'Dinner'),
                                                        ('Snack', 'Snack'), 
                                                        ('Dessert', 'Dessert')
                                                        ])
    cuisine_type = models.CharField(max_length=50) # Italian, Chinese, Indian, etc.
    total_portions = models.PositiveIntegerField() # One meal should just be one portion

    # implement later
    # image = models.ImageField(upload_to='meal_images/', blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meals_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def total_cost_gbp(self):
        return sum((ingredient.cost_gbp for ingredient in self.ingredients.all()), Decimal('0.00'))

    @property
    def nutrients(self):
        totals = {field: Decimal('0') for field in NUTRIENT_FIELDS}

        for ingredient in self.ingredients.all():
            nutrients = ingredient.nutrients
            for field, value in nutrients.items():
                totals[field] += value

        return totals

class MealPriceRecord(models.Model):
    '''
    A record of the price of a `Meal`.
    '''
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='price_records')
    cost_gbp = models.DecimalField(max_digits=6, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Price record for {self.meal.name}: £{self.cost_gbp}'
    

class CookingEvent(models.Model):
    '''
    A record of a user cooking a `Meal` at a specific time.
    '''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='cooking_events')
    meal_time = models.CharField(max_length=50, choices=[('Breakfast', 'Breakfast'), ('Lunch', 'Lunch'), ('Dinner', 'Dinner')])

    cooked_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} cooked {self.meal.name} for {self.get_meal_time()} at {self.cooked_at}.'

    def get_meal_time(self):
        if 4 <= self.cooked_at.hour < 12:
            return 'Breakfast'
        elif 12 <= self.cooked_at.hour < 16:
            return 'Lunch'
        else:
            return 'Dinner'


class PlannedMeal(models.Model):
    '''
    A record of a user planning to cook a `Meal` at a specific time.
    '''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='planned_meals')
    planned_time = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} planned to cook {self.meal.name} at {self.planned_time}.'

class Ingredient(models.Model):
    '''
    An ingredient in a `Meal`, which is a specific quantity of a `FoodItem`.</br>
    The `Ingredient` model serves as a through table for the many-to-many relationship</br>
    between `Meal` and `FoodItem`. `FoodItem` fields are best accessed through the </br>
    nutrients property which calculates the nutrient values based on the quantity.
    '''
    name = models.CharField(max_length=100)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='ingredients')
    food_item = models.ForeignKey(FoodItem, on_delete=models.PROTECT, related_name='ingredients')
    quantity = models.DecimalField(max_digits=8, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['meal', 'food_item'], name='unique_ingredient_per_meal')
        ]

    def __str__(self):
        return f'{self.quantity} {self.food_item.measurement_unit} of {self.food_item.name} for {self.meal.name}'

    def get_nutrient_value(self, nutrient):
        '''
        Calculate the nutrient value for a given nutrient, portion size, and quantity, converted to the appropriate unit.
        '''
        try:
            nutrient_value_per_100g = getattr(self.food_item, nutrient)
        except AttributeError:
            raise AttributeError(f"FoodItem {self.food_item.name} does not have attribute '{nutrient}'.")
        
        # TODO: Add self.food_item.measurement_unit conversion logic
        nutrient_value = (nutrient_value_per_100g * self.food_item.portion_size_g / 100) * self.quantity
        return nutrient_value

    @property
    def nutrients(self):
        totals = {field: Decimal('0') for field in NUTRIENT_FIELDS}

        for field in totals:
            totals[field] = self.get_nutrient_value(field)

        return totals

    @property
    def current_price(self):
        '''
        Get the most recent price record.
        '''
        return self.price_records.order_by('-created_at').first()

    @property
    def price_at_creation(self):
        '''
        Get the price record from the date of creation.
        '''
        # TODO: Test this method returns the correct price record from the date of creation. 
        return self.price_records.filter(created_at__date=self.created_at.date()).order_by('-created_at').first()

    
class IngredientPriceRecord(models.Model):
    '''
    A record of the price of an `Ingredient`.
    '''
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='price_records')
    price = models.DecimalField(max_digits=8, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        # Use '£' for now - TODO: Add local currency to user settings later
        return f'Price record for {self.ingredient.name}: £{self.price}'
    