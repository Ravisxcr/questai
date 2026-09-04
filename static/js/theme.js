/**
 * shadcn/ui Theme Manager for QuestAI
 * Handles 'light', 'dark', and 'system' themes with zero flash of unstyled content.
 */

(function () {
  function applyTheme(theme) {
    const isDark =
      theme === 'dark' ||
      (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  window.ThemeManager = {
    get: function () {
      return localStorage.getItem('questai-theme') || 'system';
    },
    set: function (theme) {
      localStorage.setItem('questai-theme', theme);
      applyTheme(theme);
      this.updateUI();
    },
    updateUI: function () {
      const current = this.get();
      
      // Update checkmarks in dropdown if open
      const options = document.querySelectorAll('[data-theme-value]');
      options.forEach(function (el) {
        const check = el.querySelector('.theme-check');
        if (check) {
          if (el.getAttribute('data-theme-value') === current) {
            check.classList.remove('opacity-0');
          } else {
            check.classList.add('opacity-0');
          }
        }
      });

      // Update button icon
      const iconLight = document.getElementById('themeIconLight');
      const iconDark = document.getElementById('themeIconDark');
      const iconSystem = document.getElementById('themeIconSystem');

      if (iconLight && iconDark && iconSystem) {
        iconLight.classList.add('hidden');
        iconDark.classList.add('hidden');
        iconSystem.classList.add('hidden');

        if (current === 'light') {
          iconLight.classList.remove('hidden');
        } else if (current === 'dark') {
          iconDark.classList.remove('hidden');
        } else {
          iconSystem.classList.remove('hidden');
        }
      }
    },
  };

  // Watch for system theme changes if user selected 'system'
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
    if (window.ThemeManager.get() === 'system') {
      applyTheme('system');
    }
  });

  // Apply immediately
  applyTheme(window.ThemeManager.get());

  // Initialize UI once DOM is ready or immediately if already loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      window.ThemeManager.updateUI();
    });
  } else {
    window.ThemeManager.updateUI();
  }
})();
