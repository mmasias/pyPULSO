import { Link, Route, Routes } from "react-router-dom";
import Participar from "./pages/Participar";
import Panel from "./pages/Panel";
import Plantillas from "./pages/Plantillas";
import NuevaEncuesta from "./pages/NuevaEncuesta";
import Encuesta from "./pages/Encuesta";

export default function App() {
  return (
    <>
      <header className="cabecera">
        <strong>PULSO</strong>
        <nav>
          <Link to="/">Participar</Link>
          <Link to="/panel">Panel</Link>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Participar />} />
          <Route path="/panel" element={<Panel />} />
          <Route path="/panel/plantillas" element={<Plantillas />} />
          <Route path="/panel/encuestas/nueva" element={<NuevaEncuesta />} />
          <Route path="/panel/encuestas/:id" element={<Encuesta />} />
        </Routes>
      </main>
    </>
  );
}
