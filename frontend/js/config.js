/* Runtime configuration for the static prototype.

   In Checkpoint 3 these values will be injected by Flask/Jinja from
   environment variables. For now they are placeholders so local pages run
   without any secrets:

   - googleMapsApiKey: leave empty to render the OpenStreetMap fallback.
     If set, the Google Maps JS API loads and draws a proper marker.
   - liveFeedEndpoint: the Flask proxy path that will front CricketData.org
     once the backend exists. While it does not, js/livefeed.js falls back
     to window.CTM_MOCK.liveFeed automatically. */

window.CTM_CONFIG = {
  googleMapsApiKey: '',
  liveFeedEndpoint: '/api/live/matches',
  liveFeedPollMs: 30000,
};
