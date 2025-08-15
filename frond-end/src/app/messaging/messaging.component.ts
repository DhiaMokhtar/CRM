import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { MessagingService } from '../services/messaging.service';
import { AuthService } from '../services/auth.service';
import { Conversation, Message, User } from '../api.service';
import { Subscription } from 'rxjs';
import { environment } from '../../environments/environment';

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
        if (user) {
          this.loadConversations();
        }
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

  loadConversations(): void {
    this.messagingService.loadConversations();
  }

  selectConversation(conversation: Conversation): void {
    console.log('Selecting conversation:', conversation);
    this.messagingService.selectConversation(conversation);
    this.showNewConversation = false;
    this.selectedRecipient = null; // Clear any selected recipient
    this.searchQuery = '';
    this.searchResults = [];
    this.messageContent = ''; // Clear message content
  }

  startNewConversation(): void {
    console.log('Starting new conversation...');
    this.showNewConversation = true;
    this.selectedConversation = null; // Clear any existing conversation
    this.messages = [];
    this.searchQuery = '';
    this.searchResults = [];
    this.selectedRecipient = null;
    this.messageContent = ''; // Clear any existing message content
    
    console.log('New conversation state:', {
      showNewConversation: this.showNewConversation,
      selectedConversation: this.selectedConversation,
      selectedRecipient: this.selectedRecipient
    });
  }

  searchUsers(): void {
    if (this.searchQuery.trim().length > 2) {
      console.log('Searching for:', this.searchQuery); // Debug log
      console.log('Using messaging service URL:', environment.messagingServiceUrl); // Debug log
      
      this.messagingService.searchUsers(this.searchQuery).subscribe({
        next: (users) => {
          console.log('Raw search results:', users); // Debug log
          console.log('Number of results:', users.length); // Debug log
          
          // Filter out current user
          this.searchResults = users.filter(user => 
            !(user.type === this.currentUser?.user_type && user.id === this.currentUser?.user_id)
          );
          
          console.log('Filtered search results:', this.searchResults); // Debug log
        },
        error: (error) => {
          console.error('Error searching users:', error);
          console.error('Full error object:', JSON.stringify(error, null, 2)); // More detailed error
          this.searchResults = [];
        }
      });
    } else {
      this.searchResults = [];
    }
  }

  selectRecipient(user: User): void {
    console.log('Selecting recipient:', user);
    this.selectedRecipient = user;
    this.selectedConversation = null; // Clear any existing conversation
    this.messages = []; // Clear messages from previous conversation
    this.searchResults = [];
    this.searchQuery = user.name || user.username;
    
    console.log('Recipient selection state:', {
      selectedRecipient: this.selectedRecipient,
      selectedConversation: this.selectedConversation,
      showNewConversation: this.showNewConversation
    });
    
    // Focus on message input after recipient selection
    setTimeout(() => {
      if (this.messageInput) {
        this.messageInput.nativeElement.focus();
      }
    }, 100);
  }

  sendMessage(): void {
    if (!this.messageContent.trim()) {
      return;
    }

    console.log('Sending message...');
    console.log('Selected conversation:', this.selectedConversation);
    console.log('Selected recipient:', this.selectedRecipient);
    console.log('Show new conversation:', this.showNewConversation);

    if (this.showNewConversation && this.selectedRecipient) {
      // Starting new conversation - this should take priority
      console.log('Starting new conversation with:', this.selectedRecipient);
      this.messagingService.createMessage(
        this.selectedRecipient.type,
        this.selectedRecipient.id,
        this.messageContent.trim()
      ).subscribe({
        next: (response) => {
          console.log('New conversation message sent successfully:', response);
          this.messageContent = '';
          this.selectedRecipient = null;
          this.showNewConversation = false;
          this.selectedConversation = null; // Clear any existing conversation
          this.loadConversations(); // Refresh conversations
        },
        error: (error) => {
          console.error('Error sending new conversation message:', error);
        }
      });
    } else if (this.selectedConversation && !this.showNewConversation) {
      // Sending to existing conversation
      console.log('Sending to existing conversation:', this.selectedConversation.id);
      this.messagingService.sendMessage(
        this.selectedConversation.id,
        this.messageContent.trim()
      ).subscribe({
        next: (response) => {
          console.log('Existing conversation message sent successfully:', response);
          this.messageContent = '';
          this.messagingService.loadConversationMessages(this.selectedConversation!.id);
        },
        error: (error) => {
          console.error('Error sending existing conversation message:', error);
        }
      });
    } else {
      console.error('No recipient or conversation selected');
    }
  }

  markAsRead(message: Message): void {
    if (!message.is_read && this.isRecipient(message)) {
      this.messagingService.markMessageAsRead(message.id);
    }
  }

  isRecipient(message: Message): boolean {
    return message.recipient_type === this.currentUser?.user_type && 
           message.recipient_id === this.currentUser?.user_id;
  }

  isSender(message: Message): boolean {
    return message.sender_type === this.currentUser?.user_type && 
           message.sender_id === this.currentUser?.user_id;
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

  debugState(): void {
    console.log('=== Debug State ===');
    console.log('showNewConversation:', this.showNewConversation);
    console.log('selectedConversation:', this.selectedConversation);
    console.log('selectedRecipient:', this.selectedRecipient);
    console.log('messageContent:', this.messageContent);
    console.log('===================');
  }
}
