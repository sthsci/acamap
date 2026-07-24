interface Props {
  text?: string;
}

const DEFAULT =
  'Everything here reflects unverified, user-reported perceptions aggregated from public social media — not verified facts. Summaries never rank or make claims about individual researchers.';

export function Disclaimer({ text = DEFAULT }: Props) {
  return (
    <div className="disclaimer" role="note">
      <svg
        className="disclaimer__icon"
        width="18"
        height="18"
        viewBox="0 0 24 24"
        aria-hidden="true"
        fill="currentColor"
      >
        <path d="M12 2 1 21h22L12 2zm0 6c.6 0 1 .4 1 1v5a1 1 0 0 1-2 0V9c0-.6.4-1 1-1zm0 9.5a1.2 1.2 0 1 1 0 2.4 1.2 1.2 0 0 1 0-2.4z" />
      </svg>
      <span>{text}</span>
    </div>
  );
}

export function PerceptionsNote() {
  return (
    <p className="perceptions-note">
      <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
        <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
      </svg>
      User-reported perceptions, not verified facts.
    </p>
  );
}
