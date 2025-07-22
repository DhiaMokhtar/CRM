import { Component, OnInit, Inject, PLATFORM_ID } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { CourseMaterial, Lesson, Chapter, Grade, GradeTable, Subject } from '../api.service'; // Add Grade, GradeTable, Subject
import { AuthService } from '../services/auth.service';
import { MessagingService } from '../services/messaging.service';
import { isPlatformBrowser } from '@angular/common';
import { ApiService } from '../api.service'; // Add ApiService import

// Add Homework interface
interface Homework {
  id: number;
  title: string;
  description: string;
  classroom: number;
  teacher: number;
  due_date: string;
  created_at: string;
  submissions?: HomeworkSubmission[];
  showSubmissions?: boolean; // Add this property to fix the previous error
}

// Add HomeworkSubmission interface
interface HomeworkSubmission {
  id: number;
  homework: number;
  student: number;
  student_name: string;
  file: string;
  submission_date: string;
  comments?: string;
}

@Component({
  selector: 'app-teacher',
  standalone: false,
  templateUrl: './teacher.component.html',
  styleUrl: './teacher.component.scss'
})
export class TeacherComponent implements OnInit {
  selectedClass: any = null;
  classStudents: any[] = [];
  activeSection = 'info';
  username: any;
  teacherForm: FormGroup;
  userId: string | null = null;
  classes: any[] = [];
  selectedStudent: any = null;
  studentComments: any[] = [];
  newComment: string = '';
  bulkComment: string = '';
  // Add these new properties
  homeworkForm: FormGroup;
  classHomework: Homework[] = [];
  showAddHomeworkForm: boolean = false; // Add this property
  showBulkCommentSection: boolean = false; // Add this line
  isBrowser: boolean;
  unreadMessagesCount = 0;

  // Add grading properties
  selectedClassForGrading: any = null;
  gradeTable: GradeTable | null = null;
  isGradingMode = false;
  editingGrades: { [key: string]: number } = {};
  newSubjectName = '';
  showAddSubjectForm = false;


  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService,
    private messagingService: MessagingService,
    private apiService: ApiService, // Add ApiService
    @Inject(PLATFORM_ID) private platformId: Object
  ) {

    const userStr = localStorage.getItem('currentUser');
    const userData = userStr ? JSON.parse(userStr) : null;
    this.isBrowser = isPlatformBrowser(this.platformId);
    if (this.isBrowser) {
      this.username = userData?.username;
    }
    
      this.userId = userData?.user_id;
      if (this.userId) {
        this.loadTeacherInfo();
        this.loadTeacherClasses();
      }
    
    this.teacherForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.minLength(6)]]
    });
    
    // Initialize homework form
    this.homeworkForm = this.fb.group({
      title: ['', Validators.required],
      description: ['', Validators.required],
      due_date: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    // Remove these calls since they're now handled in the constructor after getting userId
     this.loadTeacherInfo();
     this.loadTeacherClasses();
    
    // Subscribe to unread messages count
    this.messagingService.unreadCount$.subscribe(count => {
      this.unreadMessagesCount = count;
    });
  }

  loadCoursesForChapter(chapter: any) {
    this.http.get<any[]>(`http://localhost:8000/api/courses/?chapter=${chapter.id}`)
      .subscribe({
        next: (courses) => {
          chapter.materials = courses.map((course) => ({
            name: course.title,
            url: `https://localhost:8000${course.pdf}`  // Change to HTTPS
          }));
        },
        error: (error) => {
          console.error('Error loading materials:', error);
        }
      });
  }
  

  // Fix loadTeacherInfo to use HTTPS
  loadTeacherInfo() {
    if (this.userId) {
      // Use HTTPS for users microservice endpoint
      this.http.get(`https://localhost:8001/api/teachers/${this.userId}/`).subscribe({
        next: (response: any) => {
          this.teacherForm.patchValue({
            username: response.username,
            email: response.email,
            password: ''
          });
        },
        error: (error) => {
          console.error('Error loading teacher info:', error);
        }
      });
    }
  }

  // Fix loadTeacherClasses to use HTTPS
  loadTeacherClasses() {
    if (this.userId) {
      // Use HTTPS for users microservice endpoint
      this.http.get(`https://localhost:8001/api/teachers/${this.userId}/`).subscribe({
        next: (response: any) => {
          this.classes = response.classes || [];
        },
        error: (error) => {
          console.error('Error loading teacher classes:', error);
        }
      });
    }
  }

  // Fix updateInfo to use HTTPS
  updateInfo() {
    if (this.teacherForm.valid && this.userId) {
      const updateData = {
        ...this.teacherForm.value,
        password: this.teacherForm.value.password || undefined,
        class_ids: this.classes.map(c => c.id)
      };

      // Use HTTPS for users microservice endpoint
      this.http.put(`https://localhost:8001/api/teachers/${this.userId}/`, updateData).subscribe({
        next: (response: any) => {
          alert('Information updated successfully');
          this.loadTeacherInfo();
          this.loadTeacherClasses();
        },
        error: (error) => {
          alert('Failed to update information: ' + error.error?.detail || 'Unknown error');
        }
      });
    }
  }

  setActiveSection(section: string) {
    this.activeSection = section;
  }

  logout() {
    this.authService.logout();
    window.location.href = '/auth';
  }

  lessons: Lesson[] = [];

  // Update loadLessons method
  loadLessons(classId: number) {
    this.apiService.getLessons(classId).subscribe({
      next: (lessons) => {
        this.lessons = lessons;
        console.log('class:', classId);
        console.log('lesson:', this.lessons);
        lessons.forEach(lesson => this.loadChapters(lesson));
      },
      error: (error) => {
        console.error('Error loading lessons:', error);
      }
    });
  }

  // Update loadChapters method
  loadChapters(lesson: Lesson) {
    this.apiService.getChapters(lesson.id).subscribe({
      next: (chapters) => {
        lesson.chapters = chapters;
        chapters.forEach(chapter => this.loadCourseMaterials(chapter));
      },
      error: (error) => {
        console.error('Error loading chapters:', error);
      }
    });
  }

  // Update loadCourseMaterials method
  loadCourseMaterials(chapter: Chapter) {
    this.apiService.getCourseMaterials(chapter.id).subscribe({
      next: (materials) => {
        chapter.materials = materials;
        chapter.materials.forEach(material => {
          console.log("material:"+material.pdf);
        });
      },
      error: (error) => {
        console.error('Error loading materials:', error);
      }
    });
  }

  addNewLesson() {
    const title = prompt('Enter lesson title:');
    if (title && this.selectedClass) {
      const newLesson = {
        title,
        classroom: this.selectedClass.id,
      };

      this.apiService.createLesson(newLesson).subscribe({
        next: (response: any) => {
          this.loadLessons(this.selectedClass.id);
        },
        error: (error) => {
          console.error('Error creating lesson:', error);
        }
      });
    }
  }

  // Update addChapter method
  addChapter(lesson: Lesson) {
    const title = prompt('Enter chapter title:');
    if (title) {
      const newChapter = {
        title,
        lesson: lesson.id,
      };

      this.apiService.createChapter(newChapter).subscribe({
        next: (response: any) => {
          this.loadChapters(lesson);
        },
        error: (error) => {
          console.error('Error creating chapter:', error);
        }
      });
    }
  }

  // Remove courseChapters array since we're using lessons/chapters structure
  
  addChapterContent(chapter: Chapter) {
    chapter.isAddingContent = true;
  }

  onFileSelected(event: any, chapter: Chapter) {
    const file = event.target.files[0];
    if (file) {
      chapter.selectedFile = file;
    }
  }

  // Update uploadContent method
  uploadContent(chapter: Chapter) {
    if (chapter.selectedFile) {
      const formData = new FormData();
      formData.append('title', chapter.selectedFile.name);
      formData.append('chapter', chapter.id.toString());
      formData.append('pdf_file', chapter.selectedFile);
      
      this.apiService.createCourseMaterial(formData).subscribe({
        next: (response: any) => {
          this.loadCourseMaterials(chapter);
          chapter.isAddingContent = false;
          delete chapter.selectedFile;
        },
        error: (error) => {
          console.error('Error uploading content:', error);
          alert('Failed to upload file');
        }
      });
    }
  }

  cancelUpload(chapter: Chapter) {
    chapter.isAddingContent = false;
    chapter.selectedFile = undefined;  // Changed from null to undefined
  }

  // Update deleteMaterial method
  deleteMaterial(chapter: Chapter, material: CourseMaterial) {
    if (confirm('Are you sure you want to delete this material?')) {
      this.apiService.deleteCourseMaterial(material.id).subscribe({
        next: () => {
          this.loadCourseMaterials(chapter);
        },
        error: (error) => {
          console.error('Error deleting material:', error);
          alert('Failed to delete material');
        }
      });
    }
  }

  // Update selectClass method to load homework
  selectClass(classRoom: any) {
    this.selectedClass = classRoom;
    if (this.activeSection === 'courses') {
      // Clear existing lessons and their chapters before loading new ones
      this.lessons = [];
      this.loadLessons(classRoom.id);
    } else {
      this.loadClassStudents(classRoom.id);
      this.loadClassHomework(classRoom.id); // Add this line
    }
  }

  // Fix loadClassStudents to use HTTPS
  loadClassStudents(classId: number) {
    this.http.get(`https://localhost:8000/api/classes/${classId}/students/`).subscribe({
      next: (response: any) => {
        this.classStudents = response;
      },
      error: (error) => {
        console.error('Error loading class students:', error);
      }
    });

  }
  // Update the loadClassHomework method to include submissions
  loadClassHomework(classId: number) {
    this.http.get<Homework[]>(`https://localhost:8000/api/homeworks/?classroom=${classId}`)
      .subscribe({
        next: (homework) => {
          this.classHomework = homework;
          
          // For each homework, load its submissions
          this.classHomework.forEach(hw => {
            this.loadHomeworkSubmissions(hw.id);
          });
        },
        error: (error) => {
          console.error('Error loading homework:', error);
        }
      });
  }
  
  // Fix loadHomeworkSubmissions to use HTTPS
  loadHomeworkSubmissions(homeworkId: number) {
    this.http.get<HomeworkSubmission[]>(`https://localhost:8000/api/homework-submissions/?homework=${homeworkId}`)
      .subscribe({
        next: (submissions) => {
          // Find the homework and attach its submissions
          const homework = this.classHomework.find(hw => hw.id === homeworkId);
          if (homework) {
            homework.submissions = submissions;
          }
        },
        error: (error) => {
          console.error('Error loading homework submissions:', error);
        }
      });
  }
  
  // Add method to view submission file
  viewSubmission(fileUrl: string) {
    window.open(fileUrl, '_blank');
  }
  
  // Add method to add a new homework
  addHomework() {
    if (this.homeworkForm.valid && this.selectedClass && this.userId) {
      const homeworkData = {
        ...this.homeworkForm.value,
        classroom: this.selectedClass.id,
        teacher: this.userId
      };
      
      this.http.post('https://localhost:8000/api/homeworks/', homeworkData)
        .subscribe({
          next: (response: any) => {
            this.loadClassHomework(this.selectedClass.id);
            this.homeworkForm.reset();
          },
          error: (error) => {
            console.error('Error adding homework:', error);
            alert('Failed to add homework. Please try again.');
          }
        });
    }
  }
  
  // Fix deleteHomework to use HTTPS
  deleteHomework(homeworkId: number) {
    if (confirm('Are you sure you want to delete this homework assignment?')) {
      this.http.delete(`https://localhost:8000/api/homeworks/${homeworkId}/`)
        .subscribe({
          next: () => {
            this.loadClassHomework(this.selectedClass.id);
          },
          error: (error) => {
            console.error('Error deleting homework:', error);
            alert('Failed to delete homework. Please try again.');
          }
        });
    }
  }
  
  // Update backToClasses method to clear homework
  backToClasses() {
    this.selectedClass = null;
    this.classStudents = [];
    this.lessons = []; // Clear lessons when going back to class list
    this.classHomework = []; // Add this line
  }


  courseChapters: any[] = [];

  addNewChapter() {
    const chapterTitle = prompt('Enter chapter title:');
    if (chapterTitle) {
      this.courseChapters.push({
        title: chapterTitle,
        materials: [],
        isAddingContent: false
      });
    }
  }
  
  viewStudentComments(student: any) {
    this.selectedStudent = student;
    this.loadStudentComments();
  }

  closeCommentsModal() {
    this.selectedStudent = null;
    this.studentComments = [];
    this.newComment = '';
  }

  // Fix loadStudentComments to use HTTPS
  loadStudentComments() {
    if (this.selectedStudent) {
      this.http.get(`https://localhost:8000/api/student-comments/?student=${this.selectedStudent.id}`)
        .subscribe({
          next: (response: any) => {
            this.studentComments = response;
          },
          error: (error) => {
            console.error('Error loading student comments:', error);
          }
        });
    }
  }

  // Fix addComment to use HTTPS
  addComment() {
    if (this.newComment.trim() && this.selectedStudent && this.userId) {
      const commentData = {
        student: this.selectedStudent.id,
        teacher: this.userId,
        content: this.newComment.trim()
      };
      
      this.http.post('https://localhost:8000/api/student-comments/', commentData)
        .subscribe({
          next: (response: any) => {
            this.loadStudentComments();
            this.newComment = '';
          },
          error: (error) => {
            console.error('Error adding comment:', error);
            alert('Failed to add comment. Please try again.');
          }
        });
    }
  }

  addCommentToAllStudents() {
    if (this.bulkComment.trim() && this.selectedClass) {
      const commentData = {
        content: this.bulkComment,
        class_id: this.selectedClass.id,
        teacher: this.userId
      };
      this.http.post('https://localhost:8000/api/comments/bulk/', commentData).subscribe({
        next: () => {
          alert('Comment added to all students successfully');
          this.bulkComment = '';
          this.loadStudentComments(); // Refresh comments if needed
        },
        error: (error) => {
          console.error('Error adding comments:', error);
          alert('Failed to add comments to all students');
        }
      });
    } else {
      alert('Please enter a comment and select a class');
    }
  }
  // Add method to toggle homework form visibility
  toggleAddHomeworkForm() {
    this.showAddHomeworkForm = !this.showAddHomeworkForm;
    }

    openMessages(): void {
      this.router.navigate(['/messages']);
    }
    
// Add grading methods
selectClassForGrading(classItem: any) {
  this.selectedClassForGrading = classItem;
  this.loadGradeTable(classItem.id);
  this.setActiveSection('grading');
  }
  
  loadGradeTable(classroomId: number) {
  this.apiService.getGradeTable(classroomId).subscribe({
  next: (gradeTable) => {
  this.gradeTable = gradeTable;
  this.isGradingMode = true;
  },
  error: (error) => {
  console.error('Failed to load grade table:', error);
  }
  });
  }
  
  addSubject() {
  if (!this.newSubjectName.trim() || !this.selectedClassForGrading) {
  return;
  }
  
  const subject = {
  name: this.newSubjectName,
  classroom: this.selectedClassForGrading.id
  };
  
  this.apiService.createSubject(subject).subscribe({
  next: () => {
  this.newSubjectName = '';
  this.showAddSubjectForm = false;
  this.loadGradeTable(this.selectedClassForGrading!.id);
  },
  error: (error) => {
  console.error('Failed to add subject:', error);
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
  alert('Please enter a valid grade between 0 and 20');
  return;
  }
  
  const grade: Partial<Grade> = {
  student: studentId,
  subject: subjectId,
  score: score,
  grade_type: 'exam'
  };
  
  this.apiService.createGrade(grade).subscribe({
  next: (newGrade) => {
  delete this.editingGrades[key];
  this.loadGradeTable(this.selectedClassForGrading!.id);
  },
  error: (error) => {
  console.error('Failed to save grade:', error);
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
  
  exitGradingMode() {
  this.isGradingMode = false;
  this.selectedClassForGrading = null;
  this.gradeTable = null;
  this.showAddSubjectForm = false;
  this.editingGrades = {};
  }
}











