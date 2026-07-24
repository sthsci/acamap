import { Route, Routes } from 'react-router-dom';

import { Footer } from './components/Footer';
import { Header } from './components/Header';
import { AboutPage } from './pages/AboutPage';
import { EthicsPage } from './pages/EthicsPage';
import { HomePage } from './pages/HomePage';
import { MethodologyPage } from './pages/MethodologyPage';

export function App() {
  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header />
      <main id="main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/methodology" element={<MethodologyPage />} />
          <Route path="/ethics" element={<EthicsPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
