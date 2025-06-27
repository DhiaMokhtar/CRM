import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { MessagingService } from '../services/messaging.service';
import { AuthService } from '../services/auth.service';
import { Conversation, Message, User } from '../api.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-messaging',
  standalone: false,
  templateUrl: './messaging.component.html',
  styleUrl: './messaging.component.scss'
})
export class MessagingComponent implements OnInit, OnDestroy {
  @ViewChild('messageInput') messageInput!: ElementRef;
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  conversations: Conversation[] = [];
  messages: Message[] = [];
  selectedConversation: Conversation | null = null;
  currentUser: any = null;
  unreadCount = 0;
  
  // New conversation
  showNewConversation = false;
  searchQuery = '';
  searchResults: User[] = [];
  selectedRecipient: User | null = null;
  
  // Message input
  messageContent = '';
  
  private subscriptions: Subscription[] = [];

  constructor(
    private messagingService: MessagingService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Subscribe to current user
    this.subscriptions.push(
      this.authService.currentUser$.subscribe(user => {
        this.currentUser = user;
        
      })
    );

    
    // Subscribe to conversations
    this.subscriptions.push(
      this.messagingService.conversations$.subscribe(conversations => {
        
        this.conversations = conversations;
        
      })
    );
    // Subscribe to messages
    this.subscriptions.push(
      this.messagingService.messages$.subscribe(messages => {
        this.messages = messages;
        setTimeout(() => this.scrollToBottom(), 100);
      })
    );

    // Subscribe to selected conversation
    this.subscriptions.push(
      this.messagingService.selectedConversation$.subscribe(conversation => {
        this.selectedConversation = conversation;
      })
    );

    // Subscribe to unread count
    this.subscriptions.push(
      this.messagingService.unreadCount$.subscribe(count => {
        this.unreadCount = count;
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  selectConversation(conversation: Conversation): void {
    this.messagingService.selectConversation(conversation);
    this.showNewConversation = false;
  }

  startNewConversation(): void {
    this.showNewConversation = true;
    this.selectedConversation = null;
    this.messages = [];
    this.searchQuery = '';
    this.searchResults = [];
    this.selectedRecipient = null;
  }

  searchUsers(): void {
    if (this.searchQuery.trim().length > 2) {
      this.messagingService.searchUsers(this.searchQuery).subscribe({
        next: (users) => {
          // Filter out current user
          this.searchResults = users.filter(user => 
            !(user.type === this.currentUser?.userType && user.id === this.currentUser?.userId)
          );
        },
        error: (error) => {
          console.error('Error searching users:', error);
        }
      });
    } else {
      this.searchResults = [];
    }
  }

  selectRecipient(user: User): void {
    this.selectedRecipient = user;
    this.searchResults = [];
    this.searchQuery = user.username;
  }

  sendMessage(): void {
    if (!this.messageContent.trim()) {
      return;
    }

    let recipientType: string;
    let recipientId: number;

    if (this.showNewConversation && this.selectedRecipient) {
      // New conversation
      recipientType = this.selectedRecipient.type;
      recipientId = this.selectedRecipient.id;
    } else if (this.selectedConversation) {
      // Existing conversation
      const currentUserType = this.currentUser?.user_type;
      const currentUserId = this.currentUser?.user_id;
      
      if (this.selectedConversation.participant1_type === currentUserType && 
          this.selectedConversation.participant1_id === currentUserId) {
        recipientType = this.selectedConversation.participant2_type;
        recipientId = this.selectedConversation.participant2_id;
      } else {
        recipientType = this.selectedConversation.participant1_type;
        recipientId = this.selectedConversation.participant1_id;
      }
    } else {
      return;
    }

    this.messagingService.sendMessage(recipientType, recipientId, this.messageContent).subscribe({
      next: (message) => {
        this.messageContent = '';
        if (this.showNewConversation) {
          this.showNewConversation = false;
          // The conversation list will be refreshed automatically
        }
      },
      error: (error) => {
        console.error('Error sending message:', error);
      }
    });
  }

  markAsRead(message: Message): void {
    if (!message.is_read && this.isRecipient(message)) {
      this.messagingService.markMessageAsRead(message.id);
    }
  }

  isRecipient(message: Message): boolean {
    return message.recipient_type === this.currentUser?.userType && 
           message.recipient_id === this.currentUser?.userId;
  }

  isSender(message: Message): boolean {
    return message.sender_type === this.currentUser?.userType && 
           message.sender_id === this.currentUser?.userId;
  }

  getConversationPartnerName(conversation: Conversation): string {
    const currentUserType = this.currentUser?.user_type;
    const currentUserId = this.currentUser?.user_id;
    
    if (conversation.participant1_type === currentUserType && 
        conversation.participant1_id === currentUserId) {
      return conversation.participant2_name;
    } else {
      return conversation.participant1_name;
    }
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString();
    }
  }

  private scrollToBottom(): void {
    if (this.messagesContainer) {
      this.messagesContainer.nativeElement.scrollTop = this.messagesContainer.nativeElement.scrollHeight;
    }
  }

  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  goBackToDashboard(): void {
    if (this.currentUser) {
      switch (this.currentUser.user_type) {
        case 'administrator':
          this.router.navigate(['/admin']);
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
          break;
      }
    } else {
      this.router.navigate(['/auth']);
    }
  }
}
