from django.db import models

class Homework(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    classroom_id = models.IntegerField()  # Reference to classroom in users microservice
    teacher_id = models.IntegerField()    # Reference to teacher in users microservice
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class HomeworkSubmission(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student_id = models.IntegerField()  # Reference to student in users microservice
    file = models.FileField(upload_to='homework_submissions/', blank=True, null=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True, null=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    graded_at = models.DateTimeField(blank=True, null=True)
    graded_by = models.IntegerField(blank=True, null=True)  # Teacher who graded
    
    class Meta:
        unique_together = ['homework', 'student_id']
        ordering = ['-submission_date']
    
    def __str__(self):
        return f"Submission for {self.homework.title} by Student #{self.student_id}"
