import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <strong>Lab Vibes London</strong>
          <p className="small">
            Aggregated, user-reported impressions of research workplaces. Summaries are unverified
            perceptions, not verified facts, and never rank individual researchers.
          </p>
        </div>
        <div>
          <div className="section-label">Project</div>
          <p className="small" style={{ margin: 0 }}>
            <Link to="/methodology">Methodology</Link>
            <br />
            <Link to="/ethics">Ethics &amp; limitations</Link>
            <br />
            <Link to="/about">About this project</Link>
          </p>
        </div>
        <div>
          <div className="section-label">Data</div>
          <p className="small" style={{ margin: 0 }}>
            Map data © OpenStreetMap contributors, © CARTO.
            <br />
            Raw posts are never published or committed.
          </p>
        </div>
      </div>
    </footer>
  );
}
