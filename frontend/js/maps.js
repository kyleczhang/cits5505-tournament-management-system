/* Venue map renderer.

   Each page that wants a map drops this shell into the DOM:

     <div class="ctm-map-frame" data-ctm-map
          data-lat="-31.98" data-lng="115.82" data-label="UWA Sports Park">
     </div>

   If CTM_CONFIG.googleMapsApiKey is set, we load the Google Maps JS API
   once and draw a real marker. Otherwise we render an OpenStreetMap iframe
   so the prototype works without a billing account. The backend proxy and
   real API key arrive in Checkpoint 3 (Section 13.1). */

(function () {
  'use strict';

  let gmScriptPromise = null;

  function loadGoogleMaps(key) {
    if (window.google && window.google.maps) return Promise.resolve();
    if (gmScriptPromise) return gmScriptPromise;
    gmScriptPromise = new Promise(function (resolve, reject) {
      const s = document.createElement('script');
      s.src =
        'https://maps.googleapis.com/maps/api/js?key=' +
        encodeURIComponent(key) +
        '&v=weekly';
      s.async = true;
      s.defer = true;
      s.onload = function () {
        resolve();
      };
      s.onerror = function () {
        reject(new Error('Google Maps failed to load'));
      };
      document.head.appendChild(s);
    });
    return gmScriptPromise;
  }

  function renderOSM(frame, lat, lng, label) {
    /* OpenStreetMap embed — no API key required. Bounding box is a ~0.02°
       square around the marker so the venue is always visible. */
    const d = 0.01;
    const bbox = [lng - d, lat - d, lng + d, lat + d].join(',');
    const iframe = document.createElement('iframe');
    iframe.title = 'Map showing ' + label;
    iframe.loading = 'lazy';
    iframe.src =
      'https://www.openstreetmap.org/export/embed.html?bbox=' +
      encodeURIComponent(bbox) +
      '&layer=mapnik&marker=' +
      encodeURIComponent(lat + ',' + lng);
    frame.innerHTML = '';
    frame.appendChild(iframe);
    const provider = frame.nextElementSibling;
    if (provider && provider.classList.contains('ctm-map-provider')) {
      provider.innerHTML =
        '<a href="https://www.openstreetmap.org/?mlat=' +
        lat +
        '&mlon=' +
        lng +
        '#map=15/' +
        lat +
        '/' +
        lng +
        '" target="_blank" rel="noopener">View on OpenStreetMap →</a>';
    }
  }

  function renderGoogle(frame, lat, lng, label) {
    const canvas = document.createElement('div');
    canvas.className = 'gm-canvas';
    frame.innerHTML = '';
    frame.appendChild(canvas);
    const map = new google.maps.Map(canvas, {
      center: { lat: lat, lng: lng },
      zoom: 15,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
    });
    const marker = new google.maps.Marker({
      position: { lat: lat, lng: lng },
      map: map,
      title: label,
    });
    const info = new google.maps.InfoWindow({ content: escapeHtml(label) });
    marker.addListener('click', function () {
      info.open(map, marker);
    });
    const provider = frame.nextElementSibling;
    if (provider && provider.classList.contains('ctm-map-provider')) {
      provider.innerHTML =
        '<a href="https://www.google.com/maps/search/?api=1&query=' +
        lat +
        ',' +
        lng +
        '" target="_blank" rel="noopener">View on Google Maps →</a>';
    }
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      }[c];
    });
  }

  function renderAll() {
    const frames = document.querySelectorAll('[data-ctm-map]');
    if (!frames.length) return;
    const cfg = window.CTM_CONFIG || {};
    const key = cfg.googleMapsApiKey;

    frames.forEach(function (frame) {
      const lat = parseFloat(frame.getAttribute('data-lat'));
      const lng = parseFloat(frame.getAttribute('data-lng'));
      const label = frame.getAttribute('data-label') || 'Match venue';
      if (isNaN(lat) || isNaN(lng)) return;

      if (key) {
        loadGoogleMaps(key)
          .then(function () {
            renderGoogle(frame, lat, lng, label);
          })
          .catch(function () {
            renderOSM(frame, lat, lng, label);
          });
      } else {
        renderOSM(frame, lat, lng, label);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderAll);
  } else {
    renderAll();
  }

  window.ctmMaps = { render: renderAll };
})();
