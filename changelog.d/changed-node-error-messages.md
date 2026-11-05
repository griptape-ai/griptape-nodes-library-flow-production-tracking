- Autodesk Flow nodes show Flow's own reason, status code and response under More info when a request
  fails, and name the parameter when an input is missing or not a whole number. A missing
  `SHOTGRID_API_KEY` or `SHOTGRID_URL` is reported first, with a link to Settings. A missing input
  that used to end the node quietly now stops the run unless the Failed output is wired. Requires
  Griptape Nodes 0.104.0 or newer.
  [#17](https://github.com/griptape-ai/griptape-nodes-library-flow-production-tracking/issues/17)
