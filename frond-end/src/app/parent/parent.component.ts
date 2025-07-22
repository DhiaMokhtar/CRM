import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
// Add these imports to the existing imports
import { Router } from '@angular/router';
import { MessagingService } from '../services/messaging.service';
import { ApiService } from '../api.service'; // Fix: Change from '../services/api.service' to '../api.service'

// Add homework interfaces
interface Homework {
  id: number;
  title: string;
  description: string;
  classroom: number;
  teacher: number;
  teacher_name?: string;
  due_date: string;
  created_at: string;
  submission?: HomeworkSubmission;
}

interface HomeworkSubmission {
  id: number;
  homework: number;
  student: number;
  file: string;
  submission_date: string;
  comments?: string;
}

@Component({
  selector: 'app-parent',
  standalone: false,
  templateUrl: './parent.component.html',
  styleUrl: './parent.component.scss'
})


export class ParentComponent implements OnInit {
  activeSection = 'info';
  username: any;
  parentForm: FormGroup;
  userId: string | null = null;
  children: any[] = [];
  selectedChild: any = null;
  childLessons: any[] = [];
  studentComments: any[] = [];
  childHomework: Homework[] = []; // Add this property
  unreadMessagesCount=0;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private route: ActivatedRoute,
    private router: Router,
    private messagingService: MessagingService,
    private apiService: ApiService // Add ApiService
  ) {
    const userStr = localStorage.getItem('currentUser');
    const userData = userStr ? JSON.parse(userStr) : null;
      this.username = userData?.username;

      this.userId = userData?.user_id;
      if (this.userId) {
        this.loadParentInfo();
        this.loadChildren();
      }
    
    this.parentForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.minLength(6)]]
    });
  }

  ngOnInit(): void {
    // Remove these calls since they're now handled in the constructor after getting userId
    // this.loadParentInfo();
    // this.loadChildren();
    
    // Subscribe to unread messages count
    this.messagingService.unreadCount$.subscribe(count => {
      this.unreadMessagesCount = count;
    });
  }

  loadParentInfo() {
    if (this.userId) {
      // Use HTTPS consistently for users microservice endpoint
      this.http.get(`https://localhost:8001/api/parents/${this.userId}/`).subscribe({
        next: (response: any) => {
          this.parentForm.patchValue({
            username: response.username,
            email: response.email,
            password: ''
          });
        },
        error: (error) => {
          console.error('Error loading parent info:', error);
        }
      });
    }
  }

  loadChildren() {
    if (this.userId) {
      // Change this to HTTPS to match the microservice
      this.http.get(`https://localhost:8001/api/parents/${this.userId}/children/`).subscribe({
        next: (children: any) => {
          this.children = children;
        },
        error: (error) => {
          console.error('Error loading children:', error);
        }
      });
    }
  }

  updateInfo() {
    if (this.parentForm.valid && this.userId) {
      const updateData = {
        ...this.parentForm.value,
        password: this.parentForm.value.password || undefined
      };

      // Use HTTPS consistently for users microservice endpoint
      this.http.put(`https://localhost:8001/api/parents/${this.userId}/`, updateData).subscribe({
        next: (response: any) => {
          alert('Information updated successfully');
          this.loadParentInfo();
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
    localStorage.clear();
    window.location.href = '/auth';
  }

  loadChildComments(childId: number) {
    this.http.get(`http://localhost:8000/api/student-comments/?student=${childId}`)
      .subscribe({
        next: (response: any) => {
          this.studentComments = response;
        },
        error: (error) => {
          console.error('Error loading student comments:', error);
        }
      });
  }

  loadChildHomework(childId: number) {
    this.http.get<Homework[]>(`http://localhost:8000/api/homeworks/?student=${childId}`)
      .subscribe({
        next: (homework) => {
          this.childHomework = homework;
          
          // Get teacher names and check for submissions
          this.childHomework.forEach(hw => {
            // Get teacher name
            this.http.get(`http://localhost:8000/api/teachers/${hw.teacher}/`)
              .subscribe({
                next: (teacher: any) => {
                  hw.teacher_name = teacher.username;
                },
                error: (error) => {
                  console.error('Error loading teacher info:', error);
                }
              });
              
            // Check for homework submission
            this.http.get(`http://localhost:8000/api/homework-submissions/?homework=${hw.id}&student=${childId}`)
              .subscribe({
                next: (submissions: any) => {
                  if (submissions.length > 0) {
                    hw.submission = submissions[0];
                  }
                },
                error: (error) => {
                  console.error('Error loading homework submissions:', error);
                }
              });
          });
        },
        error: (error) => {
          console.error('Error loading homework assignments:', error);
        }
      });
  }

  // Update the existing loadChildCourses method
  loadChildCourses(childId: number) {
    this.apiService.getStudentCourses(childId).subscribe({
      next: (response: any) => {
        this.childLessons = response;
        this.selectedChild = this.children.find(child => child.id === childId);
        this.loadChildComments(childId);
        this.loadChildHomework(childId);
        this.setActiveSection('childCourses');
      },
      error: (error: any) => { // Fix: Add type annotation
        console.error('Error loading child courses:', error);
      }
    });
  }

  // Add method to check if homework is overdue
  isOverdue(dueDate: string): boolean {
    return new Date(dueDate) < new Date();
  }

  openMessages(): void {
    this.router.navigate(['/messages']);
  }
}
