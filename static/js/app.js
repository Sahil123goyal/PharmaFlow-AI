/* ==========================================================================
   PharmaFlowAI — Application shell behaviour
   Only the mobile navigation drawer. Everything else in the shell is static
   markup, so the product remains fully usable with JavaScript disabled.
   ========================================================================== */

(function () {
  "use strict";

  var app = document.querySelector("[data-app]");
  var toggle = document.querySelector("[data-nav-toggle]");
  var backdrop = document.querySelector("[data-nav-backdrop]");
  var sidebar = document.querySelector("[data-nav]");

  if (!app || !toggle) {
    return;
  }

  // Matches the breakpoint in app.css where the sidebar stops being a drawer.
  var wideViewport = window.matchMedia("(min-width: 64em)");

  function setOpen(open) {
    app.classList.toggle("is-nav-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function isOpen() {
    return app.classList.contains("is-nav-open");
  }

  function close(returnFocus) {
    if (!isOpen()) {
      return;
    }
    setOpen(false);
    if (returnFocus) {
      toggle.focus();
    }
  }

  toggle.addEventListener("click", function () {
    var open = !isOpen();
    setOpen(open);
    if (open && sidebar) {
      // Move focus into the drawer so keyboard users land where they expect.
      var firstLink = sidebar.querySelector("a");
      if (firstLink) {
        firstLink.focus();
      }
    }
  });

  if (backdrop) {
    backdrop.addEventListener("click", function () {
      close(true);
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      close(true);
    }
  });

  // Following a link should not leave the drawer open behind the new page, and
  // resizing back to desktop should drop the drawer state entirely.
  if (sidebar) {
    sidebar.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        setOpen(false);
      }
    });
  }

  wideViewport.addEventListener("change", function (event) {
    if (event.matches) {
      setOpen(false);
    }
  });
})();
