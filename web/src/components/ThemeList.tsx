import { pluralise } from '../lib/format';
import type { Theme } from '../types';

interface Props {
  title: string;
  themes: Theme[];
}

export function ThemeList({ title, themes }: Props) {
  if (themes.length === 0) return null;
  return (
    <div className="theme-group">
      <div className="theme-group__title">{title}</div>
      {themes.map((theme) => (
        <div className="theme" key={theme.theme}>
          <div className="theme__head">
            <span className="theme__name">{theme.theme}</span>
            <span className="theme__count">{pluralise(theme.supporting_item_count, 'item')}</span>
          </div>
          <p className="theme__desc">{theme.description}</p>
        </div>
      ))}
    </div>
  );
}
