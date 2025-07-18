import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class HttpsInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Skip HTTPS upgrade for LM Studio server
    if (req.url.startsWith('http://localhost:1234/')) {
      return next.handle(req);
    }
    // Clone the request and ensure HTTPS for other URLs
    const httpsReq = req.clone({
      url: req.url.replace('http://', 'https://'),
      setHeaders: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    return next.handle(httpsReq);
  }
}