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

  function getCookie(name) {
    var cookies = document.cookie ? document.cookie.split(";") : [];
    for (var index = 0; index < cookies.length; index += 1) {
      var cookie = cookies[index].trim();
      if (cookie.indexOf(name + "=") === 0) {
        return decodeURIComponent(cookie.slice(name.length + 1));
      }
    }
    return "";
  }

  var chatbot = document.querySelector("[data-chatbot]");
  if (chatbot) {
    var chatToggle = chatbot.querySelector("[data-chat-toggle]");
    var chatClose = chatbot.querySelector("[data-chat-close]");
    var chatPanel = chatbot.querySelector("[data-chat-panel]") || chatbot.querySelector(".chatbot__panel");
    var chatMessages = chatbot.querySelector("[data-chat-messages]");
    var chatForm = chatbot.querySelector("[data-chat-form]");
    var chatInput = chatbot.querySelector("[data-chat-input]");
    var chatSend = chatbot.querySelector("[data-chat-send]");
    var chatStorageKey = "pharmaflow-chat-history";

    function addMessage(text, role, persist) {
      var item = document.createElement("p");
      item.className = "chatbot__message chatbot__message--" + role;
      item.textContent = text;
      chatMessages.appendChild(item);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      if (persist) {
        try {
          var history = JSON.parse(sessionStorage.getItem(chatStorageKey) || "[]");
          history.push({ text: text, role: role });
          sessionStorage.setItem(chatStorageKey, JSON.stringify(history.slice(-20)));
        } catch (error) {
          // Session storage is an enhancement; the visible chat still works.
        }
      }
    }

    function restoreChat() {
      var history = [];
      try {
        history = JSON.parse(sessionStorage.getItem(chatStorageKey) || "[]");
      } catch (error) {
        history = [];
      }
      if (!history.length) {
        addMessage("Hi. Ask me about medicines, inventory, bills or sales.", "assistant", false);
        return;
      }
      history.forEach(function (item) {
        addMessage(item.text, item.role, false);
      });
    }

    function setChatOpen(open) {
      chatPanel.hidden = !open;
      chatToggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) {
        chatInput.focus();
      }
    }

    restoreChat();
    chatToggle.addEventListener("click", function () {
      setChatOpen(chatPanel.hidden);
    });
    chatClose.addEventListener("click", function () {
      setChatOpen(false);
      chatToggle.focus();
    });

    chatForm.addEventListener("submit", function (event) {
      event.preventDefault();
      var message = chatInput.value.trim();
      if (!message) {
        return;
      }
      addMessage(message, "user", true);
      chatInput.value = "";
      chatSend.disabled = true;

      fetch(chatbot.dataset.chatEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ message: message })
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Assistant request failed");
          }
          return response.json();
        })
        .then(function (data) {
          addMessage(data.reply || "I could not answer that just now.", "assistant", true);
        })
        .catch(function () {
          addMessage("The assistant is unavailable right now. Try checking the module directly.", "assistant", true);
        })
        .finally(function () {
          chatSend.disabled = false;
          chatInput.focus();
        });
    });
  }

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
