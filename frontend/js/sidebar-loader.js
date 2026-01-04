/**
 * Sidebar Loader - Separate Pages Version
 */

const SidebarLoader = {
    links: {
        admin: [
            { href: 'dashboard.html', label: '📊 Dashboard', icon: 'fa-th-large' },
            { href: 'users.html', label: '👥 Foydalanuvchilar', icon: 'fa-users' },
            { href: 'classes.html', label: '🏫 Guruhlar', icon: 'fa-school' },
            { href: 'coin-control.html', label: '🟡 Coin Control', icon: 'fa-coins' },
            { href: 'shop-management.html', label: '🛍️ Do\'kon', icon: 'fa-shopping-bag' },
            { href: 'reports.html', label: '📊 Hisobotlar', icon: 'fa-chart-bar' }
        ],
        director: [
            { href: 'dashboard.html', label: '📊 Dashboard', icon: 'fa-th-large' },
            { href: 'analytics.html', label: '📈 Analitika', icon: 'fa-chart-line' },
            { href: 'teachers-rating.html', label: '👨‍🏫 Reyting', icon: 'fa-star' }
        ],
        teacher: [
            { href: 'dashboard.html', label: '� Dashboard', icon: 'fa-th-large' },
            { href: 'attendance.html', label: '📝 Davomat', icon: 'fa-clipboard-check' },
            { href: 'homework.html', label: '📚 Uy vazifasi', icon: 'fa-book' },
            { href: 'students.html', label: '👨‍🎓 O\'quvchilar', icon: 'fa-user-graduate' }
        ],
        student: [
            { href: 'dashboard.html', label: '📊 Dashboard', icon: 'fa-th-large' },
            { href: 'shop.html', label: '🛍️ Shop', icon: 'fa-shopping-cart' },
            { href: 'coins.html', label: '🟡 Coinlarim', icon: 'fa-coins' },
            { href: 'my-group.html', label: '👥 Guruhim', icon: 'fa-users' },
            { href: 'tests.html', label: '📝 Testlar', icon: 'fa-vial' },
            { href: 'my-badges.html', label: '🏅 Nishonlar', icon: 'fa-award' }
        ]
    },

    async init() {
        this.role = localStorage.getItem('role') || 'student';
        this.userName = localStorage.getItem('user_name') || 'Foydalanuvchi';

        await this.loadSidebar();
        this.setupMobileToggle();
        this.renderRoleLinks();
        this.loadUserData();
        this.highlightActiveLink();
    },

    async loadSidebar() {
        const container = document.getElementById('sidebarContainer');
        if (!container) return;

        try {
            // Since pages are in /pages/[role]/, path to components is always ../../components/
            const path = window.location.pathname.includes('/pages/') ? '../../components/sidebar.html' : 'components/sidebar.html';
            const response = await fetch(path);
            let html = await response.text();
            container.innerHTML = html;
        } catch (e) {
            console.error('Sidebar load failed', e);
        }
    },

    setupMobileToggle() {
        // Find toggle button and overlay - these might be in the sidebar component or injected
        const toggle = document.getElementById('mobileMenuToggle');
        const sidebar = document.querySelector('.sidebar') || document.getElementById('sidebarContainer');
        const overlay = document.getElementById('sidebarOverlay');

        if (!toggle || !sidebar || !overlay) {
            // If toggle isn't in HTML, try to add it dynamically or wait for container
            console.warn('Mobile toggle elements not found yet');
            return;
        }

        const toggleMenu = () => {
            const isActive = sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        };

        toggle.onclick = toggleMenu;
        overlay.onclick = toggleMenu;
    },

    renderRoleLinks() {
        const menuContainer = document.getElementById('roleSpecificLinks');
        if (!menuContainer) return;

        const links = this.links[this.role] || [];
        const currentPath = window.location.pathname.split('/').pop();

        menuContainer.innerHTML = links.map(link => `
            <li>
                <a href="${link.href}" class="nav-item ${currentPath === link.href ? 'active' : ''}">
                    <i class="fas ${link.icon}"></i> <span>${link.label}</span>
                </a>
            </li>
        `).join('');
    },

    loadUserData() {
        const elements = {
            'userName': this.userName,
            'sidebarUserName': this.userName,
            'userRole': this.role,
            'sidebarUserRole': this.role,
            'userAvatar': this.userName[0].toUpperCase(),
            'sidebarAvatar': this.userName[0].toUpperCase()
        };

        for (let [id, val] of Object.entries(elements)) {
            const el = document.getElementById(id);
            if (el) el.innerText = val;
        }
    },

    highlightActiveLink() {
        const currentPath = window.location.pathname.split('/').pop();
        document.querySelectorAll('.nav-item').forEach(el => {
            if (el.getAttribute('href') === currentPath) {
                el.classList.add('active');
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => SidebarLoader.init());

window.logout = () => {
    localStorage.clear();
    const loginPath = window.location.pathname.includes('/pages/') ? '../../login.html' : 'login.html';
    window.location.href = loginPath;
};
