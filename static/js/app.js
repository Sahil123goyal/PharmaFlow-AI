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

(function () {
  "use strict";

  var search = document.querySelector("[data-table-search]");
  var table = document.querySelector("[data-module-table]");
  if (search && table) {
    var tableRows = table.querySelectorAll("[data-table-row]");
    var empty = document.querySelector("[data-table-empty]");
    search.addEventListener("input", function () {
      var query = search.value.trim().toLowerCase();
      var visible = 0;
      tableRows.forEach(function (row) {
        var matches = !query || row.textContent.toLowerCase().indexOf(query) !== -1;
        row.hidden = !matches;
        if (matches) {
          visible += 1;
        }
      });
      if (empty) {
        empty.hidden = visible !== 0;
      }
    });
  }

  var exportButton = document.querySelector("[data-export-table]");
  if (exportButton && table) {
    exportButton.addEventListener("click", function () {
      var lines = [];
      table.querySelectorAll("tr").forEach(function (row) {
        if (row.hidden) {
          return;
        }
        var cells = [];
        row.querySelectorAll("th, td").forEach(function (cell) {
          if (!cell.classList.contains("table__actions")) {
            cells.push('"' + cell.textContent.trim().replace(/"/g, '""') + '"');
          }
        });
        lines.push(cells.join(","));
      });
      var blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
      var link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "pharmaflow-view.csv";
      link.click();
      URL.revokeObjectURL(link.href);
    });
  }
})();
