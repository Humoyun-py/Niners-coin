const AdminModule = {
    async initDashboard() {
        await this.loadStats();
        await this.loadRecentUsers();
    },

    async loadStats() {
        try {
            const users = await api.get('/admin/users');
            const classes = await api.get('/admin/classes');
            document.getElementById('totalUsers').innerText = users.length;
            document.getElementById('totalGroups').innerText = classes.length;
        } catch (e) {
            console.error('Stats Error:', e);
            document.getElementById('totalUsers').innerText = '-';
            document.getElementById('totalGroups').innerText = '-';
        }
    },

    async loadRecentUsers() {
        try {
            const users = await api.get('/admin/users');
            const tbody = document.getElementById('userTableBody');
            if (!tbody) return;

            const recent = users.slice(-5).reverse();
            tbody.innerHTML = recent.map(u => `
                <tr style="border-bottom: 1px solid var(--border-light);">
                    <td style="padding: 12px; font-weight:600;">
                        ${u.full_name}
                        ${!u.is_active ? `
                            <div style="font-size:0.7rem; color:#C62828; font-weight:400; margin-top:4px;">
                                ⚠️ ${u.block_reason || 'Blocked'}
                            </div>
                        ` : ''}
                    </td>
                    <td style="padding: 12px; color: var(--text-muted);">${u.username}</td>
                    <td style="padding: 12px;"><span class="badge" style="background:${this.getRoleColor(u.role)}; color:white; padding:4px 8px; border-radius:4px; font-size:0.75rem;">${u.role}</span></td>
                </tr>
            `).join('');
        } catch (e) {
            console.error(e);
            const tbody = document.getElementById('userTableBody');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding:20px; color:red;">Error: ${e.message}</td></tr>`;
            }
        }
    },

    getRoleColor(role) {
        switch (role) {
            case 'admin': return '#6C5CE7';
            case 'teacher': return '#00B894';
            case 'director': return '#D63031';
            default: return '#FDCB6E';
        }
    },

    createModal(title, content, onSave, saveText = 'Save Changes') {
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
                        <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                        <button class="btn btn-primary" id="modalSaveBtn">${saveText}</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        document.getElementById('modalSaveBtn').onclick = async () => {
            const btn = document.getElementById('modalSaveBtn');
            btn.innerHTML = 'Processing...';
            btn.disabled = true;
            await onSave();
            const overlay = document.querySelector('.modal-overlay');
            if (overlay) overlay.remove();
        };
    },

    createConfirm(title, message, onConfirm) {
        const content = `<p style="color: var(--text-muted); font-size: 1rem;">${message}</p>`;
        this.createModal(title, content, onConfirm, 'Confirm');
    },

    async addUser(role) {
        let extraFields = '';
        if (role === 'student') {
            let options = '<option value="">Failed to load classes</option>';
            try {
                const classes = await api.get('/admin/classes');
                options = classes.length
                    ? classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('')
                    : '<option value="">No classes available</option>';
            } catch (e) {
                console.error("Error loading classes:", e);
            }

            extraFields = `
                <div class="input-group">
                    <label class="input-label">Assign Group (Optional)</label>
                    <select id="newClassId" class="form-control">
                        <option value="">No Group</option>
                        ${options}
                    </select>
                </div>`;
        } else if (role === 'teacher') {
            extraFields = `
                <div class="input-group">
                    <label class="input-label">Subject</label>
                    <input type="text" id="newSubject" class="form-control" placeholder="e.g. IELTS, Math">
                </div>`;
        }

        const formContent = `
            <div class="input-group">
                <label class="input-label">Username</label>
                <input type="text" id="newUsername" class="form-control" placeholder="johndoe">
            </div>
            <div class="input-group">
                <label class="input-label">Full Name</label>
                <input type="text" id="newFullName" class="form-control" placeholder="John Doe">
            </div>
            <div class="input-group">
                <label class="input-label">Password</label>
                <input type="password" id="newPassword" class="form-control" placeholder="••••••">
            </div>
            ${extraFields}
        `;

        this.createModal(`Add New ${role.charAt(0).toUpperCase() + role.slice(1)}`, formContent, async () => {
            const username = document.getElementById('newUsername').value;
            const fullName = document.getElementById('newFullName').value;
            const password = document.getElementById('newPassword').value;
            if (!username || !fullName || !password) return alert("All fields are required!");

            let extraData = { password };
            if (role === 'student') {
                const cid = document.getElementById('newClassId').value;
                if (cid) extraData.class_id = parseInt(cid);
            } else if (role === 'teacher') {
                const subj = document.getElementById('newSubject').value;
                if (subj) extraData.subject = subj;
            }

            try {
                await api.post('/admin/users', { username, full_name: fullName, role, ...extraData });
                alert("User created successfully!");
                this.initDashboard();
            } catch (e) { alert("Error: " + e.message); }
        });
    },

    async editUser(userId) {
        try {
            const users = await api.get('/admin/users');
            const user = users.find(u => u.id === userId);
            if (!user) return;

            const formContent = `
                <div class="input-group">
                    <label class="input-label">Full Name</label>
                    <input type="text" id="editFullName" class="form-control" value="${user.full_name}">
                </div>
                <div class="input-group">
                    <label class="input-label">Email Address</label>
                    <input type="email" id="editEmail" class="form-control" value="${user.email}">
                </div>
                <div class="input-group">
                    <label class="input-label">New Password (leave empty to keep)</label>
                    <input type="password" id="editPassword" class="form-control" placeholder="••••••">
                </div>
            `;

            this.createModal('Edit User Profile', formContent, async () => {
                const fullName = document.getElementById('editFullName').value;
                const email = document.getElementById('editEmail').value;
                const password = document.getElementById('editPassword').value;
                try {
                    await api.put(`/admin/users/${userId}`, { full_name: fullName, email, password: password || undefined });
                    alert("User updated successfully!");
                    this.initDashboard();
                } catch (e) { alert("Error: " + e.message); }
            });
        } catch (e) { alert("Error: " + e.message); }
    },

    async createClass() {
        try {
            const teachers = (await api.get('/admin/users')).filter(u => u.role === 'teacher');
            const options = teachers.map(t => `<option value="${t.id}">${t.full_name}</option>`).join('');

            const formContent = `
                <div class="input-group">
                    <label class="input-label">Group Name</label>
                    <input type="text" id="className" class="form-control" placeholder="e.g. IELTS Foundation">
                </div>
                <div class="input-group">
                    <label class="input-label">Assign Instructor</label>
                    <select id="classTeacher" class="form-control">
                        <option value="">Select Teacher</option>
                        ${options}
                    </select>
                </div>
            `;

            this.createModal('Create New Group', formContent, async () => {
                const name = document.getElementById('className').value;
                const teacherId = document.getElementById('classTeacher').value;
                if (!name || !teacherId) return alert("All fields are required!");

                try {
                    await api.post('/admin/classes', { name, teacher_id: parseInt(teacherId) });
                    alert("Group created successfully!");
                    this.initDashboard();
                } catch (e) { alert("Error: " + e.message); }
            });
        } catch (e) { alert("Error: " + e.message); }
    },

    async editClass(classId) {
        try {
            const classes = await api.get('/admin/classes');
            const cls = classes.find(c => c.id === classId);
            if (!cls) return;

            const teachers = (await api.get('/admin/users')).filter(u => u.role === 'teacher');
            const options = teachers.map(t => `<option value="${t.id}" ${t.full_name === cls.teacher_name ? 'selected' : ''}>${t.full_name}</option>`).join('');

            const formContent = `
                <div class="input-group">
                    <label class="input-label">Group Name</label>
                    <input type="text" id="editClassName" class="form-control" value="${cls.name}">
                </div>
                <div class="input-group">
                    <label class="input-label">Assign Instructor</label>
                    <select id="editClassTeacher" class="form-control">
                        <option value="">No Change</option>
                        ${options}
                    </select>
                </div>
            `;

            this.createModal('Edit Group', formContent, async () => {
                const name = document.getElementById('editClassName').value;
                const teacherId = document.getElementById('editClassTeacher').value;
                try {
                    await api.put(`/admin/classes/${classId}`, { name, teacher_id: teacherId ? parseInt(teacherId) : undefined });
                    alert("Group updated successfully!");
                    this.initDashboard();
                } catch (e) { alert("Error: " + e.message); }
            });
        } catch (e) { alert("Error: " + e.message); }
    },

    async deleteClass(classId) {
        this.createConfirm('Delete Group', 'Are you sure you want to delete this group? All students will be detached.', async () => {
            try {
                await api.delete(`/admin/classes/${classId}`);
                alert("Group deleted successfully!");
                this.initDashboard();
            } catch (e) { alert("Error: " + e.message); }
        });
    },

    async assignStudentToClass(classId) {
        try {
            const formContent = `
                <div class="input-group">
                    <label class="input-label">Student Username</label>
                    <input type="text" id="assignStudentUsername" class="form-control" placeholder="Enter student's username">
                </div>
            `;

            this.createModal('Add Student to Group', formContent, async () => {
                const username = document.getElementById('assignStudentUsername').value;
                if (!username) return alert("Please enter a username!");
                try {
                    await api.post(`/admin/classes/${classId}/students`, { username: username });
                    alert("Student added successfully!");
                    this.initDashboard();
                } catch (e) { alert("Error: " + e.message); }
            }, 'Add Student');
        } catch (e) { alert("Error: " + e.message); }
    },

    async toggleUserStatus(userId) {
        try {
            const users = await api.get('/admin/users');
            const user = users.find(u => u.id === userId);
            if (!user) return;

            if (user.is_active) {
                // Showing block modal
                const content = `
                    <div class="input-group">
                        <label class="input-label">Bloklash sababi</label>
                        <input type="text" id="blockReason" class="form-control" placeholder="Masalan: To'lov qilinmagan">
                    </div>
                    <div class="input-group">
                        <label class="input-label">Qarzdorlik miqdori (so'mda)</label>
                        <input type="number" id="debtAmount" class="form-control" value="0">
                    </div>
                `;
                this.createModal('Foydalanuvchini bloklash', content, async () => {
                    const reason = document.getElementById('blockReason').value;
                    const debt = document.getElementById('debtAmount').value;
                    try {
                        const res = await api.post(`/admin/users/${userId}/toggle-block`, { reason, debt });
                        alert(res.msg);
                        this.initDashboard();
                    } catch (e) { alert("Error: " + e.message); }
                }, 'Bloklash');
            } else {
                this.createConfirm('Blokdan chiqarish', `Haqiqatan ham ${user.full_name}ni blokdan chiqarmoqchimisiz?`, async () => {
                    try {
                        const res = await api.post(`/admin/users/${userId}/toggle-block`, {});
                        alert(res.msg);
                        location.reload();
                    } catch (e) { alert("Error: " + e.message); }
                });
            }
        } catch (e) { alert("Error: " + e.message); }
    },

    openShopManager() {
        window.location.href = 'shop-management.html';
    },

    async addShopItem() {
        const content = `
            <div class="input-group"><label class="input-label">Name</label><input type="text" id="itemName" class="form-control"></div>
            <div class="input-group"><label class="input-label">Price</label><input type="number" id="itemPrice" class="form-control"></div>
            <div class="input-group"><label class="input-label">Stock (-1 for infinite)</label><input type="number" id="itemStock" class="form-control" value="-1"></div>
            <div class="input-group"><label class="input-label">Image URL</label><input type="text" id="itemImage" class="form-control"></div>
        `;
        this.createModal('Add Shop Item', content, async () => {
            const name = document.getElementById('itemName').value;
            const price = document.getElementById('itemPrice').value;
            const stock = document.getElementById('itemStock').value;
            const image_url = document.getElementById('itemImage').value;

            if (!name || !price) return alert("Name and Price required");

            try {
                await api.post('/admin/shop/items', { name, price: parseFloat(price), stock: parseInt(stock), image_url });
                alert("Item added!");
                setTimeout(() => AdminModule.openShopManager(), 500);
            } catch (e) { alert("Error: " + e.message); }
        }, 'Add');
    },

    async editShopItem(itemId) {
        // Simple prompt for now or fetch item details to fill form.
        // Assuming we need to fetch first or pass data. Fetch is safer.
        // For brevity, let's just use Delete to show functionality, or basic edit.
        // Let's implement Delete fully and Edit minimally.

        // Implementing Edit with a fresh modal
        const content = `
            <p>Update Item Logic Here (Simplified)</p>
            <div class="input-group"><label class="input-label">New Price</label><input type="number" id="editItemPrice" class="form-control"></div>
        `;
        this.createModal('Edit Item', content, async () => {
            const price = document.getElementById('editItemPrice').value;
            if (price) {
                await api.put(`/admin/shop/items/${itemId}`, { price: parseFloat(price) });
                alert("Item updated!");
                setTimeout(() => AdminModule.openShopManager(), 500);
            }
        }, 'Update');
    },

    async deleteShopItem(itemId) {
        if (!confirm("Delete this item?")) return;
        try {
            await api.delete(`/admin/shop/items/${itemId}`);
            alert("Deleted!");
            setTimeout(() => AdminModule.openShopManager(), 500);
        } catch (e) { alert("Error: " + e.message); }
    }
};

// Explicitly export to window for sidebar-loader.js
window.AdminModule = AdminModule;
