# Deployment customization notes

This fork modifies the upstream project in the following areas:

- Redesigned the frontend and extracted the production page into maintainable `web/` assets.
- Added the Python API used by the deployed calculator.
- Added validation for finite positive exchange rates, non-negative renewal prices, supported cycles, dates, request content type, and request size.
- Separated reference-rate and custom-rate calculations.
- Added generated SVG share cards, a 2,000-file storage bound, and 30-day cache semantics.
- Added non-root Docker images, health checks, a Compose stack, and a Caddy example.
- Added unit tests and GitHub Actions.

The project remains licensed under GPL-3.0 and retains the upstream Git history.
