import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, post } from "../api/cliente";
import { Marco, Titular } from "../Marco";

export default function Entrada() {
  const navegar = useNavigate();
  const [usuario, setUsuario] = useState("");
  const [clave, setClave] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    // Con sesion abierta, directamente a la aplicacion.
    api("/api/yo").then(() => navegar("/app", { replace: true }), () => undefined);
  }, [navegar]);

  async function entrar(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setEnviando(true);
    try {
      await post("/api/auth/login", { usuario: usuario.trim(), clave });
      navegar("/app", { replace: true });
    } catch (err) {
      setError((err as Error).message);
      setClave("");
      setEnviando(false);
    }
  }

  return (
    <Marco>
      <Titular titulo="PULSO" subtitulo="Encuestas de satisfacción anónimas" />
      <main>
        <div className="entrada">
          <form className="tarjeta" onSubmit={entrar} autoComplete="off">
            <h2>Iniciar sesión</h2>
            <p className="tenue">Acceso del personal de la universidad.</p>
            <label htmlFor="usuario">Usuario</label>
            <input id="usuario" value={usuario} onChange={(e) => setUsuario(e.target.value)} autoComplete="off" required autoFocus />
            <label htmlFor="clave">Contraseña</label>
            <input id="clave" type="password" value={clave} onChange={(e) => setClave(e.target.value)} autoComplete="off" required />
            <button type="submit" disabled={enviando}>Entrar</button>
            {error && <p className="error">{error}</p>}
          </form>

          <div className="tarjeta tarjeta-alumno">
            <h2>¿Eres alumno?</h2>
            <p>Si has recibido un código de invitación, responde la encuesta sin registrarte.</p>
            <p className="tenue">La respuesta es anónima: no se guarda nada que la relacione contigo ni con el código.</p>
            <Link to="/participar"><button type="button">Responder encuesta</button></Link>
          </div>
        </div>
      </main>
    </Marco>
  );
}
