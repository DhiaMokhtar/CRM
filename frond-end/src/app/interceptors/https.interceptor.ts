import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class HttpsInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Clone the request and ensure HTTPS
    const httpsReq = req.clone({
      url: req.url.replace('http://', 'https://'),
      setHeaders: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    return next.handle(httpsReq);
  }
}