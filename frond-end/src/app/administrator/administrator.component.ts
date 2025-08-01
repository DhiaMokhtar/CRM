import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormControl } from '@angular/forms';
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
  parentForm: FormGroup;
  teachers: Teacher[] = [];
  students: Student[] = [];
  parents: Parent[] = [];
  classes: Class[] = [];
  errorMessage: string | null = null;
  selectedTeacher: Teacher | null = null;
  selectedStudent: Student | null = null;
  selectedParent: Parent | null = null;
  subjects: Subject[] = [];
  selectedClassForGrading: Class | null = null;
  gradeTable: GradeTable | null = null;
  isGradingMode = false;
  newSubjectName = '';
  editingGrades: { [key: string]: number } = {};
  
  activeSection: 'addTeacher' | 'addStudent' | 'addParent' | 
                'listTeachers' | 'listStudents' | 'listParents' | 
                'editStudent' | 'editTeacher' | 'editParent' | 'grading' = 'addTeacher';

  studentSearch = new FormControl('');
  filteredStudents: Student[] = [];
  selectedStudents: Student[] = [];
  
  constructor(
    private fb: FormBuilder, 
    private router: Router, 
    private apiService: ApiService,
    private authService: AuthService
  ) {
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

    this.parentForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      email: ['', [Validators.required, Validators.email]],
      student_ids: [[]]
    });
  
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

  setActiveSection(section: typeof this.activeSection) {
    this.activeSection = section;
    if (section === 'listParents') {
      this.loadParents();
    }
    if (section === 'grading') {
      this.loadClassesForGrading();
    }
  }

  ngOnInit() {
    this.loadTeachers();
    this.loadStudents();
    this.loadClasses();
    this.loadParents();
    this.filteredStudents = this.students;
  }

  loadTeachers() {
    this.apiService.getTeachers().subscribe({
      next: (teachers: Teacher[]) => {
        this.teachers = teachers;
        this.errorMessage = null;
      },
      error: (err: any) => {
        this.errorMessage = 'Failed to load teachers. Please check the server.';
        console.error('Error fetching teachers:', err);
      }
    });
  }

  loadStudents() {
    this.apiService.getStudents().subscribe({
      next: (students: Student[]) => {
        this.students = students;
        this.errorMessage = null;
      },
      error: (err: any) => {
        this.errorMessage = 'Failed to load students. Please check the server.';
        console.error('Error fetching students:', err);
      }
    });
  }

  loadClasses() {
    this.apiService.getClasses().subscribe({
      next: (classes: Class[]) => {
        this.classes = classes;
        this.errorMessage = null;
      },
      error: (err: any) => {
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
        class_ids: this.teacherForm.value.class_ids.map((id: string) => parseInt(id, 10))
      };
      this.apiService.addTeacher(teacherData).subscribe({
        next: (teacher: Teacher) => {
          this.teacherForm.reset();
          this.loadTeachers();
          this.errorMessage = null;
        },
        error: (err: any) => {
          this.errorMessage = 'Failed to add teacher: ' + (err.error?.detail || JSON.stringify(err.error));
          console.error('Error adding teacher:', err);
        }
      });
    }
  }

  addStudent() {
    if (this.studentForm.valid) {
      this.apiService.addStudent(this.studentForm.value).subscribe({
        next: (student: Student) => {
          this.studentForm.reset();
          this.loadStudents();
          this.errorMessage = null;
        },
        error: (err: any) => {
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
        next: (student: Student) => {
          this.studentForm.reset();
          this.selectedStudent = null;
          this.loadStudents();
          this.setActiveSection('listStudents');
          this.errorMessage = null;
        },
        error: (err: any) => {
          this.errorMessage = 'Failed to update student. Please try again.';
          console.error('Error updating student:', err);
        }
      });
    }
  }

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
        next: (teacher: Teacher) => {
          this.teacherForm.reset();
          this.selectedTeacher = null;
          this.loadTeachers();
          this.setActiveSection('listTeachers');
          this.errorMessage = null;
        },
        error: (err: any) => {
          this.errorMessage = 'Failed to update teacher. Please try again.';
          console.error('Error updating teacher:', err);
        }
      });
    }
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/auth']);
  }

  loadParents() {
    this.apiService.getParents().subscribe({
      next: (parents: Parent[]) => {
        this.parents = parents;
        this.errorMessage = null;
      },
      error: (err: any) => {
        this.errorMessage = 'Failed to load parents. Please check the server.';
        console.error('Error fetching parents:', err);
      }
    });
  }

  addParent() {
    if (this.parentForm.valid) {
      this.apiService.addParent(this.parentForm.value).subscribe({
        next: (parent: Parent) => {
          this.parentForm.reset();
          this.loadParents();
          this.errorMessage = null;
        },
        error: (err: any) => {
          this.errorMessage = 'Failed to add parent: ' + (err.error?.detail || JSON.stringify(err.error));
          console.error('Error adding parent:', err);
        }
      });
    }
  }

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

  editParent(parent: Parent) {
    this.selectedParent = parent;
    this.parentForm.patchValue({
      username: parent.username,
      email: parent.email
    });
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
        next: (parent: Parent) => {
          this.parentForm.reset();
          this.selectedParent = null;
          this.selectedStudents = [];
          this.loadParents();
          this.setActiveSection('listParents');
          this.errorMessage = null;
        },
        error: (err: any) => {
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
        error: (err: any) => {
          this.errorMessage = 'Failed to delete parent';
          console.error('Error deleting parent:', err);
        }
      });
    }
  }

  loadClassesForGrading() {
    this.apiService.getClasses().subscribe({
      next: (classes: Class[]) => {
        this.classes = classes;
      },
      error: (err: any) => {
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
      next: (gradeTable: GradeTable) => {
        this.gradeTable = gradeTable;
        this.isGradingMode = true;
      },
      error: (err: any) => {
        this.errorMessage = 'Failed to load grade table';
        console.error('Error:', err);
      }
    });
  }

  loadSubjectsForClass(classroomId: number) {
    this.apiService.getSubjects(classroomId).subscribe({
      next: (subjects: Subject[]) => {
        this.subjects = subjects;
      },
      error: (err: any) => {
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
      classroom_id: this.selectedClassForGrading.id,  // Use classroom_id instead of classroom
      teacher_id: 1  // You'll need to get the current user's ID
    };

    this.apiService.createSubject(subject).subscribe({
      next: (newSubject: Subject) => {
        this.subjects.push(newSubject);
        this.newSubjectName = '';
        this.loadGradeTable(this.selectedClassForGrading!.id);
      },
      error: (err: any) => {
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
    
    if (score === undefined || score < 0 || score > 20) {
      this.errorMessage = 'Please enter a valid score between 0 and 20';
      return;
    }

    const grade: Partial<Grade> = {
      student_id: studentId,  // Use student_id instead of student
      subject: subjectId,
      score: score,
      max_score: 20,
      grade_type: 'exam',
      recorded_by_id: 1  // You'll need to get the current user's ID
    };

    this.apiService.createGrade(grade).subscribe({
      next: (newGrade: Grade) => {
        delete this.editingGrades[key];
        this.loadGradeTable(this.selectedClassForGrading!.id);
        this.errorMessage = null;
      },
      error: (err: any) => {
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
