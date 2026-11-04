from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401 -- registra las clases en Base.metadata
from app.core.config import get_settings
from app.core.database import Base, engine, get_db
from app.routers import auth, catalogo, encuesta, participacion, plantilla, yo
from app.services.errores import ErrorDominio

Base.metadata.create_all(bind=engine)

_settings = get_settings()
app = FastAPI(
    title="pyPULSO API",
    # Documentacion interactiva solo en desarrollo.
    docs_url="/api/docs" if _settings.es_dev else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if _settings.es_dev else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Dev-User"],
)

# Limite de tamano de cuerpo: ninguna peticion legitima de PULSO pasa de esto.
MAX_CUERPO = 256 * 1024


@app.middleware("http")
async def cabeceras_y_limites(request: Request, call_next):
    # CSRF: un navegador moderno marca el origen de cada peticion. Se
    # rechazan escrituras iniciadas desde otro sitio, incluidos subdominios
    # hermanos (SameSite=Lax no los cubre). Clientes sin la cabecera (curl,
    # tests) no se ven afectados: no llevan la cookie de un navegador.
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get(
        "sec-fetch-site", "same-origin"
    ) not in ("same-origin", "none"):
        return JSONResponse({"detail": "Origen no permitido"}, status_code=403)
    longitud = request.headers.get("content-length")
    if longitud is not None and (not longitud.isdigit() or int(longitud) > MAX_CUERPO):
        return JSONResponse({"detail": "Cuerpo demasiado grande"}, status_code=413)
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@app.exception_handler(ErrorDominio)
async def error_dominio(_: Request, exc: ErrorDominio) -> JSONResponse:
    return JSONResponse({"detail": exc.detalle}, status_code=exc.estado_http)


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(yo.router)
app.include_router(catalogo.router)
app.include_router(plantilla.router)
app.include_router(encuesta.router)
app.include_router(participacion.router)
