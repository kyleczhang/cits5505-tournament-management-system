(function () {
  'use strict';

  const NAV_HTML = `
  <nav class="ctm-navbar" aria-label="Primary">
    <div class="container d-flex align-items-center justify-content-between">
      <a class="navbar-brand" href="index.html" aria-label="Cricket Tournament Manager home">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M14.5 3.5l6 6-11 11-4.5 1.5L6.5 17l8-13.5z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
          <circle cx="18.5" cy="5.5" r="2" fill="currentColor"/>
        </svg>
        <span>CRIKTRACK</span>
      </a>
      <button class="btn btn-ctm-ghost d-md-none" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav" aria-controls="mainNav" aria-expanded="false" aria-label="Toggle navigation">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </button>
      <div class="collapse navbar-collapse justify-content-end" id="mainNav">
        <ul class="navbar-nav d-flex flex-md-row gap-md-1 align-items-md-center">
          <li class="nav-item"><a class="nav-link" data-page="dashboard.html" href="dashboard.html">Dashboard</a></li>
          <li class="nav-item"><a class="nav-link" data-page="tournaments-list.html" href="tournaments-list.html">Tournaments</a></li>
          <li class="nav-item" data-role-gate="organizer"><a class="nav-link" data-page="tournaments-create.html" href="tournaments-create.html">Create</a></li>
          <li class="nav-item"><a class="nav-link" data-page="profile.html" href="profile.html">Profile</a></li>
          <li class="nav-item ms-md-2"><a class="btn btn-ctm-primary btn-sm" href="login.html">Log in</a></li>
        </ul>
      </div>
    </div>
  </nav>`;

  const FOOTER_HTML = `
  <footer class="ctm-footer" role="contentinfo">
    <div class="container">
      <div class="row g-4">
        <div class="col-lg-4">
          <div class="brand-block mb-2">CRIKTRACK</div>
          <p class="mb-0">Run your cricket tournament from draw to trophy. Fixtures, scorecards, standings, and player stats in one place.</p>
        </div>
        <div class="col-6 col-md-4 col-lg-2">
          <h5>Product</h5>
          <ul class="list-unstyled m-0 d-flex flex-column gap-2">
            <li><a href="tournaments-list.html">Tournaments</a></li>
            <li><a href="tournaments-create.html">Create</a></li>
            <li><a href="dashboard.html">Dashboard</a></li>
          </ul>
        </div>
        <div class="col-6 col-md-4 col-lg-2">
          <h5>Account</h5>
          <ul class="list-unstyled m-0 d-flex flex-column gap-2">
            <li><a href="login.html">Log in</a></li>
            <li><a href="register.html">Sign up</a></li>
            <li><a href="profile.html">Profile</a></li>
          </ul>
        </div>
        <div class="col-md-4 col-lg-4">
          <h5>Team</h5>
          <p class="mb-0">Built by the CITS5505 Agile team. UWA, 2026.</p>
        </div>
      </div>
      <div class="copy d-flex flex-column flex-md-row justify-content-between gap-2">
        <span>&copy; 2026 CRIKTRACK — CITS5505 Group Project</span>
        <span><a href="index.html">Back to top</a></span>
      </div>
    </div>
  </footer>`;

  document.addEventListener('DOMContentLoaded', function () {
    const nav = document.querySelector('[data-layout="nav"]');
    if (nav) nav.outerHTML = NAV_HTML;
    const footer = document.querySelector('[data-layout="footer"]');
    if (footer) footer.outerHTML = FOOTER_HTML;
  });
})();
