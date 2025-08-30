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
import { forkJoin, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

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

  // Update PDF context properties
  private pdfContext: string = '';
  private pdfContextLoading = false;
  private pdfContextReady = false;
  private pdfContextMaxChars = 15000; // safeguard to avoid overly large prompt

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
          // After lessons load, build the PDF context
          this.buildPdfContext();
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
      console.log('Loading notifications for student ID:', this.userId);
      
      // Use messaging microservice with proper authentication
      this.http.get(`https://localhost:8003/api/notifications/?student_id=${this.userId}`, 
        { withCredentials: true })
        .subscribe({
          next: (response: any) => {
            console.log('Raw notifications response:', response);
            console.log('Response type:', typeof response);
            console.log('Is array?', Array.isArray(response));
            
            this.notifications = Array.isArray(response) ? response : [];
            this.unreadNotificationsCount = this.notifications.filter(n => !n.is_read).length;
            
            console.log('Processed notifications:', this.notifications);
            console.log('Unread count:', this.unreadNotificationsCount);
          },
          error: (error) => {
            console.error('Error loading notifications:', error);
            console.error('Error status:', error.status);
            console.error('Error details:', error.error);
          }
        });
    } else {
      console.log('No user ID available for loading notifications');
    }
  }

  markAsRead(notificationId: number) {
    console.log('Marking notification as read:', notificationId, 'for student:', this.userId);
    
    this.http.put(`https://localhost:8003/api/notifications/${notificationId}/`, 
      { is_read: true, student_id: parseInt(this.userId!) }, 
      { withCredentials: true })
      .subscribe({
        next: () => {
          console.log('Notification marked as read successfully');
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

  // Add this method to the class
  markAllAsRead() {
    const unreadNotifications = this.notifications.filter(n => !n.is_read);
    
    unreadNotifications.forEach(notification => {
      this.http.put(`https://localhost:8003/api/notifications/${notification.id}/`, 
        { is_read: true }, 
        { withCredentials: true })  // Add withCredentials for authentication
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

  toggleNotifications() {
    this.showNotifications = !this.showNotifications;
    if (this.showNotifications) {
      // Auto-refresh notifications when opened
      this.loadNotifications();
    }
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

    if (!this.pdfContextReady) {
      this.addChatMessage('Course materials still loading. Please wait a moment and retry.', false);
      return;
    }

    // Add user message
    this.addChatMessage(this.currentChatMessage, true);
    const userMessage = this.currentChatMessage;
    this.currentChatMessage = '';

    // Loading placeholder
    const loadingMessage = this.addChatMessage('Thinking...', false, true);
    this.isChatLoading = true;

    // Build prompt exactly as requested
    const prompt =
  `Answer the question based only on the following course material:

  ${this.pdfContext || '[No course material available]'}

  Question: ${userMessage}`;

      const payload = {
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: 'You are a course assistant.' },
          { role: 'user', content: prompt }
        ]
      };
      console.log('Sending chat request with payload:', payload);
      this.http.post<any>(this.chatApiUrl, payload).subscribe({
        next: (response) => {
          this.isChatLoading = false;
          this.removeChatMessage(loadingMessage.id);
          const aiResponse = this.extractChatResponse(response);
          this.addChatMessage(aiResponse, false);
        },
        error: (error) => {
          this.isChatLoading = false;
          this.removeChatMessage(loadingMessage.id);
          this.addChatMessage('Error contacting AI service.', false);
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

  /**
   * Collect all PDF URLs from loaded lessons
   */
  private collectCoursePdfUrls(): string[] {
    const urls: string[] = [];
    this.lessons.forEach((lesson: any) => {
      (lesson.chapters || []).forEach((chapter: any) => {
        (chapter.courses || []).forEach((course: any) => {
          if (course.pdf) {
            // course.pdf is a relative path like /fileCourses/xyz.pdf
            const full = `https://localhost:8002${course.pdf}`;
            if (!urls.includes(full)) urls.push(full);
          }
        });
      });
    });
    return urls;
  }

  /**
   * Build a single concatenated PDF text context (truncated if necessary)
   */
  private buildPdfContext(): void {
    const pdfUrls = this.collectCoursePdfUrls();
    if (pdfUrls.length === 0) {
      this.pdfContext = '';
      this.pdfContextReady = true;
      return;
    }

    this.pdfContextLoading = true;

    const requests = pdfUrls.map(url =>
      this.http.post<{ content: string }>(
        'https://localhost:8002/api/extract-pdf-content/',
        { pdf_url: url },
        { withCredentials: true }
      ).pipe(
        map(res => ({ url, content: res.content || '' })),
        catchError(err => {
          console.warn('PDF extract failed for', url, err);
            return of({ url, content: '[Content unavailable]' });
        })
      )
    );

    forkJoin(requests).subscribe({
      next: results => {
        // Concatenate with simple headers
        let combined = '';
        for (const r of results) {
          const header = `\n===== SOURCE: ${r.url.split('/').pop()} =====\n`;
          if ((combined + header + r.content).length > this.pdfContextMaxChars) {
            const remaining = this.pdfContextMaxChars - combined.length - header.length - 20;
            if (remaining > 0) {
              combined += header + r.content.slice(0, remaining) + '\n...[TRUNCATED]...\n';
            }
            break;
          } else {
            combined += header + r.content;
          }
        }
        this.pdfContext = combined.trim();
        this.pdfContextReady = true;
        this.pdfContextLoading = false;
      },
      error: err => {
        console.error('Failed building PDF context', err);
        this.pdfContext = '';
        this.pdfContextReady = true;
        this.pdfContextLoading = false;
      }
    });
  }
}



