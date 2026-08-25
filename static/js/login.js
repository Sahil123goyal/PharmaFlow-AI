/* ==========================================================================
   PharmaFlowAI — Login page behaviour
   Progressive enhancement only. With JavaScript disabled the form still posts
   and Django performs the same validation server-side.
   ========================================================================== */

(function () {
  "use strict";

  var form = document.querySelector("[data-login-form]");
  if (!form) {
    return;
  }

  var messageRegion = form.querySelector("[data-messages]");
  var submitButton = form.querySelector("[data-submit-button]");
  var submitLabel = form.querySelector("[data-submit-label]");
  var capsLockHint = form.querySelector("[data-capslock]");
  var passwordInput = form.querySelector('input[type="password"]');
  var isSubmitting = false;

  var EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  var MESSAGES = {
    username: "Enter your email address or username.",
    password: "Enter your password.",
    email: "Enter a valid email address, or use your username instead.",
    summary: "Please complete the highlighted fields to continue.",
  };

  /* ---------------------------------------------------------------- helpers */

  function fieldWrapper(input) {
    return input.closest("[data-field]");
  }

  function errorNode(input) {
    var wrapper = fieldWrapper(input);
    return wrapper ? wrapper.querySelector("[data-field-error]") : null;
  }

  function setFieldError(input, message) {
    var wrapper = fieldWrapper(input);
    var node = errorNode(input);

    if (wrapper) {
      wrapper.classList.toggle("field--invalid", Boolean(message));
    }
    if (node) {
      node.textContent = message || "";
    }
    if (message) {
      input.setAttribute("aria-invalid", "true");
    } else {
      input.removeAttribute("aria-invalid");
    }
  }

  /** Remove the client-side summary and any stale server-rendered error. */
  function clearSummary() {
    if (!messageRegion) {
      return;
    }
    var stale = messageRegion.querySelectorAll(
      "[data-client-error], [data-server-error]"
    );
    Array.prototype.forEach.call(stale, function (node) {
      node.remove();
    });
  }

  function showSummary(message) {
    if (!messageRegion) {
      return;
    }
    clearSummary();

    var alert = document.createElement("div");
    alert.className = "alert alert--error";
    alert.setAttribute("data-client-error", "");
    alert.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M10.3 3.9 2.4 17.3A1.9 1.9 0 0 0 4 20.2h16a1.9 1.9 0 0 0 1.6-2.9' +
      'L13.7 3.9a1.9 1.9 0 0 0-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>' +
      "<span></span>";
    alert.querySelector("span").textContent = message;
    messageRegion.prepend(alert);
  }

  /* ------------------------------------------------------------- validation */

  /** Return the list of inputs that failed validation, in DOM order. */
  function validate() {
    var invalid = [];

    var fields = form.querySelectorAll("[data-field] .field__input");
    Array.prototype.forEach.call(fields, function (input) {
      var value = input.value.trim();
      var isPassword = input.type === "password" || input.name === "password";
      var message = "";

      if (!value) {
        message = isPassword ? MESSAGES.password : MESSAGES.username;
      } else if (
        !isPassword &&
        value.indexOf("@") !== -1 &&
        !EMAIL_PATTERN.test(value)
      ) {
        message = MESSAGES.email;
      }

      setFieldError(input, message);
      if (message) {
        invalid.push(input);
      }
    });

    return invalid;
  }

  /* ---------------------------------------------------------- loading state */

  function startLoading() {
    if (!submitButton) {
      return;
    }
    isSubmitting = true;
    submitButton.classList.add("is-loading");
    submitButton.setAttribute("aria-disabled", "true");
    if (submitLabel) {
      submitLabel.textContent = "Signing in…";
    }
  }

  function stopLoading() {
    if (!submitButton) {
      return;
    }
    isSubmitting = false;
    submitButton.classList.remove("is-loading");
    submitButton.removeAttribute("aria-disabled");
    if (submitLabel) {
      submitLabel.textContent = "Sign in";
    }
  }

  /* -------------------------------------------------------------- behaviour */

  form.addEventListener("submit", function (event) {
    // Guard against a second submit while the first request is in flight.
    if (isSubmitting) {
      event.preventDefault();
      return;
    }

    var invalid = validate();
    if (invalid.length > 0) {
      event.preventDefault();
      showSummary(MESSAGES.summary);
      invalid[0].focus();
      return;
    }

    clearSummary();
    startLoading();
  });

  // Clear a field's error as soon as the user starts correcting it.
  form.addEventListener("input", function (event) {
    var input = event.target;
    if (!input.classList || !input.classList.contains("field__input")) {
      return;
    }
    if (input.value.trim()) {
      setFieldError(input, "");
    }
    clearSummary();
  });

  // Password visibility toggle.
  var toggle = form.querySelector("[data-password-toggle]");
  if (toggle && passwordInput) {
    toggle.addEventListener("click", function () {
      var willShow = toggle.getAttribute("aria-pressed") !== "true";
      passwordInput.type = willShow ? "text" : "password";
      toggle.setAttribute("aria-pressed", String(willShow));
      toggle.setAttribute("aria-label", willShow ? "Hide password" : "Show password");
      // Keep the caret where the user left it.
      passwordInput.focus({ preventScroll: true });
    });
  }

  // Caps Lock hint — a common cause of "wrong password" on a shared counter PC.
  if (passwordInput && capsLockHint) {
    var updateCapsLockHint = function (event) {
      if (typeof event.getModifierState !== "function") {
        return;
      }
      capsLockHint.hidden = !event.getModifierState("CapsLock");
    };

    passwordInput.addEventListener("keydown", updateCapsLockHint);
    passwordInput.addEventListener("keyup", updateCapsLockHint);
    passwordInput.addEventListener("blur", function () {
      capsLockHint.hidden = true;
    });
  }

  // Restore the button if the browser serves this page from its back/forward
  // cache after a failed navigation.
  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      stopLoading();
    }
  });
})();
