from django.db import models

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

# Add grading models
class Subject(models.Model):
    name = models.CharField(max_length=200)
    classroom_id = models.IntegerField()  # Reference to classroom in users microservice
    teacher_id = models.IntegerField()  # Reference to teacher in users microservice
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'classroom_id']

    def __str__(self):
        return f"{self.name} - Classroom {self.classroom_id}"

class Grade(models.Model):
    GRADE_TYPES = [
        ('exam', 'Exam'),
        ('homework', 'Homework'),
        ('quiz', 'Quiz'),
        ('project', 'Project'),
        ('participation', 'Participation'),
    ]
    
    student_id = models.IntegerField()  # Reference to student in users microservice
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    grade_type = models.CharField(max_length=20, choices=GRADE_TYPES, default='exam')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    notes = models.TextField(blank=True, null=True)
    recorded_by_id = models.IntegerField()  # Reference to teacher/admin in users microservice
    date_recorded = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_recorded']

    @property
    def percentage(self):
        if self.max_score > 0:
            return (self.score / self.max_score) * 100
        return 0

    def __str__(self):
        return f"Student {self.student_id} - {self.subject.name}: {self.score}/{self.max_score}"
