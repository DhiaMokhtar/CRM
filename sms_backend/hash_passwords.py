import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sms_backend.settings')
django.setup()
from django.contrib.auth.hashers import make_password
from students.models import Administrator, Teacher, Student,Parent

# Hash Administrator passwords
for user in Administrator.objects.all():
    if not user.password.startswith('pbkdf2_'):
        user.password = make_password(user.password)
        user.save()

# Hash Teacher passwords
for user in Teacher.objects.all():
    if not user.password.startswith('pbkdf2_'):
        user.password = make_password(user.password)
        user.save()

# Hash Student passwords
for user in Student.objects.all():
    if not user.password.startswith('pbkdf2_'):
        user.password = make_password(user.password)
        user.save()

# Hash Parent passwords
for user in Parent.objects.all():
    if not user.password.startswith('pbkdf2_'):
        user.password = make_password(user.password)
        user.save()

print("Password hashing completed.")
