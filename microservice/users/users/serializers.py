from rest_framework import serializers
from .models import Administrator, Teacher, Student, ClassRoom, Parent

class ClassRoomSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassRoom
        fields = ['id', 'name', 'student_count', 'teacher_count']  # Remove created_at
        # Remove read_only_fields = ['created_at'] since there's no created_at field
    
    def get_student_count(self, obj):
        return obj.students.count()
    
    def get_teacher_count(self, obj):
        return obj.teachers.count()

class TeacherSerializer(serializers.ModelSerializer):
    classes = ClassRoomSerializer(many=True, read_only=True)
    class_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        write_only=True, 
        queryset=ClassRoom.objects.all(), 
        source='classes',
        required=False
    )
    class_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = ['id', 'username', 'password', 'email', 'classes', 'class_ids', 'class_names', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }
        read_only_fields = ['created_at']
    
    def get_class_names(self, obj):
        return [cls.name for cls in obj.classes.all()]
    
    def create(self, validated_data):
        classes_data = validated_data.pop('classes', [])
        teacher = Teacher.objects.create(**validated_data)
        if classes_data:
            teacher.classes.set(classes_data)
        return teacher
    
    def update(self, instance, validated_data):
        classes_data = validated_data.pop('classes', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update classes if provided
        if classes_data is not None:
            instance.classes.set(classes_data)
        
        return instance

class StudentSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_id.name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'username', 'password', 'email', 'class_id', 'class_name', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }
        read_only_fields = ['created_at']

class AdministratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrator
        fields = ['id', 'username', 'password', 'email', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }
        read_only_fields = ['created_at']

class ParentSerializer(serializers.ModelSerializer):
    children = StudentSerializer(many=True, read_only=True, source='students')
    children_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Student.objects.all(),
        source='students',
        required=False
    )
    
    class Meta:
        model = Parent
        fields = ['id', 'username', 'password', 'email', 'students', 'children', 'children_ids', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }
        read_only_fields = ['created_at']
    
    def create(self, validated_data):
        students_data = validated_data.pop('students', [])
        parent = Parent.objects.create(**validated_data)
        if students_data:
            parent.students.set(students_data)
        return parent
    
    def update(self, instance, validated_data):
        students_data = validated_data.pop('students', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update students if provided
        if students_data is not None:
            instance.students.set(students_data)
        
        return instance