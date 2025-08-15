import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AdministratorComponent } from './administrator/administrator.component';
import { AuthenticationComponent } from './authentication/authentication.component';
import { StudentComponent } from './student/student.component';
import { TeacherComponent } from './teacher/teacher.component';
import { ParentComponent } from './parent/parent.component';
import { MessagingComponent } from './messaging/messaging.component';
import { CalendarComponent } from './calendar/calendar.component';
import { AuthGuard } from './guards/auth.guard';

const routes: Routes = [
  { path: '', redirectTo: 'auth', pathMatch: 'full'},
  { path: 'auth', component: AuthenticationComponent },
  { path: 'admin', component: AdministratorComponent, canActivate: [AuthGuard] },
  { path: 'student', component: StudentComponent, canActivate: [AuthGuard] },
  { path: 'teacher', component: TeacherComponent, canActivate: [AuthGuard] },
  { path: 'parent', component: ParentComponent, canActivate: [AuthGuard] },
  { path: 'messages', component: MessagingComponent, canActivate: [AuthGuard] },
  { path: 'calendar', component: CalendarComponent, canActivate: [AuthGuard] },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
