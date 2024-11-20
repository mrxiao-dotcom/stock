// 更新历史数据
function updateHistoricalData() {
    console.log('开始更新历史数据');
    
    // 显示停止按钮，隐藏开始按钮
    document.getElementById('start-update-btn').style.display = 'none';
    document.getElementById('stop-update-btn').style.display = 'inline-block';
    
    // 发起更新请求
    fetch('/api/update_historical_data', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('更新请求发送成功:', data);
        // 开始轮询进度
        startProgressPolling();
    })
    .catch(error => {
        console.error('更新请求失败:', error);
        showError('更新请求失败: ' + error.message);
    });
}

// 停止更新
function stopHistoricalData() {
    console.log('停止更新');
    
    fetch('/api/stop_update', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('停止请求发送成功:', data);
        // 显示开始按钮，隐藏停止按钮
        document.getElementById('start-update-btn').style.display = 'inline-block';
        document.getElementById('stop-update-btn').style.display = 'none';
    })
    .catch(error => {
        console.error('停止请求失败:', error);
        showError('停止请求失败: ' + error.message);
    });
}

// 轮询进度
let progressInterval;
function startProgressPolling() {
    // 清除可能存在的旧定时器
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    // 设置新的定时器
    progressInterval = setInterval(checkProgress, 1000);
}

// 检查进度
function checkProgress() {
    fetch('/api/update_progress')
        .then(response => response.json())
        .then(data => {
            updateProgressUI(data);
            
            // 如果更新完成或出错，停止轮询
            if (data.status === 'completed' || data.status === 'error' || !data.is_running) {
                clearInterval(progressInterval);
                // 显示开始按钮，隐藏停止按钮
                document.getElementById('start-update-btn').style.display = 'inline-block';
                document.getElementById('stop-update-btn').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('获取进度失败:', error);
            clearInterval(progressInterval);
        });
}

// 更新进度UI
function updateProgressUI(data) {
    // 更新状态文本
    const statusText = document.getElementById('update-status');
    if (statusText) {
        if (data.current_stock) {
            statusText.textContent = `正在更新: ${data.current_stock} (${data.current_index}/${data.total_stocks})`;
        } else {
            statusText.textContent = data.status === 'idle' ? '等待更新' : '更新完成';
        }
    }
    
    // 更新统计信息
    document.getElementById('success-count').textContent = `成功: ${data.updated_count || 0}`;
    document.getElementById('error-count').textContent = `失败: ${data.error_logs.length || 0}`;
    document.getElementById('remaining-count').textContent = 
        `剩余: ${Math.max(0, (data.total_stocks || 0) - (data.current_index || 0))}`;
    
    // 更新错误日志
    const errorLogs = document.getElementById('error-logs');
    if (errorLogs && data.error_logs && data.error_logs.length > 0) {
        errorLogs.innerHTML = data.error_logs.map(log => `<div>${log}</div>`).join('');
    }
}

// 显示错误信息
function showError(message) {
    const errorMessage = document.getElementById('error-message');
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
}