// 全局变量
let currentSectorId = null;
let currentSortOrder = 'asc';
let currentStockCode = null;

// 加载板块列表
function loadSectorList() {
    console.log('开始加载板块列表');
    fetch('/api/sectors')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateSectorList(data.sectors);
                // 自动加载第一个板块的数据
                if (data.sectors && data.sectors.length > 0) {
                    loadSectorStocks(data.sectors[0].sector_id);
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

// 加载板块股票
function loadSectorStocks(sectorId) {
    currentSectorId = sectorId;
    fetch(`/api/sector/${sectorId}/stocks`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('获取到板块数据:', data);  // 添加日志
                updateStockList(data);
                updateCharts(data);
                // 自动加载第一只股票的详情
                if (data.daily_changes && data.dates && data.dates.length > 0) {
                    const latestDate = data.dates[data.dates.length - 1];
                    const stocks = data.daily_changes[latestDate].stocks;
                    if (stocks && stocks.length > 0) {
                        loadStockDetail(stocks[0].code);
                    }
                }
            } else {
                console.error('获取板块数据失败:', data.message);
            }
        })
        .catch(error => {
            console.error('加载板块股票失败:', error);
            const stockList = document.getElementById('sector-stocks');
            if (stockList) {
                stockList.innerHTML = '<div class="alert alert-danger">加载股票列表失败</div>';
            }
        });
}

// 加载个股详情
function loadStockDetail(stockCode) {
    if (currentStockCode === stockCode) return;  // 避免重复加载
    currentStockCode = stockCode;
    
    console.log('加载个股详情:', stockCode);
    fetch(`/api/stock/${stockCode}/detail`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 更新K线图
                updateStockDailyChart(data.stock_data);
                
                // 更新资金流向图
                updateMoneyFlowChart({
                    dates: data.stock_data.dates,
                    super_large_inflow: data.stock_data.super_large_inflow || [],
                    super_large_outflow: data.stock_data.super_large_outflow || [],
                    large_inflow: data.stock_data.large_inflow || [],
                    large_outflow: data.stock_data.large_outflow || []
                });
                
                // 更新资金净流入图
                updateNetInflowChart({
                    dates: data.stock_data.dates,
                    net_inflow: data.stock_data.net_inflow || []
                });
                
                // 显示所属板块
                showStockSectors(data.sectors);
            } else {
                console.error('获取个股详情失败:', data.message);
            }
        })
        .catch(error => {
            console.error('加载个股详情失败:', error);
        });
}

// 显示股票所属板块
function showStockSectors(sectors) {
    const sectorsContainer = document.getElementById('stock-sectors');
    if (!sectorsContainer) return;

    if (sectors && sectors.length > 0) {
        sectorsContainer.innerHTML = sectors.map(sector => 
            `<span class="badge bg-info me-1">${sector.sector_name}</span>`
        ).join('');
    } else {
        sectorsContainer.innerHTML = '<small class="text-muted">暂无板块信息</small>';
    }
}

// 更新股票列表
function updateStockList(data) {
    const stockList = document.getElementById('sector-stocks');
    if (!stockList) return;

    console.log('更新股票列表数据:', data);

    if (!data || !data.daily_changes || !data.dates || data.dates.length === 0) {
        console.error('无效的数据格式:', data);
        stockList.innerHTML = '<div class="alert alert-warning">暂无股票数据</div>';
        return;
    }

    const latestDate = data.dates[data.dates.length - 1];
    const firstDate = data.dates[0];
    const dailyData = data.daily_changes[latestDate];
    const firstDayData = data.daily_changes[firstDate];

    if (!dailyData || !dailyData.stocks || !firstDayData || !firstDayData.stocks) {
        console.error('无效的每日数据:', dailyData);
        stockList.innerHTML = '<div class="alert alert-warning">暂无股票数据</div>';
        return;
    }

    // 计算相对于首日的涨跌幅
    const stocksWithChanges = dailyData.stocks.map(stock => {
        const firstDayStock = firstDayData.stocks.find(s => s.code === stock.code);
        if (firstDayStock && firstDayStock.close && stock.close) {
            const basePrice = parseFloat(firstDayStock.close);
            const currentPrice = parseFloat(stock.close);
            const change = ((currentPrice - basePrice) / basePrice * 100);
            return {
                ...stock,
                change: parseFloat(change.toFixed(2))
            };
        }
        return stock;
    });

    // 按累计涨幅排序
    stocksWithChanges.sort((a, b) => b.change - a.change);

    stockList.innerHTML = stocksWithChanges.map(stock => `
        <div class="list-group-item" onclick="loadStockDetail('${stock.code}')">
            <div class="d-flex justify-content-between align-items-center">
                <div class="stock-info">
                    ${stock.name} (${stock.code})
                </div>
                <div>
                    <span class="badge ${stock.change >= 0 ? 'bg-danger' : 'bg-success'}">
                        ${stock.change.toFixed(2)}%
                    </span>
                    <small class="text-muted ms-2">${stock.amount_str}</small>
                </div>
            </div>
        </div>
    `).join('');
}

// 更新板块列表
function updateSectorList(sectors) {
    const sectorList = document.getElementById('sector-list');
    if (!sectorList) {
        console.error('未找到sector-list元素');
        return;
    }

    if (!sectors || sectors.length === 0) {
        sectorList.innerHTML = '<div class="text-muted p-3">暂无板块数据</div>';
        return;
    }

    sectorList.innerHTML = sectors.map(sector => {
        // 移除 sector_type 中的 'CONCEPT' 和 'CUSTOM'
        const sectorType = sector.sector_type ? 
            sector.sector_type.replace('CONCEPT', '').replace('CUSTOM', '').trim() : '';

        return `
            <div class="list-group-item" onclick="loadSectorStocks(${sector.sector_id})">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="stock-info">
                        <span class="sector-name">${sector.sector_name || '未命名板块'}</span>
                        ${sectorType ? `<small class="text-muted ms-2">${sectorType}</small>` : ''}
                    </div>
                    <div class="d-flex align-items-center">
                        <span class="badge bg-primary">${sector.stock_count || 0}只</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// 搜索板块
function filterSectorList(searchText) {
    if (!searchText) {
        // 如果搜索文本为空，重新加载板块列表
        loadSectorList();
        return;
    }

    const items = document.querySelectorAll('#sector-list .list-group-item');
    const searchLower = searchText.toLowerCase();
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchLower)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化图表
    initializeCharts();
    
    // 加载初始数据
    loadSectorList();
    
    // 绑定搜索事件
    const sectorSearch = document.getElementById('sector-search');
    if (sectorSearch) {
        sectorSearch.addEventListener('input', function(e) {
            filterSectorList(e.target.value);
        });
    }
});

// 初始化所有图表
function initializeCharts() {
    if (document.getElementById('timeline-chart')) {
        timelineChart = echarts.init(document.getElementById('timeline-chart'));
    }
    if (document.getElementById('volume-chart')) {
        volumeChart = echarts.init(document.getElementById('volume-chart'));
    }
    if (document.getElementById('stock-detail-chart')) {
        stockDetailChart = echarts.init(document.getElementById('stock-detail-chart'));
    }
}

// 更新图表
function updateCharts(data) {
    console.log('更新图表数据:', data);

    if (!data || !data.daily_changes || !data.dates) {
        console.error('无效的图表数据格式:', data);
        return;
    }

    try {
        // 直接传递原始数据给时间轴图表
        updateTimelineChart(data);

        // 准备成交额数据
        const dates = data.dates;
        const volumes = dates.map(date => {
            const dayData = data.daily_changes[date];
            return dayData ? dayData.total_amount : 0;
        });

        // 更新成交额图表
        updateVolumeChart({
            dates: dates,
            volumes: volumes
        });

    } catch (error) {
        console.error('更新图表时出错:', error);
    }
} 