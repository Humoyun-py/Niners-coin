const TeacherModule = {
    // Helper to get translation or fallback
    t: (key) => (window.t ? window.t(key) : key),

    async initDashboard() {
        const nameEl = document.getElementById('userName');
        if (nameEl) nameEl.innerText = 'Yuklanmoqda...';

        try {
            const data = await api.get('/teacher/dashboard');
            if (data && !data.msg) {
                if (nameEl) nameEl.innerText = data.teacher_name || 'Ustoz';
                document.getElementById('classCount').innerText = data.class_count;
                document.getElementById('rating').innerText = `${data.rating} ⭐`;

                const limitEl = document.getElementById('coinLimit');
                if (limitEl) {
                    limitEl.innerText = `${data.issued_today} / ${data.daily_limit} 🟡`;
                }

                this.renderRecentRewards(data.recent_rewards || []);
                this._cachedClasses = data.classes;
                this.renderClasses(data.classes);
                this.initMyStudentsSection(data.classes);
            }
        } catch (e) {
            console.error("Dashboard init error:", e);
            if (nameEl) nameEl.innerText = 'Xatolik!';
        }
    },

    renderRecentRewards(rewards) {
        const container = document.getElementById('recentRewardsContainer');
        if (!container) return;

        if (rewards.length === 0) {
            container.innerHTML = '<p class="text-muted">Hali koinlar berilmadi.</p>';
            return;
        }

        container.innerHTML = rewards.map(r => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid #f0f0f0;">
                <div>
                    <span style="font-weight: 700;">${r.student_name}</span>
                    <span style="font-size: 0.8rem; color: #888; margin-left: 10px;">${r.source}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="color: var(--secondary); font-weight: 700;">+${r.amount} 🟡</span>
                    <span style="font-size: 0.75rem; color: #aaa;">${r.date}</span>
                </div>
            </div>
        `).join('');
    },

    renderClasses(classes) {
        const tbody = document.getElementById('classList');
        if (!tbody) return;

        // Wrap the existing table body in a wrapper if not already
        const table = tbody.closest('table');
        if (table && !table.parentElement.classList.contains('table-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-wrapper';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }

        if (!classes || classes.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;">${this.t('no_classes')}</td></tr>`;
            return;
        }
        tbody.innerHTML = classes.map(c => {
            // Format schedule display
            let scheduleText = 'No Schedule';
            if (c.schedule_days && c.schedule_time) {
                scheduleText = `${c.schedule_days} - ${c.schedule_time}`;
            } else if (c.schedule_days) {
                scheduleText = c.schedule_days;
            } else if (c.schedule_time) {
                scheduleText = c.schedule_time;
            }

            return `
            <tr style="border-bottom: 1px solid var(--border-light);">
                <td style="padding: 12px; font-weight: 600;">${c.name}</td>
                <td style="padding: 12px;">${c.student_count} Students</td>
                <td style="padding: 12px; color: var(--primary);">${scheduleText}</td>
                <td style="padding: 12px;">
                    <button class="btn btn-secondary" style="padding: 6px 16px; font-size: 0.8rem;" onclick="TeacherModule.manageClass(${c.id})">Boshqarish</button>
                </td>
            </tr>
        `}).join('');
    },

    initMyStudentsSection(classes) {
        const container = document.getElementById('myStudentsContainer');
        if (!container) return;

        if (!classes || classes.length === 0) {
            container.innerHTML = '<p class="text-muted">Guruhlar mavjud emas.</p>';
            return;
        }

        const options = classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        container.innerHTML = `
            <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 20px;">
                <label style="font-weight: 700;">${this.t('select_group_label')}:</label>
                <select id="studentsGroupSelect" class="form-control" style="max-width: 250px;" onchange="TeacherModule.loadStudentsForSection(this.value)">
                    <option value="">-- ${this.t('select_group_label')} --</option>
                    ${options}
                </select>
            </div>
            <div id="studentsListGrid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px;">
                <p class="text-muted">Guruhni tanlab o'quvchilarni ko'ring.</p>
            </div>
        `;
    },

    async loadStudentsForSection(classId) {
        if (!classId) return;
        const grid = document.getElementById('studentsListGrid');
        grid.innerHTML = '<p>Yuklanmoqda...</p>';

        try {
            const data = await api.get(`/teacher/classes/${classId}`);
            if (data.students.length === 0) {
                grid.innerHTML = '<p>Guruhda o\'quvchilar yo\'q.</p>';
                return;
            }

            grid.innerHTML = data.students.map(s => `
                <div class="card" style="padding: 16px; display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <div style="font-weight: 700;">${s.full_name}</div>
                        <div style="font-size: 0.8rem; color: #666;">${parseFloat(s.balance).toFixed(2)} 🟡 | ${s.rank}</div>
                    </div>
                    <button class="btn btn-sm btn-primary" onclick="TeacherModule.quickAward(${s.id}, '${s.full_name}')">${this.t('encourage_btn')}</button>
                </div>
            `).join('');
        } catch (e) {
            grid.innerHTML = '<p>Xatolik yuz berdi.</p>';
        }
    },

    createModal(title, content, onSave, saveText = 'Save') {
        const existing = document.querySelector('.modal-overlay');
        if (existing) existing.remove();

        const modalHTML = `
            <div class="modal-overlay active">
                <div class="modal-box" style="width: 600px; max-width: 95%;">
                    <div class="modal-header">
                        <div class="modal-title">${title}</div>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
                        ${content}
                    </div>
                    <div style="margin-top: 24px; display: flex; justify-content: flex-end; gap: 12px;">
                        <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Bekor qilish</button>
                        ${onSave ? `<button class="btn btn-primary" id="modalSaveBtn">${saveText}</button>` : ''}
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        if (onSave) {
            document.getElementById('modalSaveBtn').onclick = async () => {
                const btn = document.getElementById('modalSaveBtn');
                btn.innerHTML = 'Bajarilmoqda...';
                btn.disabled = true;
                await onSave();
                const modal = document.querySelector('.modal-overlay');
                if (modal) modal.remove();
            };
        }
    },

    async awardCoinsToStudent() {
        if (!this._cachedClasses || this._cachedClasses.length === 0) {
            try {
                const data = await api.get('/teacher/dashboard');
                this._cachedClasses = data.classes || [];
            } catch (e) {
                console.error("Failed to fetch classes for modal:", e);
            }
        }

        const classes = this._cachedClasses || [];
        const options = classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

        const formContent = `
            <div class="input-group">
                <label class="input-label">1. Guruhni tanlang</label>
                <select id="awardClassId" class="form-control" onchange="TeacherModule.updateStudentSearch(this.value)">
                    <option value="">-- Guruhni tanlang --</option>
                    ${options}
                </select>
            </div>
            <div class="input-group">
                <label class="input-label">2. O'quvchi ismini yozing</label>
                <input type="text" id="studentSearchInput" class="form-control" list="studentNamesList" placeholder="Qidirish..." autocomplete="off">
                <datalist id="studentNamesList"></datalist>
            </div>
            <div class="input-group">
                <label class="input-label">3. Miqdor (Coin)</label>
                <input type="number" id="awardAmount" class="form-control" value="5" min="0" step="0.5">
            </div>
            <div class="input-group">
                <label class="input-label">4. Sabab</label>
                <input type="text" id="awardReason" class="form-control" placeholder="Darsdagi faollik uchun" value="Darsdagi faollik">
            </div>
        `;

        this.createModal('Coin Berish (Rag\'batlantirish)', formContent, async () => {
            const searchVal = document.getElementById('studentSearchInput').value;
            const amount = document.getElementById('awardAmount').value;
            const source = document.getElementById('awardReason').value;

            // Find student ID from datalist/cached data
            const option = document.querySelector(`#studentNamesList option[value="${searchVal}"]`);
            const studentId = option ? option.getAttribute('data-id') : null;

            if (!studentId || !amount) {
                alert("Iltimos, o'quvchini ro'yxatdan tanlang va miqdorni kiriting.");
                return;
            }

            try {
                const res = await api.post('/teacher/award-coins', {
                    student_id: parseInt(studentId),
                    amount: parseFloat(amount),
                    source: source || 'Activity'
                });
                alert(res.msg);
                if (typeof this.initDashboard === 'function' && window.location.pathname.includes('dashboard.html')) {
                    this.initDashboard();
                }
            } catch (e) { alert("Xatolik: " + e.message); }
        }, 'Yuborish');
    },

    async updateStudentSearch(classId) {
        const datalist = document.getElementById('studentNamesList');
        const searchInput = document.getElementById('studentSearchInput');

        if (!classId) {
            datalist.innerHTML = '';
            searchInput.value = '';
            searchInput.placeholder = '-- Guruhni tanlang --';
            return;
        }

        searchInput.value = '';
        searchInput.placeholder = 'Yuklanmoqda...';

        try {
            const data = await api.get(`/teacher/classes/${classId}`);
            datalist.innerHTML = data.students.map(s => `<option value="${s.full_name}" data-id="${s.id}">${s.username ? '@' + s.username : ''}</option>`).join('');
            searchInput.placeholder = 'O\'quvchi ismini tanlang';
        } catch (e) {
            searchInput.placeholder = 'Xatolik!';
        }
    },

    manageClass(classId) {
        window.location.href = `attendance.html?classId=${classId}`;
    },

    quickAward(studentId, studentName) {
        const formContent = `
            <p style="margin-bottom: 15px;">O'quvchi: <strong style="color: var(--primary);">${studentName}</strong></p>
            <div class="input-group">
                <label class="input-label">Coin Miqdori</label>
                <input type="number" id="quickAmount" class="form-control" value="5" step="0.25">
            </div>
            <div class="input-group">
                <label class="input-label">Sabab</label>
                <input type="text" id="quickReason" class="form-control" value="Darsdagi faollik">
            </div>
        `;

        this.createModal('Rag\'batlantirish', formContent, async () => {
            const amount = document.getElementById('quickAmount').value;
            const reason = document.getElementById('quickReason').value;

            try {
                const res = await api.post('/teacher/award-coins', {
                    student_id: parseInt(studentId),
                    amount: parseFloat(amount),
                    source: reason
                });
                alert(res.msg);
                if (typeof this.initDashboard === 'function' && window.location.pathname.includes('dashboard.html')) {
                    this.initDashboard();
                }
            } catch (e) { alert("Xatolik: " + e.message); }
        }, 'Yuborish');
    },

    async manageTopics(classId) {
        try {
            const topics = await api.get(`/teacher/classes/${classId}/topics`);

            const list = topics.length ? topics.map(t => `
                <div style="border:1px solid #eee; padding:15px; margin-bottom:12px; border-radius:12px; background:white; position:relative;">
                     <h4 style="margin:0 0 8px; color:var(--primary);">${t.title}</h4>
                     <p style="font-size:0.9rem; color:#444; margin:0;">${t.content}</p>
                     <div style="font-size:0.7rem; color:#aaa; margin-top:8px;">${t.date}</div>
                </div>
            `).join('') : '<p style="text-align:center; padding:20px; color:#888;">Hozircha vazifalar yo\'q.</p>';

            const content = `
                <div style="display:flex; justify-content:flex-end; margin-bottom:15px;">
                    <button class="btn btn-primary" onclick="TeacherModule.showAddTopicForm(${classId})">+ Vazifa Qo'shish</button>
                </div>
                <div style="max-height:50vh; overflow-y:auto; background:#f9f9f9; padding:15px; border-radius:12px; border:1px solid #eee;">
                    ${list}
                </div>
            `;

            this.createModal('Uy vazifalari va Mavzular', content, null);
        } catch (e) { alert("Xatolik: " + e.message); }
    },

    showAddTopicForm(classId) {
        const content = `
            <div class="input-group"><label class="input-label">Mavzu/Vazifa nomi</label><input type="text" id="topicTitle" class="form-control" placeholder="Masalan: Unit 5: Grammar"></div>
            <div class="input-group"><label class="input-label">Tafsilotlar</label><textarea id="topicContent" class="form-control" rows="5" placeholder="Vazifa haqida to'liq ma'lumot..."></textarea></div>
        `;
        this.createModal('Yangi Vazifa Qo\'shish', content, async () => {
            const title = document.getElementById('topicTitle').value;
            const content = document.getElementById('topicContent').value;
            if (!title || !content) return alert("Barcha maydonlarni to'ldiring");

            try {
                await api.post(`/teacher/classes/${classId}/topics`, { title, content });
                alert("Vazifa muvaffaqiyatli qo'shildi! 📚");
                setTimeout(() => TeacherModule.manageTopics(classId), 500);
            } catch (e) { alert("Xatolik: " + e.message); }
        }, 'Saqlash');
    },

    async initAttendancePage() {
        try {
            const data = await api.get('/teacher/dashboard');
            const container = document.getElementById('attendanceContainer');
            if (!container) return;

            // Check for URL param
            const urlParams = new URLSearchParams(window.location.search);
            const classIdParam = urlParams.get('classId');

            if (classIdParam) {
                // Find class name from data
                const cls = data.classes.find(c => c.id == classIdParam);
                if (cls) {
                    this.loadAttendanceForm(cls.id, cls.name);
                    return; // Stop here, don't show the list
                }
            }

            if (data.classes.length === 0) {
                container.innerHTML = '<div class="empty-state">Sizda hali guruhlar yo\'q.</div>';
                return;
            }

            // Render Class Cards
            const cards = data.classes.map(c => {
                // Format schedule display
                let scheduleText = 'No Schedule';
                if (c.schedule_days && c.schedule_time) {
                    scheduleText = `📅 ${c.schedule_days} | ⏰ ${c.schedule_time}`;
                } else if (c.schedule_days) {
                    scheduleText = `📅 ${c.schedule_days}`;
                } else if (c.schedule_time) {
                    scheduleText = `⏰ ${c.schedule_time}`;
                }

                return `
                <div class="card" style="padding: 24px; cursor: pointer; transition: transform 0.2s; border: 1px solid transparent; hover: border-color: var(--primary);" 
                    onclick="TeacherModule.loadAttendanceForm(${c.id})">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                        <div style="width: 50px; height: 50px; background: #eef2ff; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--primary); font-size: 1.5rem;">
                            👥
                        </div>
                        <span style="background: #e6fcf5; color: #0ca678; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;">Active</span>
                    </div>
                    <h3 style="margin: 0 0 8px 0;">${c.name}</h3>
                    <p style="color: var(--text-muted); margin: 0 0 8px 0; font-size: 0.9rem;">${c.student_count} ta o'quvchi</p>
                    <p style="color: var(--primary); margin: 0; font-size: 0.85rem; font-weight: 600;">${scheduleText}</p>
                    <button class="btn btn-primary" style="width: 100%; margin-top: 20px;">Davomat qilish</button>
                </div>
            `}).join('');

            container.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px;">
                    ${cards}
                </div>
            `;
        } catch (e) {
            console.error(e);
            document.getElementById('attendanceContainer').innerHTML = '<p>Yuklashda xatolik.</p>';
        }
    },

    async loadAttendanceForm(classId, className = null) {
        const container = document.getElementById('attendanceContainer');
        container.innerHTML = '<p>Yuklanmoqda...</p>';

        try {
            const data = await api.get(`/teacher/classes/${classId}`);
            // Use fetched name if not provided
            const finalClassName = className || data.name || 'Guruh';

            const rows = data.students.map(s => `
                <div class="attendance-card" style="background: white; border: 1px solid #eee; padding: 16px; border-radius: 12px; margin-bottom: 12px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 15px;">
                    <!-- Student Info -->
                    <div style="display: flex; align-items: center; gap: 12px; min-width: 200px; flex: 1;">
                        <div style="width: 45px; height: 45px; background: var(--primary-gradient); border-radius: 50%; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0;">
                            ${s.full_name[0]}
                        </div>
                        <div>
                            <div style="font-weight: 700; font-size: 1rem;">${s.full_name}</div>
                            <div style="font-size: 0.8rem; color: var(--text-muted);">ID: #${s.id}</div>
                            <div style="font-size: 0.85rem; color: var(--secondary); font-weight:600;">Balans: ${parseFloat(s.balance).toFixed(1)} 🟡</div>
                        </div>
                    </div>
                    
                    <!-- Controls Area -->
                    <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap; flex: 3; justify-content: flex-end;">
                        <!-- Status Toggles -->
                         <div style="border-right:1px solid #eee; padding-right:15px;">
                            <div class="attendance-toggles" style="display: flex; background: #f8f9fa; padding: 4px; border-radius: 8px; border: 1px solid #e9ecef;">
                                <label style="cursor: pointer; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 4px; position: relative;">
                                    <input type="radio" name="att_${s.id}" value="present" checked style="accent-color: #2ecc71; width: 14px; height: 14px;"> 
                                    <span>Bor</span>
                                </label>
                                <label style="cursor: pointer; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                                    <input type="radio" name="att_${s.id}" value="absent" style="accent-color: #e74c3c; width: 14px; height: 14px;"> 
                                    <span>Yo'q</span>
                                </label>
                                <label style="cursor: pointer; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                                    <input type="radio" name="att_${s.id}" value="late" style="accent-color: #f1c40f; width: 14px; height: 14px;"> 
                                    <span>Kech</span>
                                </label>
                            </div>
                        </div>

                        <!-- Extra Coins -->
                        <div style="display:flex; align-items:center; gap:10px; flex:1; min-width:280px;">
                            <div style="flex:1;">
                                <input type="text" id="reason_${s.id}" class="form-control" placeholder="Uyga vazifa / Faollik" style="font-size:0.85rem; padding:8px;">
                            </div>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span style="font-size:0.85rem; font-weight:600; color:#555; white-space:nowrap;">Coin qo'yish:</span>
                                <input type="number" id="coin_${s.id}" class="form-control" placeholder="0" min="0" step="1" style="font-size:0.9rem; padding:8px; width:70px; text-align:center; font-weight:700; color:var(--primary);">
                                <button class="btn btn-sm btn-success" title="Darhol yuborish" onclick="TeacherModule.sendIndividualCoins(this, ${s.id}, '${s.full_name.replace(/'/g, "\\'")}')" style="padding: 8px 12px;">Yuborish</button>
                            </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

            container.innerHTML = `
                <div style="margin-bottom: 24px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 15px;">
                    <div style="display: flex; align-items: center; gap: 16px;">
                        ${window.location.search.includes('classId') ?
                    `<button onclick="window.location.href='attendance.html'" class="btn btn-secondary" style="padding: 8px 16px;">← Hamma guruhlar</button>` :
                    `<button onclick="TeacherModule.initAttendancePage()" class="btn btn-secondary" style="padding: 8px 16px;">← Ortga</button>`
                }
                        <div>
                            <h2 style="margin: 0; font-size: 1.5rem;">${finalClassName}</h2>
                            <p style="margin: 0; color: var(--text-muted);">Sana: ${new Date().toLocaleDateString()}</p>
                        </div>
                    </div>
                    
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <div style="display: flex; align-items: center; gap: 8px; background: white; padding: 8px 16px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e1e4e8;" title="Faqat 'Bor' bo'lganlarga avtomatik beriladi">
                            <span style="font-weight: 600; color: #4b5563;">🎁 Davomat uchun:</span>
                            <input type="number" id="globalCoinInput" value="1" min="0" step="0.5" style="width: 60px; border: 1px solid #d1d5db; border-radius: 6px; padding: 4px 8px; font-weight: 700; text-align: center; color: var(--primary);">
                        </div>
                        <button class="btn btn-secondary" onclick="TeacherModule.manageTopics(${classId})">📚 Mavzular</button>
                    </div>
                </div>

                <div style="max-width: 1000px; margin: 0 auto;">
                    <!-- Scrollable Student List -->
                    <div style="max-height: 600px; overflow-y: auto; padding-right: 4px; margin-bottom: 20px;">
                        ${rows}
                    </div>
                    <div style="margin-top: 30px; padding: 20px; background: white; border-radius: 12px; box-shadow: 0 -5px 20px rgba(0,0,0,0.05); position: sticky; bottom: 20px; text-align: right; border-top: 1px solid #eee;">
                        <button class="btn btn-primary" style="padding: 14px 40px; font-size: 1.1rem; border-radius: 30px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);" onclick="TeacherModule.saveAttendance(${classId})">
                            ${this.t('save_changes')} ✅
                        </button>
                    </div>
                </div>
            `;
        } catch (e) {
            console.error(e);
            container.innerHTML = '<p>Xatolik yuz berdi. Qaytadan urinib ko\'ring.</p>';
        }
    },

    async saveAttendance(classId) {
        const selects = document.querySelectorAll('input[type="radio"]:checked');
        const globalCoin = parseFloat(document.getElementById('globalCoinInput')?.value) || 0;

        const records = Array.from(selects).map(radio => {
            const studentId = parseInt(radio.name.split('_')[1]);
            const status = radio.value;

            // Attendance Coin (only if present)
            let att_coins = (status === 'present') ? globalCoin : 0;

            // Bonus Coin
            const bonusInput = document.getElementById(`coin_${studentId}`);
            const reasonInput = document.getElementById(`reason_${studentId}`);

            const bonusAmount = parseFloat(bonusInput?.value) || 0;
            const bonusReason = reasonInput?.value || 'Qo\'shimcha faollik';

            return {
                student_id: studentId,
                status: status,
                coins: att_coins,
                bonus_amount: bonusAmount,
                bonus_reason: bonusReason
            };
        });

        try {
            const res = await api.post('/teacher/attendance', { class_id: classId, records });

            // Calculate totals for feedback
            const totalCoins = records.reduce((sum, r) => sum + r.coins + r.bonus_amount, 0);

            alert(`Davomat saqlandi! Jami ${totalCoins} coin berildi. 💰✅`);

            if (window.location.search.includes('classId')) {
                this.loadAttendanceForm(classId);
            } else {
                this.initAttendancePage();
            }
        } catch (e) { alert("Xatolik: " + e.message); }
    },

    async initHomeworkPage() {
        this.loadHomeworks();
    },

    async loadHomeworks() {
        try {
            const list = await api.get('/teacher/homework');
            const container = document.getElementById('homeworkList');
            if (!container) return;

            if (list.length === 0) {
                container.innerHTML = '<p class="text-muted" style="grid-column: 1/-1;">Hozircha uyga vazifalar yo\'q.</p>';
                return;
            }

            container.innerHTML = list.map(h => `
                <div class="card" style="display: flex; flex-direction: column;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <span class="badge" style="background:#E3F2FD; color:#1565C0;">${h.class_name}</span>
                        <span style="font-size: 0.8rem; color: #888;">${h.deadline ? 'Muddat: ' + h.deadline : 'Muddatsiz'}</span>
                    </div>
                    <p style="font-size: 1rem; color: var(--text-dark); margin-bottom: 15px; flex-grow: 1;">${h.description}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                        <span style="font-size: 0.75rem; color: #aaa;">Yaratildi: ${new Date(h.created_at).toLocaleDateString()}</span>
                        <button class="btn btn-sm btn-secondary" onclick="TeacherModule.viewSubmissions(${h.id})">📂 Javoblarni ko'rish</button>
                    </div>
                </div>
            `).join('');

        } catch (e) {
            console.error(e);
            const container = document.getElementById('homeworkList');
            if (container) container.innerHTML = '<p style="color:red">Xatolik yuz berdi.</p>';
        }
    },

    async showCreateHomeworkModal() {
        try {
            const dashboardData = await api.get('/teacher/dashboard');
            const classes = dashboardData.classes || [];
            if (classes.length === 0) return alert("Sizda guruhlar mavjud emas.");

            const options = classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

            const content = `
                <div class="input-group">
                    <label class="input-label">Qaysi Guruhga?</label>
                    <select id="hwClass" class="form-control">
                        ${options}
                    </select>
                </div>
                <div class="input-group">
                    <label class="input-label">Vazifa Matni</label>
                    <textarea id="hwDesc" class="form-control" rows="4" placeholder="Masalan: 12-betdagi 1-5 mashqlarni bajarish..."></textarea>
                </div>
                <div class="input-group">
                    <label class="input-label">Topshirish Muddati (Ixtiyoriy)</label>
                    <input type="date" id="hwDeadline" class="form-control">
                </div>
            `;

            this.createModal('Yangi Vazifa', content, async () => {
                const classId = document.getElementById('hwClass').value;
                const desc = document.getElementById('hwDesc').value;
                const deadline = document.getElementById('hwDeadline').value;

                if (!desc) return alert("Vazifa matnini kiriting!");

                try {
                    await api.post('/teacher/homework', {
                        class_id: classId,
                        description: desc,
                        deadline: deadline
                    });
                    alert("Vazifa muvaffaqiyatli yuklandi!");
                    this.loadHomeworks();
                } catch (e) {
                    alert("Xatolik: " + e.message);
                }
            });

        } catch (e) {
            alert("Guruhlarni yuklashda xatolik: " + e.message);
        }
    },

    createModal(title, content, onSave) {
        const existing = document.querySelector('.modal-overlay');
        if (existing) existing.remove();

        const modalHTML = `
            <div class="modal-overlay active">
                <div class="modal-box">
                    <div class="modal-header">
                        <div class="modal-title">${title}</div>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        ${content}
                    </div>
                    <div style="margin-top: 24px; display: flex; justify-content: flex-end; gap: 12px;">
                        <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Bekor qilish</button>
                        <button class="btn btn-primary" id="modalSaveBtn">Saqlash</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        document.getElementById('modalSaveBtn').onclick = async () => {
            const btn = document.getElementById('modalSaveBtn');
            btn.innerHTML = 'Saqlanmoqda...';
            btn.disabled = true;
            try {
                await onSave();
                document.querySelector('.modal-overlay')?.remove();
            } catch (e) {
                console.error(e);
                btn.innerHTML = 'Saqlash';
                btn.disabled = false;
            }
        };
    },

    async initStudentsPage() {
        try {
            const data = await api.get('/teacher/dashboard');
            this._cachedClasses = data.classes;
            const container = document.getElementById('studentsPageContainer');
            if (!container) return;

            const options = data.classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            container.innerHTML = `
                <div class="card" style="padding: 24px;">
                    <div style="display: flex; gap: 20px; align-items: center; margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px;">
                        <label style="font-weight: 700;">Guruh:</label>
                        <select class="form-control" style="max-width: 300px;" onchange="TeacherModule.loadStudentsListPage(this.value)">
                            <option value="">-- Guruhni tanlang --</option>
                            ${options}
                        </select>
                    </div>
                    <div id="studentsListArea">
                        <p class="text-muted">Guruhni tanlang va o'quvchilarni rag'batlantiring.</p>
                    </div>
                </div>
            `;
        } catch (e) { console.error(e); }
    },

    async loadStudentsListPage(classId) {
        if (!classId) return;
        const area = document.getElementById('studentsListArea');
        area.innerHTML = '<p>Yuklanmoqda...</p>';
        try {
            const data = await api.get(`/teacher/classes/${classId}`);
            const rows = data.students.map(s => `
                <tr style="border-bottom: 1px solid #eee;">
                    <td data-label="O'quvchi" style="padding: 15px;">
                        <div style="font-weight: 700;">${s.full_name}</div>
                        <div style="font-size: 0.75rem; color: #888;">ID: ${s.id} | @${s.username}</div>
                    </td>
                    <td data-label="Coinlar" style="padding: 15px;"><span class="coin-badge">${parseFloat(s.balance).toFixed(2)} 🟡</span></td>
                    <td data-label="Amal" style="padding: 15px;">
                         <button class="btn btn-sm btn-primary" onclick="TeacherModule.quickAward(${s.id}, '${s.full_name}')">✨ Rag'batlantirish</button>
                    </td>
                </tr>
            `).join('');

            area.innerHTML = `
                <div class="table-wrapper">
                    <table class="responsive-table" style="width: 100%; border-collapse: collapse;">
                        <thead><tr style="text-align: left; border-bottom: 2px solid #eee; color: #999; font-size: 0.8rem; text-transform: uppercase;">
                            <th style="padding: 15px;">O'quvchi</th><th style="padding: 15px;">Coinlar</th><th style="padding: 15px;">Amal</th>
                        </tr></thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            `;
        } catch (e) { area.innerHTML = '<p>Xatolik!</p>'; }
    },

    async sendIndividualCoins(btn, studentId, studentName) {
        const input = document.getElementById(`coin_${studentId}`);
        const reasonInput = document.getElementById(`reason_${studentId}`);
        const amount = parseFloat(input.value) || 0;
        const reason = reasonInput.value || "Qo'shimcha faollik";

        if (amount <= 0) return alert("Coin miqdori kiritilmadi!");

        if (!confirm(`${studentName} ga ${amount} coin yuborilsinmi?`)) return;

        // btn is passed directly
        const originalText = btn.innerText;
        btn.disabled = true;
        btn.innerText = 'Run...';

        try {
            const res = await api.post('/teacher/award-individual', {
                student_id: studentId,
                amount: amount,
                reason: reason
            });
            alert(`Muvaffaqiyatli! ${studentName} balans: ${res.new_balance.toFixed(1)} 🟡`);
            input.value = ''; // Clear input to avoid double send on bulk save
            reasonInput.value = '';
        } catch (e) {
            alert(e.message || "Xatolik yuz berdi");
        } finally {
            btn.disabled = false;
            btn.innerText = originalText;
        }
    },

    async viewSubmissions(hwId) {
        console.log("View Submissions clicked for:", hwId);
        const modal = document.getElementById('submissionsModal');
        modal.classList.add('active');
        this.loadSubmissions(hwId);
    },

    async loadSubmissions(hwId) {
        const container = document.getElementById('submissionsList');
        container.innerHTML = '<p class="text-center">Yuklanmoqda...</p>';

        try {
            const submissions = await api.get(`/teacher/homework/${hwId}/submissions`);
            if (submissions.length === 0) {
                container.innerHTML = '<p class="text-center text-muted">Hozircha javoblar yo\'q.</p>';
                return;
            }

            container.innerHTML = submissions.map(sub => `
                <div class="card" style="margin-bottom: 15px; border-left: 4px solid ${this._getStatusColor(sub.status)};">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div>
                            <strong>${sub.student_name}</strong>
                            <div style="font-size: 0.8rem; color: #666;">@${sub.student_username}</div>
                        </div>
                        <span class="badge" style="background: ${this._getStatusColor(sub.status)}20; color: ${this._getStatusColor(sub.status)};">
                            ${sub.status.toUpperCase()}
                        </span>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                        ${sub.content ? `<p style="white-space: pre-wrap;">${sub.content}</p>` : ''}
                        ${sub.image_url ? `
                            <div style="margin-top: 10px;">
                                <a href="/${sub.image_url}" target="_blank" style="color: #3498db; font-size: 0.9rem;">📎 To'liq hajmdagi rasm</a>
                                <img src="/${sub.image_url}" alt="Submission" style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 8px; border: 1px solid #ddd;">
                            </div>
                        ` : ''}
                    </div>

                    ${sub.status === 'submitted' ? `
                        <div style="display: flex; gap: 10px; align-items: flex-end;">
                            <div style="flex: 1;">
                                <label style="font-size: 0.8rem;">Coin:</label>
                                <input type="number" id="grade_amount_${sub.id}" class="form-control" value="5" min="0" step="0.5">
                            </div>
                            <div style="flex: 2;">
                                <label style="font-size: 0.8rem;">Izoh:</label>
                                <input type="text" id="grade_comment_${sub.id}" class="form-control" placeholder="Barakalla!">
                            </div>
                            <button class="btn btn-success" onclick="TeacherModule.submitGrade(${sub.id}, 'approve')">✅ Qabul</button>
                            <button class="btn btn-danger" onclick="TeacherModule.submitGrade(${sub.id}, 'reject')">❌ Rad</button>
                        </div>
                    ` : `
                        <div style="font-size: 0.9rem; color: #666;">
                            Teacher Comment: ${sub.admin_comment || 'No comment'}
                        </div>
                    `}
                </div>
            `).join('');

        } catch (e) {
            container.innerHTML = `<p class="text-danger">Error: ${e.message}</p>`;
        }
    },

    _getStatusColor(status) {
        switch (status) {
            case 'submitted': return '#f1c40f';
            case 'approved': return '#2ecc71';
            case 'rejected': return '#e74c3c';
            default: return '#95a5a6';
        }
    },

    async submitGrade(subId, action) {
        const amount = document.getElementById(`grade_amount_${subId}`)?.value || 0;
        const comment = document.getElementById(`grade_comment_${subId}`)?.value || '';

        if (action === 'approve' && amount <= 0) {
            return alert("Coin miqdori 0 dan katta bo'lishi kerak!");
        }

        try {
            const res = await api.post(`/teacher/homework/submission/${subId}/grade`, {
                action, amount, comment
            });
            alert(res.msg);
            // Reload the list to show updated status
            // We need the homework ID, but it's not passed here. 
            // Workaround: Find the card in DOM or refresh page.
            // Better: just remove the card or update it.
            // For simplicity, close modal or let user refresh manually, 
            // OR store current hwId in a module variable.

            // Simple refresh of the modal content if we knew the hwId, but we don't easily here.
            // Let's just reload the page or hide modal for now.
            document.getElementById('submissionsModal').style.display = 'none';
            this.initHomeworkPage(); // Full refresh
        } catch (e) {
            alert("Xatolik: " + e.message);
        }
    }
};

window.TeacherModule = TeacherModule;
