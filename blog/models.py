from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

class Position(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Worker(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to='workers/', blank=True, null=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Car(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    available = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='cars/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='cars')

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

class Customer(models.Model):
    name = models.CharField(max_length=150)
    contact_info = models.TextField()
    phone_number = models.CharField(max_length=20)
    purchased_cars = models.ManyToManyField(Car, blank=True, related_name='buyers')

    def __str__(self):
        return self.name

class Sale(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    seller = models.ForeignKey(Worker, on_delete=models.CASCADE)
    sale_date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Sale: {self.car} -> {self.customer}"