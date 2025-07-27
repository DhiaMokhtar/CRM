import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

// Add messaging interfaces
export interface Message {
  id: number;
  sender_type: string;
  sender_id: number;
  recipient_type: string;
  recipient_id: number;
  content: string;
  is_read: boolean;
  created_at: string;
  created_at_formatted: string;
  sender_name: string;
  recipient_name: string;
}

export interface Conversation {
  id: number;
  participant1_type: string;
  participant1_id: number;
  participant2_type: string;
  participant2_id: number;
  participant1_name: string;
  participant2_name: string;
  last_message_content: string;
  last_message_time: string;
  updated_at: string;
  unread_count: number;
}

export interface Teacher {
  id: number;
  username: string;
  password?: string;
  email: string;
  class_ids?: number[];
}

export interface Student {
  id: number;
  username: string;
  password: string;
  email: string;
  class_id?: number; // Added for class association
}

export interface Class {
  id: number;
  name: string;
}

export interface Parent {
  id: number;
  username: string;
  password?: string;
  email: string;
  students:any;
}

interface Course {
  id: number;
  title: string;
  chapter: number;
  pdf: string;  // This is a relative path like /media/courses/pdfs/example.pdf
}

export interface Lesson {
  id: number;
  title: string;
  description: string;
  class_room: number;
  chapters: Chapter[];
  
}

export interface Chapter {
  id: number;
  title: string;
  description: string;
  lesson: number;
  order: number;
  materials: CourseMaterial[];
  isAddingContent?: boolean;
  selectedFile?: File;
}

export interface CourseMaterial {
  id: number;
  title: string;
  pdf: string;
  chapter: number;
}

export interface HomeworkSubmission {
  id: number;
  homework: number;
  student: number;
  file: string;
  submission_date: string;
  comments?: string;
}

export interface Homework {
  id: number;
  title: string;
  description: string;
  classroom: number;
  teacher: number;
  teacher_name?: string;
  due_date: string;
  created_at: string;
  submission?: HomeworkSubmission;
  selectedFile?: File;
  comments?: string;
}

export interface User {
  id: number;
  username: string;
  type: string;
  class_name?: string;
}


export interface Subject {
  id: number;
  name: string;
  classroom: number;
  classroom_name?: string;
  teacher?: number;
  teacher_name?: string;
  created_at: string;
}

export interface Grade {
  id: number;
  student: number;
  student_name?: string;
  subject: number;
  subject_name?: string;
  grade_type: string;
  score: number;
  max_score: number;
  percentage: number;
  date_recorded: string;
  notes?: string;
  recorded_by: number;
  recorded_by_name?: string;
}

export interface GradeTable {
  classroom_id: number;
  classroom_name: string;
  subjects: Subject[];
  students: Student[];
  grades: { [studentId: number]: { [subjectId: number]: Grade[] } };
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiUrl;
  private usersServiceUrl = environment.usersServiceUrl;
  private coursesServiceUrl = environment.coursesServiceUrl;
  private messagingServiceUrl = environment.messagingServiceUrl;
  private classUrl = `${this.usersServiceUrl}/classes/`;

  constructor(private http: HttpClient) {}

  // Messaging methods (use messaging microservice)
  getConversations(): Observable<Conversation[]> {
    return this.http.get<Conversation[]>(`${this.messagingServiceUrl}/conversations/`, { withCredentials: true });
  }

  getMessages(): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.messagingServiceUrl}/messages/`, { withCredentials: true });
  }

  getConversationMessages(conversationId: number): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.messagingServiceUrl}/conversations/${conversationId}/messages/`, { withCredentials: true });
  }

  sendMessage(message: { recipient_type: string, recipient_id: number, content: string }): Observable<Message> {
    return this.http.post<Message>(`${this.messagingServiceUrl}/messages/`, message, { withCredentials: true });
  }

  markMessageAsRead(messageId: number): Observable<any> {
    return this.http.post(`${this.messagingServiceUrl}/messages/${messageId}/mark_as_read/`, {}, { withCredentials: true });
  }

  searchUsers(query: string, type?: string): Observable<User[]> {
    let params = `q=${query}`;
    console.log("params :"+params);
    if (type) {
      params += `&type=${type}`;
    }
    return this.http.get<User[]>(`${this.messagingServiceUrl}/search-users/?${params}`, { withCredentials: true });
  }

  // User management methods (use users microservice)
  getTeachers(): Observable<Teacher[]> {
    return this.http.get<Teacher[]>(`${this.usersServiceUrl}/teachers/`, { withCredentials: true });
  }

  addTeacher(teacher: Partial<Teacher>): Observable<Teacher> {
    return this.http.post<Teacher>(`${this.usersServiceUrl}/teachers/`, teacher, { withCredentials: true });
  }

  updateTeacher(teacher: Teacher): Observable<Teacher> {
    return this.http.put<Teacher>(`${this.usersServiceUrl}/teachers/${teacher.id}/`, teacher, { withCredentials: true });
  }

  deleteTeacher(id: number): Observable<void> {
    return this.http.delete<void>(`${this.usersServiceUrl}/teachers/${id}/`, { withCredentials: true });
  }

  getStudents(): Observable<Student[]> {
    return this.http.get<Student[]>(`${this.usersServiceUrl}/students/`, { withCredentials: true });
  }

  addStudent(student: Partial<Student>): Observable<Student> {
    return this.http.post<Student>(`${this.usersServiceUrl}/students/`, student, { withCredentials: true });
  }

  updateStudent(student: Student): Observable<Student> {
    return this.http.put<Student>(`${this.usersServiceUrl}/students/${student.id}/`, student, { withCredentials: true });
  }

  deleteStudent(id: number): Observable<void> {
    return this.http.delete<void>(`${this.usersServiceUrl}/students/${id}/`, { withCredentials: true });
  }

  getParents(): Observable<Parent[]> {
    return this.http.get<Parent[]>(`${this.usersServiceUrl}/parents/`, { withCredentials: true });
  }

  addParent(parent: Partial<Parent>): Observable<Parent> {
    return this.http.post<Parent>(`${this.usersServiceUrl}/parents/`, parent, { withCredentials: true });
  }

  updateParent(parent: Parent): Observable<Parent> {
    return this.http.put<Parent>(`${this.usersServiceUrl}/parents/${parent.id}/`, parent, { withCredentials: true });
  }

  deleteParent(id: number): Observable<void> {
    return this.http.delete<void>(`${this.usersServiceUrl}/parents/${id}/`, { withCredentials: true });
  }

  getClasses(): Observable<Class[]> {
    return this.http.get<Class[]>(this.classUrl, { withCredentials: true });
  }

  // Add calendar/schedule methods
  getSchedules(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/schedules/`, { withCredentials: true });
  }

  createSchedule(schedule: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/schedules/`, schedule, { withCredentials: true });
  }

  updateSchedule(id: number, schedule: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/schedules/${id}/`, schedule, { withCredentials: true });
  }

  deleteSchedule(id: number): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/schedules/${id}/`, { withCredentials: true });
  }

  // Fix the get method to accept URL and optional params
  get(url: string, params?: any): Observable<any> {
    const queryParams = params ? new URLSearchParams(params).toString() : '';
    const fullUrl = queryParams ? `${this.baseUrl}/${url}?${queryParams}` : `${this.baseUrl}/${url}`;
    return this.http.get<any>(fullUrl, { withCredentials: true });
  }

  post(url: string, data: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/${url}`, data, { withCredentials: true });
  }

  // Subject methods
  getSubjects(classroomId?: number): Observable<Subject[]> {
    const params = classroomId ? `?classroom=${classroomId}` : '';
    return this.http.get<Subject[]>(`${this.baseUrl}/subjects/${params}`, { withCredentials: true });
  }

  createSubject(subject: Partial<Subject>): Observable<Subject> {
    return this.http.post<Subject>(`${this.baseUrl}/subjects/`, subject, { withCredentials: true });
  }

  updateSubject(id: number, subject: Partial<Subject>): Observable<Subject> {
    return this.http.put<Subject>(`${this.baseUrl}/subjects/${id}/`, subject, { withCredentials: true });
  }

  deleteSubject(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/subjects/${id}/`, { withCredentials: true });
  }

  // Grade methods
  getGrades(params?: any): Observable<Grade[]> {
    const queryParams = new URLSearchParams(params).toString();
    const url = queryParams ? `${this.baseUrl}/grades/?${queryParams}` : `${this.baseUrl}/grades/`;
    return this.http.get<Grade[]>(url, { withCredentials: true });
  }

  createGrade(grade: Partial<Grade>): Observable<Grade> {
    return this.http.post<Grade>(`${this.baseUrl}/grades/`, grade, { withCredentials: true });
  }

  updateGrade(id: number, grade: Partial<Grade>): Observable<Grade> {
    return this.http.put<Grade>(`${this.baseUrl}/grades/${id}/`, grade, { withCredentials: true });
  }

  deleteGrade(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/grades/${id}/`, { withCredentials: true });
  }

  getGradeTable(classroomId: number): Observable<GradeTable> {
    return this.http.get<GradeTable>(`${this.baseUrl}/classes/${classroomId}/grade-table/`, { withCredentials: true });
  }

  createBulkGrades(grades: Partial<Grade>[]): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/grades/bulk-create/`, { grades }, { withCredentials: true });
  }

  // Add method to get class students from microservice
  getClassStudents(classId: number): Observable<Student[]> {
    return this.http.get<Student[]>(`${this.usersServiceUrl}/classes/${classId}/students/`, { withCredentials: true });
  }

  // Add method to get parent children from microservice
  getParentChildren(parentId: number): Observable<Student[]> {
    return this.http.get<Student[]>(`${this.usersServiceUrl}/parents/${parentId}/children/`, { withCredentials: true });
  }

  // Lesson methods (using courses microservice)
  getLessons(classroomId?: number): Observable<Lesson[]> {
    const params = classroomId ? `?classroom=${classroomId}` : '';
    return this.http.get<Lesson[]>(`${this.coursesServiceUrl}/lessons/${params}`, { withCredentials: true });
  }

  createLesson(lesson: Partial<Lesson>): Observable<Lesson> {
    return this.http.post<Lesson>(`${this.coursesServiceUrl}/lessons/`, lesson, { withCredentials: true });
  }

  updateLesson(id: number, lesson: Partial<Lesson>): Observable<Lesson> {
    return this.http.put<Lesson>(`${this.coursesServiceUrl}/lessons/${id}/`, lesson, { withCredentials: true });
  }

  deleteLesson(id: number): Observable<void> {
    return this.http.delete<void>(`${this.coursesServiceUrl}/lessons/${id}/`, { withCredentials: true });
  }

  // Chapter methods (courses microservice)
  getChapters(lessonId: number): Observable<Chapter[]> {
    return this.http.get<Chapter[]>(`${this.coursesServiceUrl}/chapters/?lesson=${lessonId}`, { withCredentials: true });
  }

  createChapter(chapter: Partial<Chapter>): Observable<Chapter> {
    return this.http.post<Chapter>(`${this.coursesServiceUrl}/chapters/`, chapter, { withCredentials: true });
  }

  updateChapter(id: number, chapter: Partial<Chapter>): Observable<Chapter> {
    return this.http.put<Chapter>(`${this.coursesServiceUrl}/chapters/${id}/`, chapter, { withCredentials: true });
  }

  deleteChapter(id: number): Observable<void> {
    return this.http.delete<void>(`${this.coursesServiceUrl}/chapters/${id}/`, { withCredentials: true });
  }

  // Course Material methods (courses microservice)
  getCourseMaterials(chapterId: number): Observable<CourseMaterial[]> {
    return this.http.get<CourseMaterial[]>(`${this.coursesServiceUrl}/courses/?chapter=${chapterId}`, { withCredentials: true });
  }

  createCourseMaterial(formData: FormData): Observable<CourseMaterial> {
    return this.http.post<CourseMaterial>(`${this.coursesServiceUrl}/courses/`, formData, { withCredentials: true });
  }

  deleteCourseMaterial(id: number): Observable<void> {
    return this.http.delete<void>(`${this.coursesServiceUrl}/courses/${id}/`, { withCredentials: true });
  }

  // Student courses (courses microservice)
  getStudentCourses(studentId: number): Observable<any> {
    return this.http.get<any>(`${this.coursesServiceUrl}/students/${studentId}/courses/`, { withCredentials: true });
  }

  // Homework methods (main backend)
  getHomework(params?: any): Observable<Homework[]> {
    const queryParams = params ? new URLSearchParams(params).toString() : '';
    const url = queryParams ? `${this.baseUrl}/homework/?${queryParams}` : `${this.baseUrl}/homework/`;
    return this.http.get<Homework[]>(url, { withCredentials: true });
  }

  createHomework(homework: Partial<Homework>): Observable<Homework> {
    return this.http.post<Homework>(`${this.baseUrl}/homework/`, homework, { withCredentials: true });
  }

  updateHomework(id: number, homework: Partial<Homework>): Observable<Homework> {
    return this.http.put<Homework>(`${this.baseUrl}/homework/${id}/`, homework, { withCredentials: true });
  }

  deleteHomework(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/homework/${id}/`, { withCredentials: true });
  }

  // Homework submission methods (main backend)
  submitHomework(formData: FormData): Observable<HomeworkSubmission> {
    return this.http.post<HomeworkSubmission>(`${this.baseUrl}/homework-submissions/`, formData, { withCredentials: true });
  }

  getHomeworkSubmissions(homeworkId?: number, studentId?: number): Observable<HomeworkSubmission[]> {
    let params = '';
    if (homeworkId) params += `homework=${homeworkId}`;
    if (studentId) params += `${params ? '&' : ''}student=${studentId}`;
    const url = params ? `${this.baseUrl}/homework-submissions/?${params}` : `${this.baseUrl}/homework-submissions/`;
    return this.http.get<HomeworkSubmission[]>(url, { withCredentials: true });
  }

  updateHomeworkSubmission(id: number, submission: Partial<HomeworkSubmission>): Observable<HomeworkSubmission> {
    return this.http.put<HomeworkSubmission>(`${this.baseUrl}/homework-submissions/${id}/`, submission, { withCredentials: true });
  }

  // Class management methods (using microservice)
  createClass(classroom: Partial<Class>): Observable<Class> {
    return this.http.post<Class>(this.classUrl, classroom, { withCredentials: true });
  }

  updateClass(id: number, classroom: Partial<Class>): Observable<Class> {
    return this.http.put<Class>(`${this.classUrl}${id}/`, classroom, { withCredentials: true });
  }

  deleteClass(id: number): Observable<void> {
    return this.http.delete<void>(`${this.classUrl}${id}/`, { withCredentials: true });
  }

  // File upload helper
  uploadFile(file: File, endpoint: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.baseUrl}/${endpoint}/`, formData, { withCredentials: true });
  }
}


