// 全局变量
let updateStatus = {
    isUpdating: false,
    lastUpdateTime: null
};

// 检查更新状态
function checkUpdateStatus() {
    fetch('/api/update/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatus.isUpdating = data.is_updating;
                updateStatus.lastUpdateTime = data.last_update_time;
                updateStatusUI();
            }
        })
        .catch(error => console.error('检查更新状态失败:', error));
}

// 更新状态UI
function updateStatusUI() {
    const statusElement = document.getElementById('update-status');
    if (!statusElement) return;

    if (updateStatus.isUpdating) {
        statusElement.innerHTML = `
            <span class="badge bg-warning">
                <i class="fas fa-sync fa-spin"></i> 更新中...
            </span>
        `;
    } else {
        const lastUpdate = updateStatus.lastUpdateTime ? 
            new Date(updateStatus.lastUpdateTime).toLocaleString() : '未知';
        statusElement.innerHTML = `
            <span class="badge bg-success">
                <i class="fas fa-check"></i> 最后更新: ${lastUpdate}
            </span>
        `;
    }
}

// 启动数据更新
function startUpdate() {
    if (updateStatus.isUpdating) {
        alert('数据正在更新中，请稍后再试');
        return;
    }

    if (!confirm('确定要更新数据吗？')) return;

    fetch('/api/update/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatus.isUpdating = true;
                updateStatusUI();
                // 开始轮询更新状态
                pollUpdateStatus();
            } else {
                alert('启动更新失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('启动更新失败:', error);
            alert('启动更新失败，请查看控制台');
        });
}

// 轮询更新状态
function pollUpdateStatus() {
    if (!updateStatus.isUpdating) return;

    checkUpdateStatus();
    setTimeout(pollUpdateStatus, 5000);  // 每5秒检查一次
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    checkUpdateStatus();
});