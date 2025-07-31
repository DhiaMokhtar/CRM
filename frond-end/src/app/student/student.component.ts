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
import { ApiService } from '../api.service';

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

// Add chat interface
interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  isLoading?: boolean;
}

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

  // Add chat properties
  chatMessages: any[] = [];
  currentChatMessage: string = '';
  isChatLoading: boolean = false;
  showChat: boolean = false;
  private chatApiUrl = 'http://localhost:1234/v1/chat/completions/'; // Replace with your actual API endpoint

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private route: ActivatedRoute,
    private router: Router,
    private messagingService: MessagingService,
    private apiService: ApiService, // Add ApiService
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

// Update loadHomeworkAssignments to use homework microservice
loadHomeworkAssignments() {
  if (this.userId) {
    this.apiService.getStudentHomework(parseInt(this.userId)).subscribe({
      next: (homework) => {
        this.homeworkAssignments = homework;
      },
      error: (error) => {
        console.error('Error loading homework assignments:', error);
      }
    });
  }
}

// Update submitHomework to use homework microservice
submitHomework(homework: Homework) {
  if ((homework.selectedFile || homework.submission) && this.userId) {
    const formData = new FormData();
    formData.append('homework', homework.id.toString());
    formData.append('student_id', this.userId);  // Note: use student_id for homework microservice
    
    if (homework.selectedFile) {
      formData.append('file', homework.selectedFile);
    }
    if (homework.comments) {
      formData.append('comments', homework.comments);
    }

    if (homework.submission) {
      // Update existing submission
      this.apiService.updateHomeworkSubmission(homework.submission.id, Object.fromEntries(formData)).subscribe({
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
      // New submission
      this.apiService.submitHomework(formData).subscribe({
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

  // Add this method to check if homework is overdue
  isOverdue(dueDate: string): boolean {
    return new Date(dueDate) < new Date();
  }

  loadStudentInfo() {
    if (this.userId) {
      // Use the users microservice endpoint
      this.http.get(`http://localhost:8001/api/students/${this.userId}/`).subscribe({
        next: (response: any) => {
          this.updateData = response;
          this.studentForm.patchValue({
            username: response.username,
            email: response.email,
            password: ''
          });
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
      
      // Use the users microservice endpoint
      this.http.put(`http://localhost:8001/api/students/${this.userId}/`, updateDataUp).subscribe({
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

  // Update loadStudentCourses method
  loadStudentCourses() {
    if (this.userId) {
      this.apiService.getStudentCourses(parseInt(this.userId)).subscribe({
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
    console.log('StudentComponent initialized');
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

  // Add chat methods
  toggleChat(): void {
    this.showChat = !this.showChat;
    if (this.showChat && this.chatMessages.length === 0) {
      this.addChatMessage('Hello! I\'m here to help you with your studies. Feel free to ask me anything!', false);
    }
  }

  sendChatMessage(): void {
    if (!this.currentChatMessage.trim() || this.isChatLoading) {
      return;
    }

    // Add user message
    this.addChatMessage(this.currentChatMessage, true);
    const userMessage = this.currentChatMessage;
    this.currentChatMessage = '';

    // Add loading message
    const loadingMessage = this.addChatMessage('Thinking...', false, true);
    this.isChatLoading = true;

    // Prepare API payload
    const payload = {
      "model": "deepseek/deepseek-r1-0528-qwen3-8b",
      "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": userMessage}
      ]
    };

    // Send to API
    this.http.post<any>(this.chatApiUrl, payload).subscribe({
      next: (response) => {
        this.isChatLoading = false;
        // Remove loading message
        this.removeChatMessage(loadingMessage.id);
        
        // Add AI response
        const aiResponse = this.extractChatResponse(response);
        this.addChatMessage(aiResponse, false);
      },
      error: (error) => {
        this.isChatLoading = false;
        // Remove loading message
        this.removeChatMessage(loadingMessage.id);
        
        // Add error message
        this.addChatMessage('Sorry, I encountered an error. Please try again.', false);
        console.error('Chat error:', error);
      }
    });
  }

  private addChatMessage(content: string, isUser: boolean, isLoading: boolean = false): ChatMessage {
    const message: ChatMessage = {
      id: Date.now().toString() + Math.random(),
      content,
      isUser,
      timestamp: new Date(),
      isLoading
    };
    
    this.chatMessages.push(message);
    return message;
  }

  private removeChatMessage(messageId: string): void {
    this.chatMessages = this.chatMessages.filter(msg => msg.id !== messageId);
  }

  private extractChatResponse(response: any): string {
    // Adjust this based on your API response structure
    if (response && response.choices && response.choices[0] && response.choices[0].message) {
      return response.choices[0].message.content;
    }
    return response.message || response.content || 'No response received';
  }

  onChatKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendChatMessage();
    }
  }

  clearChat(): void {
    this.chatMessages = [];
    this.addChatMessage('Hello! I\'m here to help you with your studies. Feel free to ask me anything!', false);
  }
}



