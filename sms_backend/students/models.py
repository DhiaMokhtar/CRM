from django.db import models

class ClassRoom(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Administrator(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class Teacher(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    classes = models.ManyToManyField(ClassRoom, related_name='teachers')

    def __str__(self):
        return self.username


class Student(models.Model):
    username = models.CharField(max_length=50, unique=True,null=True)
    password = models.CharField(max_length=128)  # Store hashed password
    email = models.EmailField(unique=True,null=True)
    class_id = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='students')

    def __str__(self):
        return self.username


class Parent(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    students = models.ManyToManyField(Student, related_name='parents', blank=True)

    def __str__(self):
        return self.username
    
class Lesson(models.Model):
    title = models.CharField(max_length=200)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='lessons')

    def __str__(self):
        return self.title

class Chapter(models.Model):
    title = models.CharField(max_length=200)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='chapters')

    def __str__(self):
        return self.title

class Course(models.Model):
    title = models.CharField(max_length=200)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='courses')
    pdf = models.CharField(max_length=255)  # Store the file path

    def __str__(self):
        return self.title

class StudentComment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comments')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='comments_made')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.student.username} by {self.teacher.username}"


# Add this after the existing models
class Notification(models.Model):
    recipient = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='sent_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
class Homework(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='homeworks')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assigned_homeworks')
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

# Add this after the Homework model
class HomeworkSubmission(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homework_submissions')
    file = models.FileField(upload_to='fileHomeWork/')
    submission_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.username}'s submission for {self.homework.title}"

# Message model for the messaging system
class Message(models.Model):
    SENDER_TYPES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPES)
    sender_id = models.IntegerField()
    recipient_type = models.CharField(max_length=10, choices=SENDER_TYPES)
    recipient_id = models.IntegerField()
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender_type} to {self.recipient_type}"

# Conversation model to group messages between two users
class Conversation(models.Model):
    participant1_type = models.CharField(max_length=10, choices=Message.SENDER_TYPES)
    participant1_id = models.IntegerField()
    participant2_type = models.CharField(max_length=10, choices=Message.SENDER_TYPES)
    participant2_id = models.IntegerField()
    last_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversation')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        # Ensure unique conversations between participants
        unique_together = [
            ('participant1_type', 'participant1_id', 'participant2_type', 'participant2_id'),
        ]
    
    def __str__(self):
        return f"Conversation between {self.participant1_type} and {self.participant2_type}"


# Add these models at the end of the file
class Subject(models.Model):
    name = models.CharField(max_length=100)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='subjects')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='subjects', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'classroom']
    
    def __str__(self):
        return f"{self.name} - {self.classroom.name}"

class Grade(models.Model):
    GRADE_TYPES = (
        ('exam', 'Exam'),
        ('quiz', 'Quiz'),
        ('homework', 'Homework'),
        ('project', 'Project'),
        ('participation', 'Participation'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    grade_type = models.CharField(max_length=20, choices=GRADE_TYPES, default='exam')
    score = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 85.50
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    date_recorded = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(Administrator, on_delete=models.CASCADE, related_name='recorded_grades')
    
    class Meta:
        ordering = ['-date_recorded']
    
    def __str__(self):
        return f"{self.student.username} - {self.subject.name}: {self.score}/{self.max_score}"
    
    @property
    def percentage(self):
        return (self.score / self.max_score) * 100 if self.max_score > 0 else 0

class Schedule(models.Model):
    SCHEDULE_TYPES = (
        ('class', 'Class'),
        ('exam', 'Exam'),
        ('event', 'Event'),
        ('meeting', 'Meeting'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    schedule_type = models.CharField(max_length=10, choices=SCHEDULE_TYPES, default='class')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='schedules')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], blank=True, null=True)
    recurrence_end_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(Administrator, on_delete=models.CASCADE, related_name='created_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_datetime']
    
    def __str__(self):
        return f"{self.title} - {self.classroom.name} ({self.start_datetime.strftime('%Y-%m-%d %H:%M')})"

class ScheduleNotification(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='notifications')
    recipient_type = models.CharField(max_length=10, choices=Message.SENDER_TYPES)
    recipient_id = models.IntegerField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['schedule', 'recipient_type', 'recipient_id']
    
    def __str__(self):
        return f"Notification for {self.recipient_type} about {self.schedule.title}"
