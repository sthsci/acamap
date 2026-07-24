import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Map', end: true },
  { to: '/methodology', label: 'Methodology' },
  { to: '/ethics', label: 'Ethics' },
  { to: '/about', label: 'About' },
];

export function Header() {
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <NavLink to="/" className="brand" end>
          <span className="brand__name">Lab Vibes London</span>
          <span className="brand__tag">Reported perceptions · aggregated</span>
        </NavLink>
        <nav className="site-nav" aria-label="Primary">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
