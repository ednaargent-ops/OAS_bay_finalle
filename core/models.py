from django.db import models


class Customer(models.Model):
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Vehicle(models.Model):
    HEAVY_DUTY = 'heavy_duty'
    LIGHT_DUTY = 'light_duty'
    COMMERCIAL = 'commercial'
    DUTY_CLASS_CHOICES = [
        (HEAVY_DUTY, 'Heavy Duty'),
        (LIGHT_DUTY, 'Light Duty'),
        (COMMERCIAL, 'Commercial'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=20, unique=True)
    duty_class = models.CharField(max_length=20, choices=DUTY_CLASS_CHOICES, default=LIGHT_DUTY)
    year = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.make} {self.model} ({self.plate_number})'
