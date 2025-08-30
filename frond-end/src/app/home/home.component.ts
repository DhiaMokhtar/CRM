import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: false,
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
})
export class HomeComponent {
  @ViewChild('featuresSection') featuresSection!: ElementRef;

  features = [
    {
      icon: 'fas fa-users',
      title: 'User Management',
      description: 'Efficiently manage students, teachers, parents, and administrators in one centralized system.'
    },
    {
      icon: 'fas fa-calendar-alt',
      title: 'Calendar Integration',
      description: 'Keep track of important dates, events, and schedules with our integrated calendar system.'
    },
    {
      icon: 'fas fa-comments',
      title: 'Messaging System',
      description: 'Seamless communication between all stakeholders with our built-in messaging platform.'
    },
    {
      icon: 'fas fa-robot',
      title: 'AI Chatbot',
      description: 'Get instant help and answers with our intelligent chatbot assistant.'
    },
    {
      icon: 'fas fa-chart-bar',
      title: 'Analytics & Reports',
      description: 'Generate comprehensive reports and gain insights with advanced analytics.'
    },
    {
      icon: 'fas fa-shield-alt',
      title: 'Secure & Reliable',
      description: 'Your data is protected with enterprise-grade security and reliability.'
    }
  ];

  roles = [
    {
      title: 'Administrator',
      description: 'Manage the entire system and oversee all operations',
      icon: 'fas fa-user-shield',
      route: '/auth'
    },
    {
      title: 'Teacher',
      description: 'Access teaching tools and student management',
      icon: 'fas fa-chalkboard-teacher',
      route: '/auth'
    },
    {
      title: 'Student',
      description: 'View courses, assignments, and academic progress',
      icon: 'fas fa-user-graduate',
      route: '/auth'
    },
    {
      title: 'Parent',
      description: 'Monitor your child\'s academic progress and activities',
      icon: 'fas fa-user-friends',
      route: '/auth'
    }
  ];

  constructor(private router: Router) {}

  scrollToFeatures() {
    this.featuresSection.nativeElement.scrollIntoView({ 
      behavior: 'smooth' 
    });
  }

  navigateToRole(route: string) {
    // All role cards now navigate to the authentication page
    this.router.navigate(['/auth']);
  }
}
