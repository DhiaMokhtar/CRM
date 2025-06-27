import { Component, OnInit, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { Homework } from '../api.service';
// Update the class properties
// Add these imports to the existing imports
import { Router } from '@angular/router';
import { MessagingService } from '../services/messaging.service';
import { trigger, state, style, transition, animate } from '@angular/animations';

// Add interface at the top of the file
interface Notification {
  id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  sender_name: string;
  course_title: string;
  chapter_title: string;
  lesson_title: string;
}
// Add this import at the top


// Update the component decorator
@Component({
  selector: 'app-student',
  standalone: false,
  templateUrl: './student.component.html',
  styleUrl: './student.component.scss',
  animations: [
    trigger('slideInOut', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px) scale(0.95)' }),
        animate('200ms ease-out', style({ opacity: 1, transform: 'translateY(0) scale(1)' }))
      ]),
      transition(':leave', [
        animate('150ms ease-in', style({ opacity: 0, transform: 'translateY(-10px) scale(0.95)' }))
      ])
    ])
  ]
})




export class StudentComponent implements OnInit {
  activeSection = 'info';
  username: any;
  studentForm: FormGroup;
  userId: string | null = null;
  updateData: any;
  lessons: any[] = [];
  homeworkAssignments: Homework[] = [];
  notifications: any[] = [];
  unreadNotificationsCount: number = 0;
  showNotifications: boolean = false;
  unreadMessagesCount = 0;
  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private route: ActivatedRoute,
    private router: Router,
    private messagingService: MessagingService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    const userStr = localStorage.getItem('currentUser');
    const userData = userStr ? JSON.parse(userStr) : null;
    // Only access localStorage in browser
    if (isPlatformBrowser(this.platformId)) {
      this.username = userData?.username;
    }

      this.userId = userData?.user_id;
      if (this.userId) {
        this.loadStudentInfo();
      }
    
    this.studentForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.minLength(6)]]
    });
  }
  
// Add these methods to the StudentComponent class

// Method to handle file selection
onFileSelected(event: any, homeworkId: number) {
  const file = event.target.files[0];
  if (file) {
    // Find the homework and attach the file
    const homework = this.homeworkAssignments.find(hw => hw.id === homeworkId);
    if (homework) {
      homework.selectedFile = file;
    }
  }
}

// Method to submit homework
submitHomework(homework: Homework) {
  if ((homework.selectedFile || homework.submission) && this.userId) {
    const formData = new FormData();
    formData.append('homework', homework.id.toString());
    formData.append('student', this.userId);
    if (homework.selectedFile) {
      formData.append('file', homework.selectedFile);
    }
    if (homework.comments) {
      formData.append('comments', homework.comments);
    }

    if (homework.submission) {
      // Update existing submission (PATCH or PUT)
      this.http.put(`http://localhost:8000/api/homework-submissions/${homework.submission.id}/`, formData)
        .subscribe({
          next: () => {
            alert('Homework updated successfully!');
            this.loadHomeworkAssignments();
          },
          error: (error) => {
            console.error('Error updating homework:', error);
            alert('Failed to update homework. Please try again.');
          }
        });
    } else {
      // New submission (POST)
      this.http.post('http://localhost:8000/api/homework-submissions/', formData)
        .subscribe({
          next: () => {
            alert('Homework submitted successfully!');
            this.loadHomeworkAssignments();
          },
          error: (error) => {
            console.error('Error submitting homework:', error);
            alert('Failed to submit homework. Please try again.');
          }
        });
    }
  }
}

// Update the loadHomeworkAssignments method to also load submissions
loadHomeworkAssignments() {
  if (this.userId) {
    this.http.get<Homework[]>(`http://localhost:8000/api/homeworks/?student=${this.userId}`)
      .subscribe({
        next: (homework) => {
          this.homeworkAssignments = homework;
          
          // Get teacher names for each homework
          this.homeworkAssignments.forEach(hw => {
            this.http.get(`http://localhost:8000/api/teachers/${hw.teacher}/`)
              .subscribe({
                next: (teacher: any) => {
                  hw.teacher_name = teacher.username;
                },
                error: (error) => {
                  console.error('Error loading teacher info:', error);
                }
              });
              
            // Check if student has already submitted this homework
            this.http.get(`http://localhost:8000/api/homework-submissions/?homework=${hw.id}&student=${this.userId}`)
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
}



  // Add this method to check if homework is overdue
  isOverdue(dueDate: string): boolean {
    return new Date(dueDate) < new Date();
  }

  loadStudentInfo() {
    if (this.userId) {
      this.http.get(`http://localhost:8000/api/students/${this.userId}/`).subscribe({
        next: (response: any) => {
          this.studentForm.patchValue({
            username: response.username,
            email: response.email,
            password: '' // Leave password empty
          });
          this.updateData = response;
        },
        error: (error) => {
          console.error('Error loading student info:', error);
        }
      });
    }
  }

  updateInfo() {
    if (this.studentForm.valid && this.userId) {
      const updateDataUp = {
        ...this.updateData,
        // Only include password if it was changed
        password: this.studentForm.value.password || undefined
      };
      console.log(updateDataUp);
      this.http.put(`http://localhost:8000/api/students/${this.userId}/`, updateDataUp).subscribe({
        next: (response: any) => {
          alert('Information updated successfully');
          this.loadStudentInfo(); // Reload the info
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



  // Also fix the logout method if it exists
  logout() {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.clear();
    }
    window.location.href = '/auth';
  }

  loadStudentCourses() {
    if (this.userId) {
      this.http.get(`http://localhost:8000/api/students/${this.userId}/courses/`).subscribe({
        next: (response: any) => {
          this.lessons = response;
        },
        error: (error) => {
          console.error('Error loading courses:', error);
        }
      });
    }
  }

  ngOnInit() {
    this.loadStudentInfo();
    this.loadStudentCourses();
    this.loadHomeworkAssignments(); // Add this line
    this.loadNotifications();
    
    // Subscribe to unread messages count
    this.messagingService.unreadCount$.subscribe(count => {
      this.unreadMessagesCount = count;
    });
  }

  loadNotifications() {
    if (this.userId) {
      this.http.get(`http://localhost:8000/api/notifications/?student_id=${this.userId}`)
        .subscribe({
          next: (response: any) => {
            this.notifications = response;
            this.unreadNotificationsCount = this.notifications.filter(n => !n.is_read).length;
          },
          error: (error) => {
            console.error('Error loading notifications:', error);
          }
        });
    }
  }

// Add this method to the class
// Add this method to your StudentComponent class
markAllAsRead() {
  const unreadNotifications = this.notifications.filter(n => !n.is_read);
  
  unreadNotifications.forEach(notification => {
    this.http.put(`http://localhost:8000/api/notifications/${notification.id}/`, {})
      .subscribe({
        next: () => {
          notification.is_read = true;
        },
        error: (error) => {
          console.error('Error marking notification as read:', error);
        }
      });
  });
  
  this.unreadNotificationsCount = 0;
}

// Update the existing toggleNotifications method
toggleNotifications() {
  this.showNotifications = !this.showNotifications;
  if (this.showNotifications) {
    // Auto-refresh notifications when opened
    this.loadNotifications();
  }
}

  markAsRead(notificationId: number) {
    this.http.put(`http://localhost:8000/api/notifications/${notificationId}/`, {})
      .subscribe({
        next: () => {
          const notification = this.notifications.find(n => n.id === notificationId);
          if (notification) {
            notification.is_read = true;
            this.unreadNotificationsCount = this.notifications.filter(n => !n.is_read).length;
          }
        },
        error: (error) => {
          console.error('Error marking notification as read:', error);
        }
      });
  }
  openMessages(): void {
    this.router.navigate(['/messages']);
  }
}

 

