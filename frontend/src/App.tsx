import { Navigate, Route, Routes } from "react-router-dom";
import Entrada from "./pages/Entrada";
import Participar from "./pages/Participar";
import Encuestas from "./pages/Encuestas";
import Plantillas from "./pages/Plantillas";
import NuevaEncuesta from "./pages/NuevaEncuesta";
import Encuesta from "./pages/Encuesta";
import { SoloGestor, ZonaPrivada } from "./sesion";
import { Marco, Titular } from "./Marco";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Entrada />} />
      <Route
        path="/participar"
        element={
          <Marco>
            <Titular titulo="Encuesta de satisfacción docente" subtitulo="Su opinión es anónima: la respuesta no guarda nada que la relacione con usted." />
            <main>
              <Participar />
            </main>
          </Marco>
        }
      />
      <Route path="/app" element={<ZonaPrivada />}>
        <Route index element={<Encuestas />} />
        <Route path="encuestas/:id" element={<Encuesta />} />
        <Route element={<SoloGestor />}>
          <Route path="plantillas" element={<Plantillas />} />
          <Route path="encuestas/nueva" element={<NuevaEncuesta />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
