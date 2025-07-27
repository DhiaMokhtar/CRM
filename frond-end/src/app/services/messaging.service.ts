import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, interval } from 'rxjs';
import { ApiService, Conversation, Message, User } from '../api.service';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class MessagingService {
  private baseUrl = environment.messagingServiceUrl;  // Use messaging microservice

  private conversationsSubject = new BehaviorSubject<Conversation[]>([]);
  public conversations$ = this.conversationsSubject.asObservable();
  
  private messagesSubject = new BehaviorSubject<Message[]>([]);
  public messages$ = this.messagesSubject.asObservable();
  
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();
  
  private selectedConversationSubject = new BehaviorSubject<Conversation | null>(null);
  public selectedConversation$ = this.selectedConversationSubject.asObservable();
  
  private pollingInterval: any;

  constructor(
    private apiService: ApiService,
    private authService: AuthService
  ) {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.startPolling();
        this.loadConversations();
      } else {
        this.stopPolling();
        this.conversationsSubject.next([]);
        this.messagesSubject.next([]);
        this.unreadCountSubject.next(0);
      }
    });
  }

  loadConversations(): void {
    this.apiService.getConversations().subscribe({
      next: (conversations) => {
        this.conversationsSubject.next(conversations);
        this.updateUnreadCount(conversations);
      },
      error: (error) => {
        console.error('Error loading conversations:', error);
      }
    });
  }

  loadConversationMessages(conversationId: number): void {
    this.apiService.getConversationMessages(conversationId).subscribe({
      next: (messages) => {
        this.messagesSubject.next(messages);
        const conversations = this.conversationsSubject.value;
        const conversation = conversations.find(c => c.id === conversationId);
        if (conversation) {
          this.selectedConversationSubject.next(conversation);
        }
      },
      error: (error) => {
        console.error('Error loading messages:', error);
      }
    });
  }

  // For existing conversations
  sendMessage(conversationId: number, content: string): Observable<any> {
    // Get the current selected conversation to determine the recipient
    const selectedConversation = this.selectedConversationSubject.value;
    if (!selectedConversation) {
      throw new Error('No conversation selected');
    }

    // Determine the recipient by checking which participant is NOT the current user
    const currentUser = this.authService.getCurrentUser();
    let recipientType: string;
    let recipientId: number;

    if (selectedConversation.participant1_type === currentUser?.user_type && 
        selectedConversation.participant1_id === currentUser?.user_id) {
      // Current user is participant1, so recipient is participant2
      recipientType = selectedConversation.participant2_type;
      recipientId = selectedConversation.participant2_id;
    } else {
      // Current user is participant2, so recipient is participant1
      recipientType = selectedConversation.participant1_type;
      recipientId = selectedConversation.participant1_id;
    }

    return this.apiService.sendMessage({
      recipient_type: recipientType,
      recipient_id: recipientId,
      content: content
    });
  }

  // For new conversations
  createMessage(recipientType: string, recipientId: number, content: string): Observable<any> {
    return this.apiService.sendMessage({
      recipient_type: recipientType,
      recipient_id: recipientId,
      content: content
    });
  }

  searchUsers(query: string, type?: string): Observable<User[]> {
    return this.apiService.searchUsers(query, type);
  }

  markMessageAsRead(messageId: number): void {
    this.apiService.markMessageAsRead(messageId).subscribe({
      next: () => {
        const currentMessages = this.messagesSubject.value;
        const updatedMessages = currentMessages.map(msg => 
          msg.id === messageId ? { ...msg, is_read: true } : msg
        );
        this.messagesSubject.next(updatedMessages);
        this.loadConversations();
      },
      error: (error) => {
        console.error('Error marking message as read:', error);
      }
    });
  }

  selectConversation(conversation: Conversation): void {
    this.selectedConversationSubject.next(conversation);
    this.loadConversationMessages(conversation.id);
  }

  private startPolling(): void {
    this.pollingInterval = interval(5000).subscribe(() => {
      this.loadConversations();
      const selectedConversation = this.selectedConversationSubject.value;
      if (selectedConversation) {
        this.loadConversationMessages(selectedConversation.id);
      }
    });
  }

  private stopPolling(): void {
    if (this.pollingInterval) {
      this.pollingInterval.unsubscribe();
      this.pollingInterval = null;
    }
  }

  private updateUnreadCount(conversations: Conversation[]): void {
    const totalUnread = conversations.reduce((sum, conv) => sum + conv.unread_count, 0);
    this.unreadCountSubject.next(totalUnread);
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }
}