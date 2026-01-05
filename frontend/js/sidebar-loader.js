/**
 * Sidebar Loader - Centralized sidebar management for Niners.uz
 * This script injects the sidebar and role-specific links into all dashboard pages.
 */

const SidebarLoader = {
    links: {
        admin: [
            { href: 'users.html', label: '👥 User Management' },
            { href: 'classes.html', label: '🏫 Groups/Classes' },
            { href: 'coin-control.html', label: '🟡 Coin Control' },
            { href: 'reports.html', label: '📊 Learning Reports' },
            { href: 'appeals.html', label: '📩 Appeals & complaints' },
            { href: 'audit-logs.html', label: '🛡️ Security Logs' },
            { href: 'shop-management.html', label: '🛍️ Shop Management' },
            { href: 'badges.html', label: '🏆 Badge Management' }
        ],
        director: [
            { href: 'analytics.html', label: '📈 Analytics' },
            { href: 'teachers-rating.html', label: '👨‍🏫 Teacher Ratings' },
            { href: 'coin-policy.html', label: '🟡 Coin Policy' },
            { href: 'system-logs.html', label: '🛡️ System Logs' }
        ],
        teacher: [
            { href: 'attendance.html', label: '📝 Attendance' },
            { href: 'homework.html', label: '📚 Homework' },
            { href: 'students.html', label: '👨‍🎓 My Students' },
            { href: 'activity.html', label: '📈 Activity Log' }
        ],
        student: [
            { href: 'shop.html', label: '🛍️ Niners Shop' },
            { href: 'coins.html', label: '🟡 My Coins' },
            { href: 'my-group.html', label: '👥 My Group' },
            { href: 'tests.html', label: '📝 Tests/Quizzes' },
            { href: 'profile.html', label: '👤 Profile' }
        ],
        parent: [
            { href: 'child-progress.html', label: '📊 Child Progress' },
            { href: 'notifications.html', label: '🔔 Notifications' }
        ]
    },

    async init() {
        const container = document.getElementById('sidebarContainer');
        if (!container) return;

        try {
            // 0. Mobile Toggle Logic (Initialize UI first)
            this.addMobileToggle();

            // 0.1 Load Translations
            if (window.LanguageModule) {
                window.LanguageModule.init();
            }

            // 1. Fetch sidebar template
            const isSubpage = window.location.pathname.includes('/pages/');
            const sidebarPath = isSubpage ? '../../components/sidebar.html' : 'components/sidebar.html';

            const response = await fetch(sidebarPath);
            const html = await response.text();

            // Remove any script tags from the fetched HTML to avoid confusion
            const cleanHtml = html.replace(/<script\b[^>]*>([\s\S]*?)<\/script>/gmi, "");
            container.innerHTML = cleanHtml;

            // 1.1 Render Language Switcher (Now that sidebar exists)
            if (window.LanguageModule) {
                window.LanguageModule.renderSwitcher();
            }

            // 2. Mobile Toggle Logic (2nd pass: Bind Events to Sidebar)
            this.addMobileToggle();

            // 3. Determine role
            const role = localStorage.getItem('role') || 'student';

            // Translations integration for links
            const t = window.t || ((k) => k);

            this.links = {
                admin: [
                    { href: 'users.html', label: `👥 ${t('users')}` },
                    { href: 'classes.html', label: `🏫 ${t('groups')}` },
                    { href: 'coin-control.html', label: `🟡 ${t('coin_control')}` },
                    { href: 'reports.html', label: `📊 ${t('learning_reports')}` },
                    { href: 'appeals.html', label: `📩 ${t('appeals')}` },
                    { href: 'audit-logs.html', label: `🛡️ ${t('security_logs')}` },
                    { href: 'shop-management.html', label: `🛍️ ${t('shop_management')}` },
                    { href: 'badges.html', label: `🏆 ${t('badge_management')}` }
                ],
                director: [
                    { href: 'analytics.html', label: `📈 ${t('analytics')}` },
                    { href: 'teachers-rating.html', label: `👨‍🏫 ${t('rating')}` },
                    { href: 'coin-policy.html', label: `🟡 ${t('coin_policy')}` },
                    { href: 'system-logs.html', label: `🛡️ ${t('security_logs')}` }
                ],
                teacher: [
                    { href: 'attendance.html', label: `📝 ${t('attendance')}` },
                    { href: 'homework.html', label: `📚 ${t('homework')}` },
                    { href: 'students.html', label: `👨‍🎓 ${t('students')}` },
                    { href: 'activity.html', label: `📈 ${t('activity_log')}` }
                ],
                student: [

                    { href: 'shop.html', label: `🛍️ ${t('shop')}` },
                    { href: 'coins.html', label: `🟡 ${t('coins')}` },
                    { href: 'my-group.html', label: `👥 ${t('my_group')}` },
                    { href: 'tests.html', label: `📝 ${t('tests')}` },
                    { href: 'profile.html', label: `👤 ${t('profile')}` },
                    { href: 'my-badges.html', label: `🏅 ${t('my_badges')}` }
                ],
                parent: [
                    { href: 'child-progress.html', label: `📊 ${t('child_progress')}` },
                    { href: 'notifications.html', label: `🔔 ${t('notifications')}` }
                ]
            };
            const roleLinks = this.links[role] || [];

            // 3. Inject role links
            const roleContainer = document.getElementById('roleSpecificLinks');
            if (roleContainer) {
                const currentPath = window.location.pathname.split('/').pop();

                roleContainer.innerHTML = roleLinks.map(link => {
                    const isActive = currentPath === link.href ? 'active' : '';
                    return `<li><a href="${link.href}" class="nav-item ${isActive}">${link.label}</a></li>`;
                }).join('');
            }

            // 3.1 Highlight Dashboard link if on dashboard.html
            const currentPath = window.location.pathname.split('/').pop();
            const dashboardLink = document.querySelector('a[href="dashboard.html"]');
            if (dashboardLink && currentPath === 'dashboard.html') {
                dashboardLink.classList.add('active');
            }

            // 4. Initialize dynamic data and highlighting
            await this.initSidebarData();


        } catch (error) {
            console.error('SidebarLoader error:', error);
        }
    },

    async initSidebarData() {
        try {
            // Priority: LocalStorage (instant), then API (verified)
            const cachedName = localStorage.getItem('user_name');
            const cachedRole = localStorage.getItem('role');

            const nameEl = document.getElementById('sidebarUserName');
            const roleEl = document.getElementById('sidebarUserRole');
            const avatarEl = document.getElementById('sidebarAvatar');

            if (cachedName && nameEl) nameEl.innerText = cachedName;
            if (cachedRole && roleEl) roleEl.innerText = cachedRole;
            if (cachedName && avatarEl) avatarEl.innerText = cachedName[0].toUpperCase();

            // Fetch fresh data from backend
            // Assuming 'api' is globally available or imported
            if (typeof api !== 'undefined' && api.get) {
                const user = await api.get('/auth/me');
                if (user && user.full_name) {
                    if (nameEl) nameEl.innerText = user.full_name;
                    if (roleEl) roleEl.innerText = user.role;
                    if (avatarEl) avatarEl.innerText = user.full_name[0].toUpperCase();

                    // Update cache
                    localStorage.setItem('user_name', user.full_name);
                    localStorage.setItem('role', user.role);
                }
            }
        } catch (error) {
            console.error('Sidebar data init error:', error);
        }

        // Highlight active link
        const currentPath = window.location.pathname.split('/').pop();
        document.querySelectorAll('.nav-item').forEach(item => {
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
            }
        });
    },

    logout() {
        localStorage.clear();
        // Robust redirect to login.html
        const path = window.location.pathname;
        if (path.includes('/pages/')) {
            window.location.href = '../../login.html';
        } else {
            window.location.href = 'login.html';
        }
    },

    addMobileToggle() {
        // 1. Create/Get Toggle Button
        let toggleBtn = document.querySelector('.menu-toggle');
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.className = 'menu-toggle';
            toggleBtn.innerHTML = '<i class="fas fa-bars"></i> '; // FontAwesome icon
            // Inline styles as backup
            toggleBtn.style.zIndex = '999999';
            toggleBtn.style.position = 'fixed';
            toggleBtn.style.bottom = '24px';
            toggleBtn.style.right = '24px';
            toggleBtn.style.display = 'flex';
            document.body.appendChild(toggleBtn);
        }

        // 2. Create/Get Overlay
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
        }

        // 3. Bind Events (only if sidebar exists and not already bound)
        const sidebar = document.querySelector('.sidebar');
        if (sidebar && !toggleBtn.hasAttribute('data-bound')) {
            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('active');
                overlay.classList.toggle('active');
                toggleBtn.innerHTML = sidebar.classList.contains('active') ? '✕' : '☰';
            });

            overlay.addEventListener('click', () => {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
                toggleBtn.innerHTML = '☰';
            });

            toggleBtn.setAttribute('data-bound', 'true');
        }
    }
};

// Global logout for onclick handlers
window.logout = () => SidebarLoader.logout();

// Auto-init when script is loaded
document.addEventListener('DOMContentLoaded', () => SidebarLoader.init());
