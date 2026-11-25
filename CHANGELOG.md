## Local startup and deployment readiness fixes (2026-11-25)

### Fixed
- Serve the actual static frontend without an undeclared Node dependency.
- Point Static Web Apps deployment at the existing frontend directory and skip the unnecessary build.
- Run draft pull request checks without deploying a preview; deploy when the PR becomes ready for review.
- Pin workflow actions to verified full commit SHAs as required by the organization policy.
- Validate chat requests and return Azure Functions JSON responses, including errors.
- Load ingestion credentials from environment settings and keep the news API key out of URLs and source.
- Await article processing, enforce HTTP timeouts, and report ingestion failures to the Functions host.
- Avoid startup ingestion and automatic creation of an unconfigured output container.
- Route local frontend requests to the local Functions host and recover the input controls after API failures.
- Declare the missing article-parser dependency and remove the duplicate requests dependency.
- Reuse the chat app's Cosmos client and require explicit opt-in for resource creation.
- Preserve both excluded index paths instead of overwriting a duplicate dictionary key.

### Added
- Offline regression tests for chat validation, ingestion, frontend failure recovery, and Cosmos setup.
- A pre-deployment CI sanity check and explicit local credential, storage, port, and provisioning instructions.
