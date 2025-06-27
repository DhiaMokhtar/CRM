import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-authentication',
  standalone: false,
  templateUrl: './authentication.component.html',
  styleUrl: './authentication.component.scss'
})
export class AuthenticationComponent implements OnInit {
  username = '';
  password = '';
  rememberMe = false;
  isLoading = false;
  errorMessage = '';

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit() {
    // Check for stored user session first
    if (typeof window !== 'undefined') {
      const storedUser = localStorage.getItem('currentUser');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        // Ensure the session is restored to AuthService
        if (!this.authService.isLoggedIn()) {
          // Access the private property using bracket notation
          (this.authService as any)['currentUserSubject'].next(user);
        }
        this.redirectBasedOnUserType(user.user_type, user.user_id.toString());
        return;
      }
    }
    
    // Fallback check if already logged in
    if (this.authService.isLoggedIn()) {
      const user = this.authService.getCurrentUser();
      this.redirectBasedOnUserType(user.user_type, user.user_id.toString());
    }
  }

  onRememberMeChange(event: any) {
    this.rememberMe = event.target.checked;
  }

  redirectBasedOnUserType(userType: string, userId: string) {
    switch(userType) {
      case 'admin':
        this.router.navigate(['/admin']);
        break;
      case 'student':
        this.router.navigate(['/student']);
        break;
      case 'teacher':
        this.router.navigate(['/teacher']);
        break;
      case 'parent':
        this.router.navigate(['/parent']);
        break;
    }
  }

  onLogin() {
    if (!this.username || !this.password) {
      this.errorMessage = 'Please enter both username and password';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.login(this.username, this.password, this.rememberMe).subscribe({
      next: (response) => {
        console.log('Login successful:', response);
        this.redirectBasedOnUserType(response.user_type, response.user_id.toString());
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = err.error?.error || 'Login failed. Please try again.';
        this.isLoading = false;
      }
    });
  }
}
