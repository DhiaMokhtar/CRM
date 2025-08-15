import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';

interface Schedule {
  id: number;
  title: string;
  description: string;
  schedule_type: string;
  classroom_name: string;
  teacher_name: string;
  lesson_title: string;
  start_datetime: string;
  end_datetime: string;
  is_recurring: boolean;
  recurrence_pattern: string;
}

@Component({
  selector: 'app-calendar',
  standalone: false,
  templateUrl: './calendar.component.html',
  styleUrls: ['./calendar.component.scss']
  // REMOVE standalone: true if present
})
export class CalendarComponent implements OnInit {
  schedules: Schedule[] = [];
  currentDate = new Date();
  currentView = 'month'; // 'week' or 'month'
  currentUser: any;
  isAdmin = false;
  showAddScheduleModal = false;
  
  newSchedule = {
    title: '',
    description: '',
    schedule_type: 'class',
    classroom: '',
    teacher: '',
    lesson: '',
    start_datetime: '',
    end_datetime: '',
    is_recurring: false,
    recurrence_pattern: '',
    user_type : " ",
    user_id : " "
  };
  
  classrooms: any[] = [];
  teachers: any[] = [];
  lessons: any[] = [];
  
  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}
  
  ngOnInit(): void {
    this.currentUser = this.authService.getCurrentUser();
    this.isAdmin = this.currentUser?.user_type === 'admin';
    this.loadSchedules();
    
    if (this.isAdmin) {
      this.loadClassrooms();
      this.loadTeachers();
      this.loadLessons();
    }
  }
  
  loadSchedules(): void {
    if (this.currentView === 'week') {
      const weekStart = this.getWeekStart();
      this.apiService.getSchedulesWeekly(weekStart).subscribe({
        next: (response) => {
          this.schedules = response.schedules || response;
        },
        error: (error) => {
          console.error('Error loading weekly schedules:', error);
        }
      });
    } else {
      const year = this.currentDate.getFullYear().toString();
      const month = (this.currentDate.getMonth() + 1).toString();
      this.apiService.getSchedulesMonthly(year, month).subscribe({
        next: (response) => {
          this.schedules = response.schedules || response;
        },
        error: (error) => {
          console.error('Error loading monthly schedules:', error);
        }
      });
    }
  }
  
  loadClassrooms(): void {
    // Use the correct microservice method
    this.apiService.getClasses().subscribe({
      next: (data) => this.classrooms = data,
      error: (error) => console.error('Error loading classrooms:', error)
    });
  }
  
  loadTeachers(): void {
    // Use the correct microservice method
    this.apiService.getTeachers().subscribe({
      next: (data) => this.teachers = data,
      error: (error) => console.error('Error loading teachers:', error)
    });
  }
  
  loadLessons(): void {
    // Use the correct microservice method - get all lessons without filtering by classroom
    this.apiService.getLessons().subscribe({
      next: (data) => this.lessons = data,
      error: (error) => console.error('Error loading lessons:', error)
    });
  }
  
  getWeekStart(): string {
    const date = new Date(this.currentDate);
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    date.setDate(diff);
    return date.toISOString().split('T')[0];
  }
  
  previousPeriod(): void {
    if (this.currentView === 'week') {
      this.currentDate.setDate(this.currentDate.getDate() - 7);
    } else {
      this.currentDate.setMonth(this.currentDate.getMonth() - 1);
    }
    this.loadSchedules();
  }
  
  nextPeriod(): void {
    if (this.currentView === 'week') {
      this.currentDate.setDate(this.currentDate.getDate() + 7);
    } else {
      this.currentDate.setMonth(this.currentDate.getMonth() + 1);
    }
    this.loadSchedules();
  }
  
  switchView(view: string): void {
    this.currentView = view;
    this.loadSchedules();
  }
  
  openAddScheduleModal(): void {
    this.showAddScheduleModal = true;
  }
  
  closeAddScheduleModal(): void {
    this.showAddScheduleModal = false;
    this.resetNewSchedule();
  }
  
  addSchedule() {
    const current = localStorage.getItem('currentUser');
    if (current) {
      const currentUser = JSON.parse(current);
      this.newSchedule.user_type = currentUser.user_type;
      this.newSchedule.user_id = currentUser.user_id;
      
      // Convert string values to integers for foreign keys
      const payload = {
        ...this.newSchedule,
        classroom_id: this.newSchedule.classroom ? parseInt(this.newSchedule.classroom, 10) : null,
        teacher_id: this.newSchedule.teacher ? parseInt(this.newSchedule.teacher, 10) : null,
        lesson_id: this.newSchedule.lesson ? parseInt(this.newSchedule.lesson, 10) : null,
      };
      
      console.log('Schedule payload:', payload);
      
      this.apiService.createSchedule(payload).subscribe({
        next: (response) => {
          console.log('Schedule created successfully:', response);
          this.loadSchedules();
          this.closeAddScheduleModal();
        },
        error: (error) => {
          console.error('Error adding schedule:', error);
          alert('Failed to create schedule. Please try again.');
        }
      });
    }
  }
  
  resetNewSchedule(): void {
    this.newSchedule = {
      title: '',
      description: '',
      schedule_type: 'class',
      classroom: '',
      teacher: '',
      lesson: '',
      start_datetime: '',
      end_datetime: '',
      is_recurring: false,
      recurrence_pattern: '',
      user_type : " ",
      user_id : ' '
    };
  }
  
  goBackToDashboard(): void {
    switch (this.currentUser?.user_type) {
      case 'administrator':
        this.router.navigate(['/administrator']);
        break;
      case 'teacher':
        this.router.navigate(['/teacher']);
        break;
      case 'student':
        this.router.navigate(['/student']);
        break;
      case 'parent':
        this.router.navigate(['/parent']);
        break;
      default:
        this.router.navigate(['/auth']);
    }
  }
  
  formatTime(datetime: string): string {
    return new Date(datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  formatDate(datetime: string): string {
    return new Date(datetime).toLocaleDateString();
  }
  submitSchedule() {
    const user_id = localStorage.getItem('user_id');
    console.log('User ID being sent:', user_id); // Add this line
  }
}

