import { Disclaimer } from '../components/Disclaimer';

export function EthicsPage() {
  return (
    <article className="container prose">
      <h1>Ethics &amp; limitations</h1>
      <p className="lead">
        This project concerns people&rsquo;s workplace experiences. It is designed to inform gently,
        not to accuse, rank or expose.
      </p>

      <Disclaimer />

      <h2>What these summaries are</h2>
      <ul>
        <li>Aggregated impressions that people chose to post publicly.</li>
        <li>Unverified perceptions, presented as perceptions and never as established fact.</li>
        <li>Summaries of recurring themes, with isolated one-off comments de-emphasised.</li>
      </ul>

      <h2>What they are not</h2>
      <ul>
        <li>Not a ranking, rating or league table of institutions, labs or individuals.</li>
        <li>Not a &ldquo;best lab&rdquo; or &ldquo;worst lab&rdquo; list.</li>
        <li>Not a source of claims about any named person.</li>
        <li>Not a complete or representative survey of any workplace.</li>
      </ul>

      <h2>Why interpretation is limited</h2>
      <ul>
        <li>
          <strong>Selection bias:</strong> people with strong experiences are more likely to post,
          so summaries over-represent memorable impressions.
        </li>
        <li>
          <strong>Unverifiable identities:</strong> authorship and affiliation cannot be confirmed,
          and a few active authors can dominate a small sample.
        </li>
        <li>
          <strong>Recommendation algorithms:</strong> what appears publicly is shaped by platform
          ranking, not by any representative sampling.
        </li>
        <li>
          <strong>Absence is not evidence:</strong> the absence of a complaint does not mean a
          problem does not exist, and vice versa.
        </li>
      </ul>

      <h2>Protections built into the code</h2>
      <ul>
        <li>Usernames, profile URLs and unhashed author identifiers are never published.</li>
        <li>Raw comments are never published by default.</li>
        <li>Protected characteristics are never inferred.</li>
        <li>
          Serious allegations, misconduct accusations, identifying medical information and targeted
          insults are automatically excluded to a private, git-ignored queue.
        </li>
        <li>
          A minimum of 5 items from 3 distinct authors is required before any lab summary is shown.
        </li>
        <li>
          An automated privacy test blocks the build if identifying fields would reach the public
          site.
        </li>
      </ul>

      <h2>If a summary seems wrong or harmful</h2>
      <p>
        These are automated aggregations and can be incomplete or mistaken. Maintainers can withhold
        any lab, adjust thresholds, or remove content from the private queue. The public site never
        exposes the underlying posts, and no individual is named or scored.
      </p>

      <p className="callout">
        Read how the pipeline works on the <a href="#/methodology">Methodology</a> page.
      </p>
    </article>
  );
}
