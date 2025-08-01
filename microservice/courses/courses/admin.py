from django.contrib import admin
from .models import Lesson, Chapter, Course

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'classroom_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title']

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'chapter', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title']
