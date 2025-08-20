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
                response = PlainTextResponse("Access to model files denied", status_code=403)  
                await response(scope, receive, send)  
                return 

        # Origin header is not present for same origin
        if not origin or origin in self.allowed_origins:
            await self.app(scope, receive, send)
            return

        response = PlainTextResponse("Invalid origin header", status_code=400)
        await response(scope, receive, send)
