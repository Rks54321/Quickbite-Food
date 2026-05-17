from django.db import models

# Create your models here.
class Customer(models.Model):
    username = models.CharField(max_length = 20)
    password = models.CharField(max_length = 20)
    email = models.CharField(max_length = 20)
    mobile = models.CharField(max_length = 10)
    address = models.CharField(max_length = 50)

class Restaurant(models.Model):
    name = models.CharField(max_length = 20)
    picture = models.CharField(max_length = 200, default='https://platform.la.eater.com/wp-content/uploads/sites/26/chorus/uploads/chorus_asset/file/22764709/2021_06_24_Gril_TheGoat_005.jpg?quality=90&strip=all&crop=16.619412941961%2C0%2C66.761174116077%2C100&w=2400')
    cuisine = models.CharField(max_length = 200)
    rating = models.CharField(max_length=5)

class Item(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete = models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length = 20)
    picture = models.URLField(max_length = 200, default="https://cdn-icons-png.flaticon.com/512/1147/1147856.png")
    description = models.CharField(max_length = 200)
    price = models.FloatField()
    is_veg = models.BooleanField(default = True)

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE, related_name = "cart")
    items = models.ManyToManyField("Item", related_name = "carts")

    def total_price(self):
        return sum(item.price for item in self.items.all())