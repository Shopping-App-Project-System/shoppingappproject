/* =====================================================
   MineMarket — 共用 JavaScript
   mc-common.js
   ===================================================== */

document.addEventListener('DOMContentLoaded', function() {

    // ── Hamburger menu ──
    const toggle = document.getElementById('navToggle');
    const drawer = document.getElementById('navDrawer');
    if (toggle && drawer) {
        toggle.addEventListener('click', () => {
            toggle.classList.toggle('open');
            drawer.classList.toggle('open');
        });
    }

    // ── 防止表單重複提交 ──
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const btn = this.querySelector('button[type="submit"]');
            if (btn && !btn.disabled) {
                btn.disabled = true;
                const orig = btn.textContent;
                btn.textContent = '⏳ 處理中...';
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = orig;
                }, 5000);
            }
        });
    });

});
