// ---- Menu mobile (bouton hamburger) ----
// Sur mobile la sidebar est cachée, ce bouton l'ouvre/ferme.
var menuBtn = document.getElementById("menu-btn");
var sidebar = document.getElementById("sidebar");
if (menuBtn && sidebar) {
  menuBtn.addEventListener("click", function () {
    sidebar.classList.toggle("open");
  });
  // Fermer la sidebar en cliquant en dehors
  document.addEventListener("click", function (e) {
    if (sidebar.classList.contains("open") &&
        !sidebar.contains(e.target) &&
        e.target !== menuBtn) {
      sidebar.classList.remove("open");
    }
  });
}

// ---- Messages flash disparaissent après 5 secondes ----
setTimeout(function () {
  document.querySelectorAll(".flash-wrap .flash-success").forEach(function (el) {
    el.style.transition = "opacity .5s";
    el.style.opacity = "0";
    setTimeout(function () { el.remove(); }, 600);
  });
}, 5000);

// ---- Bouton & menu déroulant de notifications ----
var notifBtn = document.getElementById("notif-btn");
var notifDropdown = document.getElementById("notif-dropdown");
var notifBadge = document.getElementById("notif-badge");
var notifClear = document.getElementById("notif-clear");

if (notifBtn && notifDropdown) {
  notifBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    var isOpen = notifDropdown.classList.toggle("open");
    notifBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  // Fermer le dropdown en cliquant à l'extérieur
  document.addEventListener("click", function (e) {
    if (!notifDropdown.contains(e.target) && e.target !== notifBtn) {
      notifDropdown.classList.remove("open");
      notifBtn.setAttribute("aria-expanded", "false");
    }
  });

  // Action marquer tout comme lu
  if (notifClear) {
    notifClear.addEventListener("click", function (e) {
      e.stopPropagation();
      document.querySelectorAll(".notif-item.unread").forEach(function (el) {
        el.classList.remove("unread");
      });
      document.querySelectorAll(".notif-dot").forEach(function (dot) {
        dot.remove();
      });
      if (notifBadge) {
        notifBadge.textContent = "0";
        notifBadge.classList.add("hidden");
      }
    });
  }
}

// Cacher le badge si le compteur est 0 dès le départ
if (notifBadge) {
  var count = parseInt(notifBadge.textContent, 10) || 0;
  if (count === 0) notifBadge.classList.add("hidden");
}

// ---- Bouton mode sombre / clair ----
function updateThemeButtons() {
  var currentTheme = document.documentElement.getAttribute("data-theme") || "light";
  var isDark = currentTheme === "dark";

  document.querySelectorAll(".theme-btn").forEach(function (btn) {
    btn.innerHTML = isDark ? "☀️" : "🌙";
    btn.setAttribute("aria-label", isDark ? "Passer en mode clair" : "Passer en mode sombre");
    btn.title = isDark ? "Passer en mode clair" : "Passer en mode sombre";
  });
}

function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try { localStorage.setItem("rc-theme", theme); } catch (e) {}
  updateThemeButtons();
}

// Initialiser tous les boutons thème de la page
document.querySelectorAll(".theme-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    setTheme(currentTheme === "dark" ? "light" : "dark");
  });
});

// Mettre à jour l'icône immédiatement
updateThemeButtons();
