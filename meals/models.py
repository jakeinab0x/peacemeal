from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

# source: https://www.omnicalculator.com/conversion/grams-in-ml-converter
GRAMS_TO_ML = {
    "Milk": 0.9709,
    "Honey": 0.7042,
    "Olive Oil": 1.0893,
    "Sunflower Oil": 1.0417,
    "Vegetable Oil": 1.1236,
}

class FoodItem(models.Model):
    '''A food item containing nutritional information that can be used as an ingredient in a `Meal`.\n
    Fields are structured to contain data from a Food Nutrition Database .csv file or JSON dump from the Kaggle API.'''
    name = models.CharField(max_length=100)
    carbs = models.DecimalField(max_digits=6, decimal_places=3)
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

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
            'kilocalories': float(self.kilocalories)
        }

class Meal(models.Model):
    '''A user-created meal that can be cooked via a `CookingEvent`. 
    A `Meal` can have many ingredients, and each `Ingredient` can be used in many meals.'''
    name = models.CharField(max_length=100)
    description = models.TextField()
    ingredients = models.ManyToManyField(FoodItem, through='Ingredient')
    recipe = models.TextField()
    category = models.CharField(max_length=50)
    total_portions = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=6, decimal_places=2) # Turn into method
    
    total_carbs = models.DecimalField(max_digits=6, decimal_places=3)
    total_sugars = models.DecimalField(max_digits=6, decimal_places=3)
    total_fibre = models.DecimalField(max_digits=6, decimal_places=3)
    total_fat = models.DecimalField(max_digits=6, decimal_places=3)
    total_protein = models.DecimalField(max_digits=6, decimal_places=3)
    total_calcium = models.DecimalField(max_digits=6, decimal_places=3)
    total_iron = models.DecimalField(max_digits=6, decimal_places=3)
    total_sodium = models.DecimalField(max_digits=6, decimal_places=3)
    total_vitamin_c = models.DecimalField(max_digits=6, decimal_places=3)
    total_vitamin_b11 = models.DecimalField(max_digits=6, decimal_places=3)
    total_kilocalories = models.DecimalField(max_digits=6, decimal_places=3)

    # implement later
    # image = models.ImageField(upload_to='meal_images/', blank=True, null=True)

    created_by = models.ForeignKey(get_user_model(), blank=True, null=True, on_delete=models.SET_NULL, related_name='meals_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def calc_total_cost(self):
        total_cost = sum(ingredient.cost for ingredient in self.ingredients.all())
        return total_cost

class CookingEvent(models.Model):
    '''A record of a user cooking a `Meal` at a specific time.'''
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    meal_time = models.CharField(max_length=50, choices=[('Breakfast', 'Breakfast'), ('Lunch', 'Lunch'), ('Dinner', 'Dinner')])

    cooked_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def get_meal_time(self):
        if 4 <= self.cooked_at.hour < 12:
            return 'Breakfast'
        elif 12 <= self.cooked_at.hour < 16:
            return 'Lunch'
        else:
            return 'Dinner'

class Ingredient(models.Model):
    '''An ingredient in a `Meal`, which is a specific `FoodItem` with a quantity and cost.'''
    name = models.CharField(max_length=100)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='ingredients')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(max_length=10) # measurement?
    cost_gbp = models.DecimalField(max_digits=6, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} of {self.food_item.name} for {self.meal.name}"

    def get_nutrional_info(self):
        return {
            'carbs': self.food_item.carbs * self.quantity, # check calculation - should be per 100g or per serving?
            'sugars': self.food_item.sugars * self.quantity,
            'fibre': self.food_item.fibre * self.quantity,
            'fat': self.food_item.fat * self.quantity,
            'protein': self.food_item.protein * self.quantity,
            'calcium': self.food_item.calcium * self.quantity,
            'iron': self.food_item.iron * self.quantity,
            'sodium': self.food_item.sodium * self.quantity,
            'vitamin_c': self.food_item.vitamin_c * self.quantity,
            'vitamin_b11': self.food_item.vitamin_b11 * self.quantity,
            'kilocalories': self.food_item.kilocalories * self.quantity
        }

class IngredientPriceHistory(models.Model):
    '''A record of the price history of an `Ingredient`.'''
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=6, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)