import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators,FormControl } from '@angular/forms';
import { ApiService, Class, Student, Teacher, Parent, Subject, GradeTable, Grade } from '../api.service';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
@Component({
  selector: 'app-administrator',
  standalone: false,
  templateUrl: './administrator.component.html',
  styleUrl: './administrator.component.scss'
})
export class AdministratorComponent implements OnInit {
  teacherForm: FormGroup;
  studentForm: FormGroup;
  parentForm: FormGroup; // Add parent form
  teachers: Teacher[] = [];
  students: Student[] = [];
  parents: Parent[] = []; // Add parents array
  classes: Class[] = [];
  errorMessage: string | null = null;
  selectedTeacher: Teacher | null = null;
  selectedStudent: Student | null = null;
  selectedParent: Parent | null = null; // Add selected parent
  // Add new properties for grading
  subjects: Subject[] = [];
  selectedClassForGrading: Class | null = null;
  gradeTable: GradeTable | null = null;
  isGradingMode = false;
  newSubjectName = '';
  editingGrades: { [key: string]: number } = {};
  
  // Update activeSection type
  activeSection: 'addTeacher' | 'addStudent' | 'addParent' | 
                'listTeachers' | 'listStudents' | 'listParents' | 
                'editStudent' | 'editTeacher' | 'editParent' | 'grading' = 'addTeacher';

  // Add to your class properties
  studentSearch = new FormControl('');
  filteredStudents: Student[] = [];
  
  // Update constructor
  constructor(private fb: FormBuilder, private router: Router, private apiService: ApiService,private authService: AuthService,) {
    this.teacherForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      email: ['', [Validators.required, Validators.email]],
      class_ids: [[]]
    });

    this.studentForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      email: ['', [Validators.required, Validators.email]],
      class_id: ['', Validators.required]
    });

    // Add parent form initialization
    this.parentForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      email: ['', [Validators.required, Validators.email]],
      student_ids: [[]]  // Add this form control
    });
  
    // Add search filter subscription
    this.studentSearch.valueChanges.subscribe(searchTerm => {
      if (searchTerm) {
        this.filteredStudents = this.students.filter(student =>
          student.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
          student.email.toLowerCase().includes(searchTerm.toLowerCase())
        );
      } else {
        this.filteredStudents = this.students;
      }
    });
  }

  // Update setActiveSection to include parent sections
  setActiveSection(section: typeof this.activeSection) {
    this.activeSection = section;
    if (section === 'listParents') {
      this.loadParents();
    }
  }

  ngOnInit() {
    this.loadTeachers();
    this.loadStudents();
    this.loadClasses();
    this.loadParents(); // Add loading parents
    this.filteredStudents = this.students;
  }

  loadTeachers() {
    this.apiService.getTeachers().subscribe({
      next: (teachers) => {
        this.teachers = teachers;
        this.errorMessage = null;
      },
      error: (err) => {
        this.errorMessage = 'Failed to load teachers. Please check the server.';
        console.error('Error fetching teachers:', err);
      }
    });
  }

  loadStudents() {
    this.apiService.getStudents().subscribe({
      next: (students) => {
        this.students = students;
        this.errorMessage = null;
      },
      error: (err) => {
        this.errorMessage = 'Failed to load students. Please check the server.';
        console.error('Error fetching students:', err);
      }
    });
  }

  loadClasses() {
    this.apiService.getClasses().subscribe({
      next: (classes) => {
        this.classes = classes;
        this.errorMessage = null;
      },
      error: (err) => {
        this.errorMessage = 'Failed to load classes. Please check the server.';
        console.error('Error fetching classes:', err);
      }
    });
  }

  addTeacher() {
  if (this.teacherForm.valid) {
    const teacherData = {
      username: this.teacherForm.value.username,
      password: this.teacherForm.value.password,
      email: this.teacherForm.value.email,
      class_ids: this.teacherForm.value.class_ids.map((id: string) => parseInt(id, 10)) // Convert to numbers
    };
    this.apiService.addTeacher(this.teacherForm.value).subscribe({
      next: () => {
        this.teacherForm.reset();
        this.loadTeachers();
        this.errorMessage = null;
      },
      error: (err) => {
        this.errorMessage = 'Failed to add teacher: ' + (err.error?.detail || JSON.stringify(err.error));
        console.error('Error adding teacher:', err);
      }
    });
  }
}

  addStudent() {
    if (this.studentForm.valid) {
      this.apiService.addStudent(this.studentForm.value).subscribe({
        next: () => {
          this.studentForm.reset();
          this.loadStudents();
          this.errorMessage = null;
        },
        error: (err) => {
          this.errorMessage = 'Failed to add student. Please try again.';
          console.error('Error adding student:', err);
        }
      });
    }
  }

  editStudent(student: Student) {
    this.selectedStudent = student;
    this.studentForm.patchValue({
      username: student.username,
      password: student.password,
      email: student.email,
      class_id: student.class_id
    });
    this.setActiveSection('editStudent');
  }

  updateStudent() {
    if (this.studentForm.valid && this.selectedStudent) {
      const updatedStudent = {
        ...this.selectedStudent,
        ...this.studentForm.value
      };
      this.apiService.updateStudent(updatedStudent).subscribe({
        next: () => {
          this.studentForm.reset();
          this.selectedStudent = null;
          this.loadStudents();
          this.setActiveSection('listStudents');
          this.errorMessage = null;
        },
        error: (err) => {
          this.errorMessage = 'Failed to update student. Please try again.';
          console.error('Error updating student:', err);
        }
      });
    }
  }

  // Add these new methods
  editTeacher(teacher: Teacher) {
    this.selectedTeacher = teacher;
    this.teacherForm.patchValue({
      username: teacher.username,
      email: teacher.email,
      class_ids: teacher.class_ids
    });
    this.setActiveSection('editTeacher');
  }

  updateTeacher() {
    if (this.teacherForm.valid && this.selectedTeacher) {
      const updatedTeacher = {
        ...this.selectedTeacher,
        ...this.teacherForm.value,
        class_ids: this.teacherForm.value.class_ids.map((id: string) => parseInt(id, 10))
      };
      this.apiService.updateTeacher(updatedTeacher).subscribe({
        next: () => {
          this.teacherForm.reset();
          this.selectedTeacher = null;
          this.loadTeachers();
          this.setActiveSection('listTeachers');
          this.errorMessage = null;
        },
        error: (err) => {
          this.errorMessage = 'Failed to update teacher. Please try again.';
          console.error('Error updating teacher:', err);
        }
      });
    }
  }

  // Update setActiveSection method
  
  logout() {
    this.authService.logout();
    this.router.navigate(['/auth']);
  }

  // Add parent-related methods
  loadParents() {
    this.apiService.getParents().subscribe({
      next: (parents) => {
        this.parents = parents;
        this.errorMessage = null;
      },
      error: (err) => {
        this.errorMessage = 'Failed to load parents. Please check the server.';
        console.error('Error fetching parents:', err);
      }
    });
  }

  addParent() {
    if (this.parentForm.valid) {
      this.apiService.addParent(this.parentForm.value).subscribe({
        next: () => {
          this.parentForm.reset();
          this.loadParents();
          this.errorMessage = null;
        },
        error: (err) => {
          this.errorMessage = 'Failed to add parent: ' + (err.error?.detail || JSON.stringify(err.error));
          console.error('Error adding parent:', err);
        }
      });
    }
  }

  // Add these properties to your component class
  selectedStudents: Student[] = [];
  
  // Add these methods
  toggleStudent(student: Student) {
    const index = this.selectedStudents.findIndex(s => s.id === student.id);
    if (index === -1) {
      this.selectedStudents.push(student);
    } else {
      this.selectedStudents.splice(index, 1);
    }
    this.parentForm.patchValue({ student_ids: this.selectedStudents.map(s => s.id) });
  }
  
  removeStudent(student: Student) {
    const index = this.selectedStudents.findIndex(s => s.id === student.id);
    if (index !== -1) {
      this.selectedStudents.splice(index, 1);
      this.parentForm.patchValue({ student_ids: this.selectedStudents.map(s => s.id) });
    }
  }
  
  isSelected(student: Student): boolean {
    return this.selectedStudents.some(s => s.id === student.id);
  }
  
  // Update your editParent method to include
  editParent(parent: Parent) {
    this.selectedParent = parent;
    this.parentForm.patchValue({
      username: parent.username,
      email: parent.email
    });
    // Initialize selected students if they exist
    if (parent.students) {
      this.selectedStudents = this.students.filter(student => 
        parent.students?.includes(student.id)
      );
    } else {
      this.selectedStudents = [];
    }
    this.setActiveSection('editParent');
  }

  updateParent() {
    if (this.parentForm.valid && this.selectedParent) {
      const updatedParent = {
        ...this.selectedParent,
        ...this.parentForm.value,
        students: this.selectedStudents.map(student => student.id)
      };
      this.apiService.updateParent(updatedParent).subscribe({
        next: () => {
          this.parentForm.reset();
          this.selectedParent = null;
          this.selectedStudents = []; // Reset selected students
          this.loadParents();
          this.setActiveSection('listParents');
          this.errorMessage = null;
        },
        error: (err) => {
          this.errorMessage = 'Failed to update parent. Please try again.';
          console.error('Error updating parent:', err);
        }
      });
    }
  }

  deleteParent(id: number) {
    if (confirm('Are you sure you want to delete this parent?')) {
      this.apiService.deleteParent(id).subscribe({
        next: () => {
          this.loadParents();
          this.errorMessage = null;
        },
        error: (err) => {
          this.errorMessage = 'Failed to delete parent';
          console.error('Error deleting parent:', err);
        }
      });
    }
  }
  

  loadClassesForGrading() {
    this.apiService.getClasses().subscribe({
      next: (classes) => {
        this.classes = classes;
      },
      error: (err) => {
        this.errorMessage = 'Failed to load classes';
        console.error('Error:', err);
      }
    });
  }

  selectClassForGrading(classItem: Class) {
    this.selectedClassForGrading = classItem;
    this.loadGradeTable(classItem.id);
    this.loadSubjectsForClass(classItem.id);
  }

  loadGradeTable(classroomId: number) {
    this.apiService.getGradeTable(classroomId).subscribe({
      next: (gradeTable) => {
        this.gradeTable = gradeTable;
        this.isGradingMode = true;
      },
      error: (err) => {
        this.errorMessage = 'Failed to load grade table';
        console.error('Error:', err);
      }
    });
  }

  loadSubjectsForClass(classroomId: number) {
    this.apiService.getSubjects(classroomId).subscribe({
      next: (subjects) => {
        this.subjects = subjects;
      },
      error: (err) => {
        console.error('Error loading subjects:', err);
      }
    });
  }

  addSubject() {
    if (!this.newSubjectName.trim() || !this.selectedClassForGrading) {
      return;
    }

    const subject: Partial<Subject> = {
      name: this.newSubjectName.trim(),
      classroom: this.selectedClassForGrading.id
    };

    this.apiService.createSubject(subject).subscribe({
      next: (newSubject) => {
        this.subjects.push(newSubject);
        this.newSubjectName = '';
        this.loadGradeTable(this.selectedClassForGrading!.id);
      },
      error: (err) => {
        this.errorMessage = 'Failed to add subject';
        console.error('Error:', err);
      }
    });
  }

  updateGrade(studentId: number, subjectId: number, score: number) {
    const key = `${studentId}-${subjectId}`;
    this.editingGrades[key] = score;
  }

  saveGrade(studentId: number, subjectId: number) {
    const key = `${studentId}-${subjectId}`;
    const score = this.editingGrades[key];
    
    if (score === undefined || score < 0 || score > 100) {
      this.errorMessage = 'Please enter a valid score between 0 and 100';
      return;
    }

    const grade: Partial<Grade> = {
      student: studentId,
      subject: subjectId,
      score: score,
      max_score: 100,
      grade_type: 'exam'
    };

    this.apiService.createGrade(grade).subscribe({
      next: (newGrade) => {
        delete this.editingGrades[key];
        this.loadGradeTable(this.selectedClassForGrading!.id);
        this.errorMessage = null;
      },
      error: (err) => {
        this.errorMessage = 'Failed to save grade';
        console.error('Error:', err);
      }
    });
  }

  getGradeForStudent(studentId: number, subjectId: number): Grade | null {
    if (!this.gradeTable?.grades[studentId]?.[subjectId]) {
      return null;
    }
    const grades = this.gradeTable.grades[studentId][subjectId];
    return grades.length > 0 ? grades[grades.length - 1] : null;
  }

  isEditingGrade(studentId: number, subjectId: number): boolean {
    const key = `${studentId}-${subjectId}`;
    return key in this.editingGrades;
  }

  startEditingGrade(studentId: number, subjectId: number) {
    const key = `${studentId}-${subjectId}`;
    const existingGrade = this.getGradeForStudent(studentId, subjectId);
    this.editingGrades[key] = existingGrade?.score || 0;
  }

  cancelEditingGrade(studentId: number, subjectId: number) {
    const key = `${studentId}-${subjectId}`;
    delete this.editingGrades[key];
  }

  backToClassSelection() {
    this.isGradingMode = false;
    this.selectedClassForGrading = null;
    this.gradeTable = null;
    this.subjects = [];
    this.editingGrades = {};
  }
}
