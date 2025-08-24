from typing import Optional, Sequence, Literal

from mods.origins import compute_local_origins, normalize_origins
from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class TrustedOriginMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: Optional[Sequence[str]] = None,
        port: Optional[int] = None,
    ) -> None:
        self.allowed_origins: set[str] = set()

        local_origins = compute_local_origins(port)
        self.allowed_origins.update(local_origins)

        if allowed_origins is not None:
            normalized_origins = normalize_origins(allowed_origins)
            self.allowed_origins.update(normalized_origins)

        self.app = app

    def is_webview_or_desktop(self, headers: Headers) -> bool:  
        """Detecta si la solicitud viene de webview o aplicación de escritorio"""  
        user_agent = headers.get("user-agent", "").lower()  
          
        # Detecta Electron (aplicación de escritorio)  
        if "electron" in user_agent:  
            return True  
              
        # Detecta webviews comunes  
        webview_indicators = [  
            "webview",  
            "wkwebview",   
            "android",  
            "mobile",  
            "cordova",  
            "phonegap"  
        ]  
          
        return any(indicator in user_agent for indicator in webview_indicators)  
  
    def get_password_form(self) -> str:  
        """Retorna el formulario HTML para pedir contraseña"""  
        return """  
        <!DOCTYPE html>  
        <html>  
        <head>  
            <title>Voice Changer - Acceso Requerido</title>  
            <style>  
                body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f0f0f0; }  
                .login-form { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }  
                input[type="password"] { width: 200px; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }  
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }  
                button:hover { background: #0056b3; }  
                .error { color: red; margin-top: 10px; }  
            </style>  
        </head>  
        <body>  
            <div class="login-form">  
                <h2>Voice Changer</h2>  
                <p>Acceso desde navegador web detectado. Ingrese la contraseña:</p>  
                <form method="POST">  
                    <input type="password" name="password" placeholder="Contraseña" required>  
                    <br>  
                    <button type="submit">Acceder</button>  
                </form>  
            </div>  
        </body>  
        </html>  
        """ 

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in (
            "http",
            "websocket",
        ):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        origin = headers.get("origin", "")
        path = scope.get("path", "") 
      
        # Verificar si es una ruta de modelo  
        is_model_route = "/model_dir" in path  
        
        if is_model_route:  
            # Para rutas de modelos, verificar tanto origin como IP del cliente  
            client_ip = None  
            if "client" in scope:  
                client_ip = scope["client"][0]  
            
            local_origins = compute_local_origins()  
            is_local_origin = not origin or origin in local_origins  
            is_local_ip = client_ip in ["127.0.0.1", "::1", "localhost"] if client_ip else False  
            
            if is_local_origin and is_local_ip:  
                await self.app(scope, receive, send)  
                return  
            else:  
                response = PlainTextResponse("Access to model files denied XD", status_code=403)  
                await response(scope, receive, send)  
                return 

        # Origin header is not present for same origin
        if not origin or origin in self.allowed_origins:
            await self.app(scope, receive, send)
            return 
  
        # Si es webview o aplicación de escritorio, permitir acceso  
        if self.is_webview_or_desktop(headers):  
            await self.app(scope, receive, send)  
            return  
  
        # Si es navegador web normal, verificar contraseña  
        if scope["method"] == "POST":  
            # Leer el cuerpo de la solicitud para obtener la contraseña  
            body = b""  
            more_body = True  
            while more_body:  
                message = await receive()  
                body += message.get("body", b"")  
                more_body = message.get("more_body", False)  
              
            # Parsear la contraseña del formulario  
            body_str = body.decode("utf-8")  
            if "password=" in body_str:  
                password = body_str.split("password=")[1].split("&")[0]  
                # Decodificar URL encoding  
                import urllib.parse  
                password = urllib.parse.unquote_plus(password)  
                  
                # Verificar contraseña hardcodeada  
                if password == self.HARDCODED_PASSWORD:  
                    # Contraseña correcta, permitir acceso  
                    await self.app(scope, receive, send)  
                    return 

        response = PlainTextResponse("Invalid origin header", status_code=400)
        await response(scope, receive, send)
