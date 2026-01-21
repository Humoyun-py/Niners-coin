const StudentModule = {
    // Helper to get translation or fallback
    t: (key, params) => (window.t ? window.t(key, params) : key),

    initDashboard() {
        this.fetchDashboardData();
        this.loadTests();
        this.loadMyClassInfo();
        this.loadClassmatesLeaderboard();
        this.initializeWordOfTheDay();
        this.initializeMotivation();

        // Notification Polling
        this.checkNotifications();
        setInterval(() => this.checkNotifications(), 2000);
    },

    initializeMotivation() {
        const quotes = [
            { text: "Success is not final, failure is not fatal: it is the courage to continue that counts.", author: "Winston Churchill" },
            { text: "The beautiful thing about learning is that no one can take it away from you.", author: "B.B. King" },
            { text: "Education is the most powerful weapon which you can use to change the world.", author: "Nelson Mandela" },
            { text: "Believe you can and you're halfway there.", author: "Theodore Roosevelt" },
            { text: "Language is the blood of the soul into which thoughts run and out of which they grow.", author: "Oliver Wendell Holmes" }
        ];

        const dayOfYear = Math.floor((new Date() - new Date(new Date().getFullYear(), 0, 0)) / 1000 / 60 / 60 / 24);
        const dailyQuote = quotes[dayOfYear % quotes.length];

        const quoteEl = document.getElementById('dailyQuote');
        const authorEl = document.getElementById('quoteAuthor');

        if (quoteEl) quoteEl.innerText = `"${dailyQuote.text}"`;
        if (authorEl) authorEl.innerText = `— ${dailyQuote.author}`;
    },

    updateRankProgress(rank, xp = 0) {
        const progressEl = document.getElementById('rankProgress');
        const rankText = document.getElementById('rankText');
        const nextRankText = document.getElementById('nextRankText');
        const xpLabel = document.querySelector('.xp-label-current');
        const xpMaxLabel = document.querySelector('.xp-label-max');

        const ranks = [
            { name: 'Newbie', min: 0, max: 1000 },
            { name: 'Intermediate', min: 1000, max: 2500 },
            { name: 'Advanced', min: 2500, max: 5000 },
            { name: 'Expert', min: 5000, max: 10000 }
        ];

        let currentRank = ranks.find(r => r.name === rank) || ranks[0];
        let nextRank = ranks[ranks.indexOf(currentRank) + 1] || currentRank;

        let progress = ((xp - currentRank.min) / (currentRank.max - currentRank.min)) * 100;
        progress = Math.max(0, Math.min(100, progress));

        if (progressEl) progressEl.style.width = `${progress}%`;
        if (rankText) rankText.innerText = rank;
        if (nextRankText) nextRankText.innerText = rank === 'Expert' ? 'Max Level Reached!' : `Next: ${nextRank.name} (${nextRank.min} XP)`;

        if (xpLabel) xpLabel.innerText = `${xp} XP`;
        if (xpMaxLabel) xpMaxLabel.innerText = `${currentRank.max} XP`;
    },

    initializeWordOfTheDay() {
        const words = [
            { word: "Persist", pronunciation: "/pəˈsɪst/", type: "verb", definition: "To continue firmly in an opinion or a course of action in spite of difficulty or opposition.", usage: "Keep persisting and you will earn more coins!" },
            { word: "Resilient", pronunciation: "/rɪˈzɪliənt/", type: "adj", definition: "Able to withstand or recover quickly from difficult conditions.", usage: "English learners must be resilient in their studies!" },
            { word: "Eloquence", pronunciation: "/ˈeləkwəns/", type: "noun", definition: "Fluent or persuasive speaking or writing.", usage: "Mastering vocabulary leads to great eloquence." }
        ];

        // Pick a word based on the date
        const dayOfYear = Math.floor((new Date() - new Date(new Date().getFullYear(), 0, 0)) / 1000 / 60 / 60 / 24);
        const dailyWord = words[dayOfYear % words.length];

        const wordEl = document.getElementById('dailyWord');
        const pronEl = document.getElementById('dailyPron');
        const defEl = document.getElementById('dailyDef');
        const usageEl = document.getElementById('dailyUsage');

        if (wordEl) wordEl.innerText = dailyWord.word;
        if (pronEl) pronEl.innerText = `${dailyWord.pronunciation} • ${dailyWord.type}`;
        if (defEl) defEl.innerText = `"${dailyWord.definition}"`;
        if (usageEl) usageEl.innerHTML = `Usage: ${dailyWord.usage}`;
    },

    async initShop() {
        this.fetchDashboardData(); // Sync balance
        try {
            const items = await api.get('/student/shop/items');
            const container = document.getElementById('shopContainer');

            if (!container) return; // fail safe if not on shop page

            if (items.length === 0) {
                container.innerHTML = `<p style="text-align:center; grid-column: 1/-1;">${this.t('shop_empty')}</p>`;
                return;
            }

            container.innerHTML = items.map(item => {
                // Fix image path - ensure it starts with /uploads/ if it's a local shop image
                let imgSrc = item.image_url || '';
                if (!imgSrc) {
                    imgSrc = 'https://via.placeholder.com/150?text=No+Image';
                } else if (!imgSrc.startsWith('http') && !imgSrc.startsWith('data:')) {
                    // It's a local path
                    // clean up leads
                    if (imgSrc.startsWith('/')) imgSrc = imgSrc.substring(1);

                    if (imgSrc.startsWith('uploads/')) {
                        imgSrc = '/' + imgSrc;
                    } else if (imgSrc.startsWith('shop/')) {
                        imgSrc = '/uploads/' + imgSrc;
                    } else {
                        // assume it's just a filename
                        imgSrc = '/uploads/shop/' + imgSrc;
                    }
                }

                return `
                <div class="shop-item">
                    <img src="${imgSrc}" 
                         class="item-image" 
                         alt="${item.name}"
                         onerror="this.onerror=null; this.src='https://via.placeholder.com/150/cccccc/666666?text=Image+Error';">
                    <h4>${item.name}</h4>
                    <div class="item-price">${item.price} 🟡</div>
                    <p style="font-size: 0.8rem; color: #666;">${item.stock === -1 ? this.t('unlimited') : item.stock + ' ' + this.t('stock_left')}</p>
                    <button class="btn btn-primary" style="width: 100%; margin-top: 10px;" 
                        onclick="StudentModule.buyItem(${item.id}, '${item.name}', ${item.price})">${this.t('buy_action')}</button>
                </div>
            `}).join('');
        } catch (e) {
            console.error(e);
            const c = document.getElementById('shopContainer');
            if (c) c.innerHTML = `<p>${this.t('loading_error')}</p>`;
        }
    },

    buyItem(itemId, name, price) {
        if (!confirm(this.t('confirm_purchase_query', { name: name, price: price }))) return;

        api.post('/student/shop/buy', { item_id: itemId })
            .then(res => {
                this.showNotification(this.t('purchase_success_title'), res.msg);
                this.initShop();
            })
            .catch(err => {
                this.showNotification(this.t('error_title'), err.message, 'error');
            });
    },

    async fetchDashboardData() {
        try {
            const data = await api.get('/student/dashboard');
            if (data && !data.msg) {
                this.updateStats(data);
                if (document.getElementById('activityList')) {
                    this.updateActivity(data.recent_activity);
                }

                // Keep track for polling
                if (!localStorage.getItem('lastCoinBalance')) {
                    localStorage.setItem('lastCoinBalance', data.balance);
                }
            }
        } catch (e) { console.error("Dashboard fetch error:", e); }
    },

    isPolling: false,

    async checkNotifications() {
        if (this.isPolling) return;
        this.isPolling = true;

        try {
            const notifications = await api.get('/student/notifications');
            if (notifications) {
                // Filter unread
                const unread = notifications.filter(n => !n.is_read);

                for (const n of unread) {
                    // Show notification
                    this.showNotification(n.title, n.message);

                    // Mark as read immediately
                    await api.post(`/student/notifications/${n.id}/read`, {});
                }
            }
        } catch (e) {
            console.error("Notification poll error", e);
            // Optional: uncomment to see errors on screen
            // this.showNotification('Error', e.message, 'error');
        }
        finally { this.isPolling = false; }
    },

    async checkForCoinUpdates() {
        try {
            // Just sync balance silently
            const data = await api.get('/student/dashboard');
            const currentBalance = data.balance;

            // Update UI if changed
            const lastBalance = parseFloat(localStorage.getItem('lastCoinBalance') || 0);
            if (currentBalance !== lastBalance) {
                this.updateStats(data);
                this.fetchDashboardData(); // Refresh activity log too
            }
            localStorage.setItem('lastCoinBalance', currentBalance);
        } catch (e) { console.error("Polling error", e); }
    },

    showNotification(title, message, type = 'success') {
        const existing = document.querySelector('.modal-overlay');
        if (existing) existing.remove();

        const emoji = type === 'success' ? '✨' : '⚠️';
        const titleColor = type === 'success' ? 'var(--primary)' : '#e74c3c';

        const modalHTML = `
            <div class="modal-overlay active">
                <div class="modal-box" style="text-align: center; border-top: 5px solid ${titleColor}">
                    <div style="font-size: 4rem; margin-bottom: 10px;">${emoji}</div>
                    <div class="modal-title" style="margin-bottom: 10px; color: ${titleColor};">${title}</div>
                    <p>${message}</p>
                    <button class="btn btn-primary" style="margin-top: 20px; background: ${titleColor}; border: none;" onclick="this.closest('.modal-overlay').remove()">OK</button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    },

    updateStats(data) {
        const balance = parseFloat(data.balance).toFixed(2);
        const total = parseFloat(data.total_earned).toFixed(2);

        if (document.getElementById('coinBalance')) document.getElementById('coinBalance').innerText = `${balance} 🟡`;
        if (document.getElementById('userBalance')) document.getElementById('userBalance').innerText = `${balance} 🟡`; // For shop page
        if (document.getElementById('totalCoins')) document.getElementById('totalCoins').innerText = total;
        if (document.getElementById('rank')) document.getElementById('rank').innerText = data.rank;
        if (document.getElementById('streakCount')) document.getElementById('streakCount').innerText = `${data.streak} Day`;

        // Update new premium components
        this.updateRankProgress(data.rank, data.xp);
    },

    updateActivity(activity) {
        const container = document.getElementById('activityList');
        if (!container) return;

        if (activity.length === 0) {
            container.innerHTML = `<p class="text-muted">${this.t('no_activity')}</p>`;
            return;
        }
        container.innerHTML = activity.map(item => `
            <div style="padding: 12px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between;">
                <span>${item.source}</span>
                <b style="color: ${item.type === 'earn' ? '#2ecc71' : '#e74c3c'}">
                    ${item.amount > 0 ? '+' : ''}${item.amount} 🟡
                </b>
            </div>
        `).join('');
    },

    async loadTests() {
        const container = document.getElementById('testList');
        if (!container) return;

        try {
            const tests = await api.get('/game/tests');
            if (tests && tests.length > 0) {
                container.innerHTML = tests.map(t => `
                    <div class="card" style="padding: 20px; background: white; margin-bottom: 12px; border-left: 5px solid var(--primary);">
                        <div style="display:flex; justify-content:space-between;">
                            <h4>${t.title}</h4>
                            <span class="coin-badge">${t.reward} 🟡</span>
                        </div>
                        <p style="font-size: 0.8rem; color: #666;">${this.t('teacher_prefix')}: ${t.teacher}</p>
                        <button class="btn btn-secondary" style="margin-top: 10px;" onclick="StudentModule.startTest(${t.id})">${this.t('start_test')}</button>
                    </div>
                `).join('');
            }
        } catch (e) { console.error("Load tests error:", e); }
    },

    async startTest(testId) {
        const score = prompt(this.t('enter_test_score'));
        if (score === null) return;
        const res = await api.post(`/game/tests/${testId}/submit`, { score: parseInt(score) });
        alert(res.msg);
        this.loadTests();
    },

    async loadMyClassInfo() {
        const container = document.getElementById('myClassContainer');
        if (!container) return; // Only if element exists (I will add it to dashboard HTML)

        try {
            const topics = await api.get('/student/my-group/topics');

            container.innerHTML = `
                <div class="card" style="background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 24px; border-radius: var(--radius-lg);">
                    <h3>${this.t('my_group_topics_title')}</h3>
                    <p>${this.t('my_group_topics_desc')}</p>
                    <button class="btn" style="background: white; color: var(--primary); border: none; margin-top: 15px;" 
                        onclick="StudentModule.openTopicsModal()">${this.t('view_topics')}</button>
                </div>
            `;

            this._cachedTopics = topics;

        } catch (e) {
            container.innerHTML = `
                <div class="card" style="padding: 24px; border-radius: var(--radius-lg); border: 1px dashed #ccc; text-align: center;">
                    <p class="text-muted">${this.t('not_in_group')}</p>
                </div>
            `;
        }
    },

    openTopicsModal() {
        const topics = this._cachedTopics || [];

        const topicsList = topics.length ? topics.map(t => `
            <div style="border-bottom: 1px solid #eee; padding: 15px 0;">
                <h4 style="margin-bottom: 5px;">${t.title}</h4>
                <div style="font-size: 0.9rem; color: #555;">${t.content}</div>
                <div style="font-size: 0.75rem; color: #999; margin-top: 5px;">${t.date}</div>
            </div>
        `).join('') : `<p>${this.t('no_topics_yet')}</p>`;

        const modalHTML = `
            <div class="modal-overlay active">
                <div class="modal-box" style="width: 600px; max-width: 95%;">
                    <div class="modal-header">
                        <div class="modal-title">${this.t('group_topics_modal_title')}</div>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
                        ${topicsList}
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    },

    testNotification() {
        api.post('/student/test-notification', {})
            .then(res => console.log(res.msg))
            .catch(err => alert("Error: " + err.message));
    },

    async loadMyHomework() {
        const container = document.getElementById('homeworkList');
        if (!container) return;

        try {
            const homeworks = await api.get('/student/homework');

            if (homeworks.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 40px;">
                        <div style="font-size: 3rem; margin-bottom: 10px;">📚</div>
                        <p class="text-muted">Hozircha vazifa yo'q</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = homeworks.map(hw => {
                const isOverdue = hw.deadline && new Date(hw.deadline) < new Date();
                const statusBadge = hw.submitted
                    ? '<span style="background: #2ecc71; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">✓ Yuborilgan</span>'
                    : isOverdue
                        ? '<span style="background: #e74c3c; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">⏰ Muddati o\'tgan</span>'
                        : '<span style="background: #f39c12; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">⏳ Kutilmoqda</span>';

                return `
                    <div class="card" style="margin-bottom: 16px; border-left: 4px solid ${hw.submitted ? '#2ecc71' : '#f39c12'};">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                            <div>
                                <h4 style="margin-bottom: 4px;">${hw.class_name}</h4>
                                <p style="font-size: 0.85rem; color: #666;">
                                    ${hw.deadline ? '📅 Muddat: ' + new Date(hw.deadline).toLocaleDateString('uz-UZ') : 'Muddat yo\'q'}
                                </p>
                            </div>
                            ${statusBadge}
                        </div>
                        <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                            <strong>Vazifa:</strong>
                            <p style="margin-top: 8px; white-space: pre-wrap;">${hw.description}</p>
                        </div>
                        ${hw.submitted ? `
                            <div style="background: #e8f5e9; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                                <strong style="color: #2ecc71;">Sizning javobingiz:</strong>
                                <p style="margin-top: 8px; white-space: pre-wrap;">${hw.submission_content}</p>
                                <p style="font-size: 0.75rem; color: #666; margin-top: 4px;">
                                    Yuborilgan vaqt: ${new Date(hw.submission_date).toLocaleString('uz-UZ')}
                                </p>
                            </div>
                        ` : `
                            <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                                <button class="btn" style="flex: 1; background: #3498db; color: white;" 
                                    onclick="document.getElementById('file_${hw.id}').click()">
                                    📎 Rasm Yuklash
                                </button>
                                <input type="file" id="file_${hw.id}" accept="image/*" style="display: none;" 
                                    onchange="StudentModule.handleFileUpload(${hw.id}, this)">
                                
                                <button class="btn" style="flex: 1; background: #95a5a6; color: white;" 
                                    onclick="StudentModule.submitPaper(${hw.id})">
                                    📝 Qog'ozda Bajardim
                                </button>
                            </div>
                            <div id="preview_${hw.id}" style="margin-bottom: 10px; font-size: 0.9rem; color: #2ecc71;"></div>
                            
                            <textarea id="hw_${hw.id}" class="form-control" 
                                placeholder="Yoki javobingizni bu yerga yozing..." 
                                style="min-height: 80px; margin-bottom: 12px;"></textarea>
                            
                            <button class="btn btn-primary" onclick="StudentModule.submitHomework(${hw.id})" 
                                style="width: 100%; padding: 12px;" id="btn_submit_${hw.id}">
                                📤 Javobni Yuborish
                            </button>
                        `}
                    </div>
                `;
            }).join('');
        } catch (error) {
            console.error('Load homework error:', error);
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #e74c3c;">
                    <p>Vazifalarni yuklashda xatolik yuz berdi</p>
                </div>
            `;
        }
    },

    handleFileUpload(hwId, input) {
        if (input.files && input.files[0]) {
            document.getElementById(`preview_${hwId}`).innerText = `📸 Rasm tanlandi: ${input.files[0].name}`;
        }
    },

    async submitPaper(hwId) {
        if (!confirm("Vazifani qog'ozda bajarganingizni tasdiqlaysizmi?")) return;

        const formData = new FormData();
        formData.append('type', 'paper');
        formData.append('content', '');

        this._sendHomework(hwId, formData);
    },

    async submitHomework(hwId) {
        const textarea = document.getElementById(`hw_${hwId}`);
        const fileInput = document.getElementById(`file_${hwId}`);

        if (!textarea) return;

        const content = textarea.value.trim();
        const file = fileInput && fileInput.files[0];

        if (!content && !file) {
            this.showNotification('⚠️ Diqqat', "Iltimos, rasm yuklang, matn yozing yoki 'Qog'ozda bajardim' tugmasini bosing", 'error');
            return;
        }

        let imageBase64 = null;

        if (file) {
            // Check file size (max 2MB)
            if (file.size > 2 * 1024 * 1024) {
                this.showNotification('❌ Xato', 'Rasm juda katta! Maksimal 2MB bo\'lishi kerak.', 'error');
                return;
            }

            // Convert to Base64
            try {
                imageBase64 = await new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(file);
                });
            } catch (error) {
                this.showNotification('❌ Xato', 'Rasmni yuklashda xatolik', 'error');
                return;
            }
        }

        this._sendHomework(hwId, content, imageBase64);
    },

    async _sendHomework(hwId, content, imageBase64) {
        try {
            const payload = {
                type: imageBase64 ? 'file' : 'text',
                content: content || '',
                image_base64: imageBase64
            };

            const result = await api.post(`/student/homework/${hwId}/submit`, payload);

            this.showNotification('✅ Muvaffaqiyat', result.msg);
            this.loadMyHomework();
        } catch (error) {
            this.showNotification('❌ Xato', error.message, 'error');
        }
    },

    async loadClassmatesLeaderboard() {
        try {
            const container = document.getElementById('classmatesLeaderboard');
            if (!container) return;

            const response = await api.get('/student/classmates');
            const classmates = response.classmates || [];

            const countEl = document.getElementById('classmateCount');
            if (countEl) countEl.innerText = `${classmates.length} ta o'quvchi`;

            if (classmates.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: var(--text-muted);">Sinfdoshlar yo\'q</p>';
                return;
            }

            // Sort by coins (highest first)
            classmates.sort((a, b) => b.coin_balance - a.coin_balance);

            container.innerHTML = classmates.map((student, index) => `
                <div style="display: flex; align-items: center; gap: 15px; padding: 12px; background: ${index < 3 ? '#fff9e6' : 'white'}; border-radius: 12px; border: 1px solid ${index < 3 ? '#ffd700' : '#e5e7eb'};">
                    <div style="font-size: 1.2rem; font-weight: 700; color: ${index === 0 ? '#FFD700' : index === 1 ? '#C0C0C0' : index === 2 ? '#CD7F32' : '#999'}; min-width: 30px;">
                        ${index + 1}
                    </div>
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;">
                        ${student.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #1f2937;">${student.full_name}</div>
                        <div style="font-size: 0.85rem; color: #6b7280;">@${student.username}</div>
                    </div>
                    <div style="font-weight: 700; color: #f59e0b; font-size: 1.1rem;">
                        ${parseFloat(student.coin_balance).toFixed(1)} 🟡
                    </div>
                </div>
            `).join('');

        } catch (error) {
            console.error('Leaderboard error:', error);
            const container = document.getElementById('classmatesLeaderboard');
            if (container) container.innerHTML = '<p style="text-align: center; color: red;">Xatolik</p>';
        }
    }
};
