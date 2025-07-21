from rest_framework import serializers
from .models import Administrator, Teacher, Student, Parent, ClassRoom

class ClassRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = '__all__'

class AdministratorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)  # Make it required
    
    class Meta:
        model = Administrator
        fields = ['id', 'username', 'email', 'password', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }
    
    def create(self, validated_data):
        # Extract password and create administrator
        password = validated_data.pop('password')  # Remove None default
        administrator = Administrator(**validated_data)
        
        # Always set password during creation
        administrator.password = password  # This will be hashed by the model's save method
        administrator.save()
        return administrator
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Only update password if provided
        if password:
            instance.password = password  # This will be hashed by the model's save method
        
        instance.save()
        return instance

class TeacherSerializer(serializers.ModelSerializer):
    class_ids = serializers.ListField(write_only=True, required=False)
    classes = ClassRoomSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Teacher
        fields = ['id', 'username', 'email', 'password', 'classes', 'class_ids', 'created_at']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        class_ids = validated_data.pop('class_ids', [])
        password = validated_data.pop('password', None)
        
        teacher = Teacher(**validated_data)
        if password:
            teacher.password = password
        teacher.save()
        
        if class_ids:
            teacher.classes.set(class_ids)
        return teacher
    
    def update(self, instance, validated_data):
        class_ids = validated_data.pop('class_ids', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.password = password
            
        instance.save()
        
        if class_ids is not None:
            instance.classes.set(class_ids)
        return instance

class StudentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Student
        fields = ['id', 'username', 'email', 'password', 'class_id', 'created_at']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        student = Student(**validated_data)
        if password:
            student.password = password
        student.save()
        return student
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.password = password
            
        instance.save()
        return instance

class ParentSerializer(serializers.ModelSerializer):
    student_ids = serializers.ListField(write_only=True, required=False)
    students = StudentSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Parent
        fields = ['id', 'username', 'email', 'password', 'students', 'student_ids', 'created_at']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        student_ids = validated_data.pop('student_ids', [])
        password = validated_data.pop('password', None)
        
        parent = Parent(**validated_data)
        if password:
            parent.password = password
        parent.save()
        
        if student_ids:
            parent.students.set(student_ids)
        return parent
    
    def update(self, instance, validated_data):
        student_ids = validated_data.pop('student_ids', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.password = password
            
        instance.save()
        
        if student_ids is not None:
            instance.students.set(student_ids)
        return instance