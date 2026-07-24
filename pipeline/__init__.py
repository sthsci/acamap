"""Lab Vibes London — local data-processing and summarisation pipeline.

This package is intended to run ONLY on a maintainer's machine. It ingests
lawfully collected public social-media posts, anonymises identifiers, routes
sensitive content to a private moderation queue, aggregates the remainder,
summarises recurring themes with a LOCAL LLM (Ollama), and exports sanitised,
aggregated JSON for the static website.

Raw text never leaves the local machine and is never written to the exported
public JSON.
"""

__version__ = "0.1.0"
