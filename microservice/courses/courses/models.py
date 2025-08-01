from django.db import models

# Remove ClassRoom model - it should only exist in users microservice

class Lesson(models.Model):
    title = models.CharField(max_length=200)
    classroom_id = models.IntegerField()  # Reference to classroom in users microservice
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Chapter(models.Model):
    title = models.CharField(max_length=200)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='chapters')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Course(models.Model):
    title = models.CharField(max_length=200)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='courses')
    pdf = models.CharField(max_length=255)  # Store the file path
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Remove Message and Conversation models - they should only exist in messaging microservice
