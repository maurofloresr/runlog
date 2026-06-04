  const usernameInput = document.getElementById("username");
  const usernameIcon = document.getElementById("username-icon");
  const usernameMsg = document.getElementById("username-msg");
  const passwordInput = document.getElementById("password");
  const passwordIcon = document.getElementById("password-icon");
  const strengthFill = document.getElementById("strength-fill");
  const confirmationWrap = document.getElementById("confirmation-wrap");
  const confirmationInput = document.getElementById("confirmation");
  const confirmationIcon = document.getElementById("confirmation-icon");

  // --- username availability check ---
  let usernameTimer;
  usernameInput.addEventListener("input", () => {
    clearTimeout(usernameTimer);
    const val = usernameInput.value.trim();

    if (val.length < 3) {
      setField(usernameInput, usernameIcon, val.length > 0 ? false : null);
      if (val.length > 0) {
        usernameMsg.textContent = "Username must be at least 3 characters";
        usernameMsg.style.color = "#ef4444";
        usernameMsg.style.display = "block";
      } else {
        usernameMsg.style.display = "none";
      }
      return;
    }

    usernameTimer = setTimeout(async () => {
      const res = await fetch(
        `/check-username?username=${encodeURIComponent(val)}`,
      );
      const data = await res.json();
      if (data.available) {
        setField(usernameInput, usernameIcon, true);
        usernameMsg.style.display = "none";
      } else {
        setField(usernameInput, usernameIcon, false);
        usernameMsg.textContent = "Username already taken";
        usernameMsg.style.color = "#ef4444";
        usernameMsg.style.display = "block";
      }
    }, 500);
  });

  // --- password strength ---
  function getStrength(val) {
    let score = 0;
    if (val.length >= 8) score++;
    if (/[0-9]/.test(val)) score++;
    if (/[A-Z]/.test(val)) score++;
    if (/[^a-zA-Z0-9]/.test(val)) score++;
    return score;
  }

  passwordInput.addEventListener("input", () => {
    const val = passwordInput.value;
    const strength = getStrength(val);
    const colors = ["#ef4444", "#f59e0b", "#22c55e", "#22c55e"];
    const widths = ["25%", "50%", "75%", "100%"];
    const valid = val.length >= 8 && /[0-9]/.test(val);

    if (val.length === 0) {
      strengthFill.style.width = "0";
      setField(passwordInput, passwordIcon, null);
    } else {
      strengthFill.style.width = widths[strength - 1] || "10%";
      strengthFill.style.background = colors[strength - 1] || "#ef4444";
      setField(passwordInput, passwordIcon, valid);
    }

    // show/hide confirmation
    confirmationWrap.style.display = valid ? "block" : "none";
    if (!valid) {
      confirmationInput.value = "";
      setField(confirmationInput, confirmationIcon, null);
    } else {
      checkConfirmation();
    }
  });

  // --- confirmation match ---
  confirmationInput.addEventListener("input", checkConfirmation);

  function checkConfirmation() {
    const match =
      confirmationInput.value === passwordInput.value &&
      confirmationInput.value.length > 0;
    setField(confirmationInput, confirmationIcon, match);
  }

  // --- helper: set valid/invalid/neutral state ---
  function setField(input, icon, state) {
    input.classList.remove("input-valid", "input-invalid");
    if (state === true) {
      input.classList.add("input-valid");
      icon.textContent = "✓";
      icon.style.color = "#22c55e";
    }
    if (state === false) {
      input.classList.add("input-invalid");
      icon.textContent = "✗";
      icon.style.color = "#ef4444";
    }
    if (state === null) {
      icon.textContent = "";
    }
  }

  // --- collapsible HR help ---
  document.getElementById("fc-help-toggle").addEventListener("click", () => {
    const el = document.getElementById("fc-help");
    el.style.display = el.style.display === "none" ? "block" : "none";
  });





