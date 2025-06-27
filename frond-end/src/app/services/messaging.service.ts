import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, interval } from 'rxjs';
import { ApiService, Conversation, Message, User } from '../api.service';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class MessagingService {
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
    // Start polling for new messages when user is logged in
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
        // Find and update the selected conversation
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

  sendMessage(recipientType: string, recipientId: number, content: string): Observable<Message> {
    const messageData = {
      recipient_type: recipientType,
      recipient_id: recipientId,
      content: content
    };

    return new Observable(observer => {
      this.apiService.sendMessage(messageData).subscribe({
        next: (message) => {
          // Add the new message to the current messages
          const currentMessages = this.messagesSubject.value;
          this.messagesSubject.next([...currentMessages, message]);
          
          // Refresh conversations to update last message
          this.loadConversations();
          
          observer.next(message);
          observer.complete();
        },
        error: (error) => {
          observer.error(error);
        }
      });
    });
  }

  searchUsers(query: string, type?: string): Observable<User[]> {
    return this.apiService.searchUsers(query, type);
  }

  markMessageAsRead(messageId: number): void {
    this.apiService.markMessageAsRead(messageId).subscribe({
      next: () => {
        // Update the message in the current messages list
        const currentMessages = this.messagesSubject.value;
        const updatedMessages = currentMessages.map(msg => 
          msg.id === messageId ? { ...msg, is_read: true } : msg
        );
        this.messagesSubject.next(updatedMessages);
        
        // Refresh conversations to update unread count
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
    // Poll for new messages every 5 seconds
    this.pollingInterval = interval(5000).subscribe(() => {
      this.loadConversations();
      
      // If a conversation is selected, refresh its messages
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