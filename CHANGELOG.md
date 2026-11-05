# Changelog

All notable changes to the Griptape Nodes Flow Production Tracking Library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/), and each version is
the `library_version` in `flow_production_tracking/griptape_nodes_library.json`.
**Breaking** marks a change that can stop a saved workflow from working without edits.

## [Unreleased]

<!-- Entries go in changelog.d/, one file each. See changelog.d/README.md. -->

## [0.2.0] - 2026-11-06

### Changed

- Autodesk Flow nodes show Flow's own reason, status code and response under More info when a request
  fails, and name the parameter when an input is missing or not a whole number. A missing
  `SHOTGRID_API_KEY` or `SHOTGRID_URL` is reported first, with a link to Settings. A missing input
  that used to end the node quietly now stops the run unless the Failed output is wired. Requires
  Griptape Nodes 0.105.0 or newer.
  [#17](https://github.com/griptape-ai/griptape-nodes-library-flow-production-tracking/issues/17)

## [0.1.8] - 2026-05-28

Changes up to and including this version are not recorded here.

[Unreleased]: https://github.com/griptape-ai/griptape-nodes-library-flow-production-tracking/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/griptape-ai/griptape-nodes-library-flow-production-tracking/compare/3ab5c2f16065ab662ba89e35d2180c4f0bc1992b...v0.2.0
[0.1.8]: https://github.com/griptape-ai/griptape-nodes-library-flow-production-tracking/commit/3ab5c2f16065ab662ba89e35d2180c4f0bc1992b
