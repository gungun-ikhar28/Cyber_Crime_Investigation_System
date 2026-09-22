// Theme & Font Manager with LocalStorage Persistence
(function() {
    function applySavedTheme() {
        const savedTheme = localStorage.getItem('cyber_theme') || 'dark';
        if (savedTheme === 'light') {
            document.body.classList.add('light-mode');
        } else {
            document.body.classList.remove('light-mode');
        }
        updateButtonLabel();
    }

    function updateButtonLabel() {
        const btn = document.getElementById('theme-toggle-btn');
        if (!btn) return;
        const isLight = document.body.classList.contains('light-mode');
        btn.innerHTML = isLight ? '🌙 Dark Mode' : '☀️ Light Mode';
    }

    window.toggleTheme = function() {
        document.body.classList.toggle('light-mode');
        const isLight = document.body.classList.contains('light-mode');
        localStorage.setItem('cyber_theme', isLight ? 'light' : 'dark');
        updateButtonLabel();
    };

    function applySavedFont() {
        const savedFont = localStorage.getItem('cyber_font') || 'Orbitron';
        document.documentElement.style.setProperty('--current-font', `'${savedFont}', sans-serif`);
        const fontSelector = document.getElementById('font-selector');
        if (fontSelector) {
            fontSelector.value = savedFont;
        }
    }

    window.changeFont = function(fontName) {
        localStorage.setItem('cyber_font', fontName);
        document.documentElement.style.setProperty('--current-font', `'${fontName}', sans-serif`);
    };

    function init() {
        applySavedTheme();
        applySavedFont();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
