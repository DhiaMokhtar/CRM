import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class HttpsInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Only skip HTTPS upgrade for LM Studio server (chatbot)
    if (req.url.startsWith('http://localhost:1234/')) {
      return next.handle(req);
    }
    
    // Convert all other requests to HTTPS (including courses microservice)
    const httpsReq = req.clone({
      url: req.url.replace('http://', 'https://'),
      setHeaders: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    return next.handle(httpsReq);
  }
}