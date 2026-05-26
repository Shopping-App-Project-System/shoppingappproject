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
            const isOpen = toggle.classList.contains('open');
            toggle.classList.toggle('open');
            drawer.classList.toggle('open');
            // 強制套用 display 避免被其他 CSS 蓋掉
            drawer.style.display = isOpen ? 'none' : 'flex';
        });

        // 點選單外面關閉
        document.addEventListener('click', (e) => {
            if (!toggle.contains(e.target) && !drawer.contains(e.target)) {
                toggle.classList.remove('open');
                drawer.classList.remove('open');
                drawer.style.display = 'none';
            }
        });

        // 視窗變大時自動收起
        window.addEventListener('resize', () => {
            if (window.innerWidth > 800) {
                toggle.classList.remove('open');
                drawer.classList.remove('open');
                drawer.style.display = '';
            }
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
