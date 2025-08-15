import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { isPlatformBrowser } from '@angular/common';

export interface LoginResponse {
  message: string;
  user_type: string;
  user_id: number;
  username: string;
  token: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = '/api/users';  // relative same-origin path
  private currentUserSubject = new BehaviorSubject<any>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  private isBrowser: boolean;

  constructor(
    private http: HttpClient,
    private router: Router,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    // Check if user is already logged in from localStorage
    if (this.isBrowser) {
      const savedUser = localStorage.getItem('currentUser');
      if (savedUser) {
        this.currentUserSubject.next(JSON.parse(savedUser));
      }
    }
  }

  login(username: string, password: string, rememberMe: boolean = false): Observable<LoginResponse> {
    const credentials = { username, password };
    return this.http.post<LoginResponse>(`${this.apiUrl}/login/`, credentials, {
      withCredentials: true
    }).pipe(
      tap(response => {
        if (this.isBrowser) {
          // Always store in localStorage regardless of rememberMe option
          localStorage.setItem('currentUser', JSON.stringify({
            user_id: response.user_id,
            user_type: response.user_type,
            username: response.username
          }));
        }
        this.currentUserSubject.next(response);
      })
    );
  }

  logout(): void {
    if (this.isBrowser) {
      localStorage.removeItem('currentUser');
      sessionStorage.removeItem('currentUser'); // Clean up any old sessionStorage
    }
    this.currentUserSubject.next(null);
    
    // Call logout endpoint to clear server-side session
    this.http.post(`${this.apiUrl}/logout/`, {}, { withCredentials: true })
      .subscribe(() => {
        this.router.navigate(['/auth']);
      });
  }

  isLoggedIn(): boolean {
    return this.currentUserSubject.value !== null;
  }

  getCurrentUser(): any {
    return this.currentUserSubject.value;
  }

  getAuthHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json'
    });
  }
}