/* Runtime configuration for the CRIKTRACK application.

   In production these values are injected by Flask/Jinja from
   environment variables. Locally, sensible defaults are provided:

   - googleMapsApiKey: leave empty to render the OpenStreetMap fallback.
     When set, the Google Maps JS API loads and displays interactive maps.
   - liveFeedEndpoint: the Flask proxy route that fronts CricketData.org.
     Set to '/api/live/matches' to use the backend; js/livefeed.js will
     fall back to window.CTM_MOCK.liveFeed if the endpoint is unreachable.
   - liveFeedPollMs: polling interval for live cricket data (milliseconds).
     Minimum 5000ms to avoid excessive requests. */

window.CTM_CONFIG = {
  googleMapsApiKey: '',
  liveFeedEndpoint: '/api/live/matches',
  liveFeedPollMs: 30000,
};
