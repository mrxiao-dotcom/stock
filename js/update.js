// 防抖函数定义
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 板块寻龙模块的全局变量（使用 var 避免重复声明错误）
var dragonStockData = [];
var dragonSortField = 'market_value';
var dragonSortOrder = 'desc';
var dragonFilters = {
    market_value: null,
    revenue: null,
    net_profit: null,
    gross_margin: null,
    debt_ratio: null
};

// 初始化 Bootstrap Tab
function initializeTabs() {
    // 获取所有 tab 元素
    const tabElements = document.querySelectorAll('[data-bs-toggle="pill"]');
    
    // 为每个 tab 添加点击事件监听
    tabElements.forEach(tabEl => {
        // 将文字转为竖排
        const text = tabEl.textContent.trim();
        tabEl.innerHTML = text.split('').join('<br>');
        tabEl.style.writingMode = 'vertical-lr';
        tabEl.style.textOrientation = 'upright';
        tabEl.style.padding = '15px 3px';  // 调整内边距
        tabEl.style.fontSize = '14px';      // 增大字体
        tabEl.style.lineHeight = '1.2';     // 调整行高
        tabEl.style.width = '24px';         // 调整宽度
        tabEl.style.whiteSpace = 'nowrap';
        tabEl.style.letterSpacing = '2px';  // 增加字间距
        tabEl.style.marginBottom = '2px';   // 减小标签间距
        
        tabEl.addEventListener('click', event => {
            event.preventDefault();
            
            // 获取目标面板的 ID
            const targetId = tabEl.getAttribute('data-bs-target');
            console.log('点击 tab:', targetId);
            
            // 移除所有 tab 的激活状态
            tabElements.forEach(el => {
                el.classList.remove('active');
                const paneId = el.getAttribute('data-bs-target');
                document.querySelector(paneId)?.classList.remove('show', 'active');
            });
            
            // 激活当前 tab
            tabEl.classList.add('active');
            const targetPane = document.querySelector(targetId);
            if (targetPane) {
                targetPane.classList.add('show', 'active');
                
                // 根据不同的 tab 执行相应的初始化
                const tabId = targetId.substring(1);
                console.log('Tab切换到:', tabId);
                
                if (tabId === 'maintain') {
                    refreshSectorTable();
                } else if (tabId === 'browse') {
                    loadSectorList();
                } else if (tabId === 'dragon') {
                    loadDragonSectorList();
                }
            }
        });
    });
    
    // 设置父容器样式
    const tabContainer = document.querySelector('.nav-pills');
    if (tabContainer) {
        tabContainer.style.width = '24px';      // 调整容器宽度
        tabContainer.style.marginRight = '2px';  // 减小右边距
        tabContainer.style.marginLeft = '2px';   // 减小左边距
    }
}

// 在页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始初始化...');
    
    // 初始化 Bootstrap Tab
    initializeTabs();
    
    // 加载初始数据
    const activeTab = document.querySelector('[data-bs-toggle="pill"].active');
    if (activeTab) {
        const targetId = activeTab.getAttribute('data-bs-target').substring(1);
        console.log('初始化激活的 tab:', targetId);
        
        if (targetId === 'maintain') {
            refreshSectorTable();
        } else if (targetId === 'browse') {
            loadSectorList();
        } else if (targetId === 'dragon') {
            loadDragonSectorList();
        }
    }
    
    // 初始化其他功能
    initializeDragonSortAndFilter();
    initializeSearch();
    
    // 绑定更新按钮点击事件
    const startBtn = document.getElementById('start-update-btn');
    if (startBtn) {
        console.log('找到开始更新按钮，绑定点击事件');
        startBtn.addEventListener('click', updateHistoricalData);
    }
    
    // 绑定停止按钮点击事件
    const stopBtn = document.getElementById('stop-update-btn');
    if (stopBtn) {
        console.log('找到停止更新按钮，绑定点击事件');
        stopBtn.addEventListener('click', stopHistoricalData);
    }
    
    console.log('初始化完成');
});

// 加载板块列表
async function loadSectorList() {
    try {
        console.log('开始加载板块列表');
        const response = await fetch('/api/get_sectors');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || '获取板块列表失败');
        }
        
        const sectorList = document.getElementById('sector-list');
        if (!sectorList) {
            console.error('未找到板块列表容器');
            return;
        }
        
        // 生成板块列表HTML
        const html = data.sectors.map(sector => `
            <button class="list-group-item list-group-item-action d-flex justify-content-between align-items-center py-1"
                    onclick="loadSectorStocks(${sector.id})">
                <span class="sector-name">${sector.name}</span>
                <span class="badge bg-secondary">${sector.stock_count}</span>
            </button>
        `).join('');
        
        sectorList.innerHTML = html;
        console.log('板块列表加载完成');
        
    } catch (error) {
        console.error('加载板块列表失败:', error);
        const sectorList = document.getElementById('sector-list');
        if (sectorList) {
            sectorList.innerHTML = `
                <div class="alert alert-danger">
                    加载失败: ${error.message}
                </div>
            `;
        }
    }
}

// 刷新板块列表
async function refreshSectorList() {
    try {
        console.log('开始刷新板块列表');
        const response = await fetch('/api/get_sector_info', {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('获取到板块数据:', data);
        
        if (!data.success) {
            throw new Error(data.message || '获板块信息失败');
        }
        
        // 更新板块列表
        const sectorList = document.getElementById('sector-list');
        if (!sectorList) {
            console.error('未找到板块列表容器');
            return;
        }
        
        // 按类型分组
        const sectorsByType = {};
        data.sectors.forEach(sector => {
            if (!sectorsByType[sector.type]) {
                sectorsByType[sector.type] = [];
            }
            sectorsByType[sector.type].push(sector);
        });
        
        // 生成HTML
        let html = '';
        for (const [type, sectors] of Object.entries(sectorsByType)) {
            html += `
                <div class="sector-group mb-3">
                    <h6 class="text-muted mb-2">${type}</h6>
                    <div class="list-group">
                        ${sectors.map(sector => `
                            <div class="list-group-item d-flex justify-content-between align-items-center" 
                                 onclick="loadSectorStocks(${sector.id})">
                                <span class="sector-name">${sector.name}</span>
                                <span class="badge bg-secondary">${sector.stock_count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        sectorList.innerHTML = html;
        console.log('板块列表刷新完成');
        
    } catch (error) {
        console.error('刷新板块列表失败:', error);
        const sectorList = document.getElementById('sector-list');
        if (sectorList) {
            sectorList.innerHTML = `
                <div class="alert alert-danger">
                    加载失败: ${error.message}
                </div>
            `;
        }
    }
}

// 添加排序切换函数
function toggleStockSort() {
    console.log('切换排序顺序');
    const stockList = document.getElementById('sector-stocks');
    if (!stockList) {
        console.error('未找到股票列表容器');
        return;
    }
    
    // 切换排序顺序
    appState.stockSortOrder = appState.stockSortOrder === 'desc' ? 'asc' : 'desc';
    
    // 更新排序按钮图标
    const sortBtn = document.getElementById('sort-stocks-btn');
    if (sortBtn) {
        sortBtn.innerHTML = `<i class="fas fa-sort-${appState.stockSortOrder === 'desc' ? 'down' : 'up'}"></i>`;
    }
    
    // 获取所有股票元素并转换为数
    const stocks = Array.from(stockList.children);
    
    // 对股票列表进行排序
    stocks.sort((a, b) => {
        const changeA = parseFloat(a.querySelector('.badge')?.textContent || '0');
        const changeB = parseFloat(b.querySelector('.badge')?.textContent || '0');
        return appState.stockSortOrder === 'desc' ? changeB - changeA : changeA - changeB;
    });
    
    // 重新插入排序后的元素
    stocks.forEach(stock => stockList.appendChild(stock));
}

// 数据浏览模块 - 板块搜索
function searchBrowseSectors() {
    console.log('执行数据浏览模块板块搜索');
    const searchInput = document.getElementById('sector-search');
    if (!searchInput) {
        console.error('未找到数据浏览搜索输入框');
        return;
    }
    
    const searchText = searchInput.value.toLowerCase().trim();
    console.log('数据浏览搜索文本:', searchText);
    
    // 获取板块列表容器
    const sectorList = document.getElementById('sector-list');
    if (!sectorList) {
        console.error('找到板块列表容器');
        return;
    }
    
    // 获取所有板块项
    const sectorItems = sectorList.querySelectorAll('.list-group-item');
    console.log(`找到 ${sectorItems.length} 个板块项`);
    
    let totalVisible = 0;
    const visibleGroups = new Set();
    
    // 遍历所板块项进行筛选
    sectorItems.forEach(item => {
        const sectorName = item.querySelector('.sector-name')?.textContent.toLowerCase();
        if (!sectorName) return;
        
        const group = item.closest('.sector-group');
        if (!group) return;
        
        // 判断是否匹配搜索文本
        const isMatch = !searchText || sectorName.includes(searchText);
        
        // 设置显示状态
        if (isMatch) {
            item.classList.remove('d-none');
            totalVisible++;
            visibleGroups.add(group);
        } else {
            item.classList.add('d-none');
        }
        
        console.log(`板块: ${sectorName}, 匹配: ${isMatch}`);
    });
    
    // 处理板块组的显示/隐藏
    const sectorGroups = sectorList.querySelectorAll('.sector-group');
    sectorGroups.forEach(group => {
        const hasVisibleItems = Array.from(group.querySelectorAll('.list-group-item'))
            .some(item => !item.classList.contains('d-none'));
        
        if (hasVisibleItems) {
            group.classList.remove('d-none');
        } else {
            group.classList.add('d-none');
        }
    });
    
    console.log(`搜索完成，显示 ${totalVisible} 个匹配项`);
}

// 据维护模块 - 板块表格搜索
function searchMaintainSectors() {
    console.log('执行数据维护模块板块搜索');
    const searchInput = document.getElementById('sector-table-search');
    const searchText = searchInput?.value.toLowerCase().trim();
    
    console.log('数据维护搜索文本:', searchText);
    
    const tableBody = document.getElementById('sector-table-body');
    if (!tableBody) {
        console.error('未找到板块表格');
        return;
    }
    
    const rows = tableBody.getElementsByTagName('tr');
    let visibleCount = 0;
    
    Array.from(rows).forEach(row => {
        const nameCell = row.cells[0];  // 板块名称列
        const typeCell = row.cells[1];  // 板块类型列
        
        if (nameCell && typeCell) {
            const name = nameCell.textContent.toLowerCase();
            const type = typeCell.textContent.toLowerCase();
            
            if (!searchText || 
                name.includes(searchText) || 
                type.includes(searchText)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        }
    });
    
    console.log(`数据维护搜索完成，显示 ${visibleCount} 条记录`);
}

// 刷新板块信息表
async function refreshSectorTable() {
    try {
        console.log('开始刷新板块信息表');
        const response = await fetch('/api/get_sector_info');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || '获取板块信息失败');
        }
        
        const tableBody = document.getElementById('sector-table-body');
        if (!tableBody) {
            console.error('未找到板块表格容器');
            return;
        }
        
        // 生成表格HTML
        const html = data.sectors.map(sector => `
            <tr data-sector-id="${sector.id}" onclick="showSectorStocks(${sector.id})">
                <td class="py-1">${sector.name}</td>
                <td class="py-1">${sector.type}</td>
                <td class="py-1">${sector.stock_count}</td>
                <td class="py-1 text-end">
                    <button class="btn btn-sm btn-outline-warning me-1" 
                            onclick="event.stopPropagation(); renameSector(${sector.id}, '${sector.name}')">
                        重命名
                    </button>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="event.stopPropagation(); deleteSector(${sector.id}, '${sector.name}')">
                        删除
                    </button>
                </td>
            </tr>
        `).join('');
        
        tableBody.innerHTML = html;
        console.log('板块信息表刷新完成');
        
    } catch (error) {
        console.error('刷新板块信息表失败:', error);
        const tableBody = document.getElementById('sector-table-body');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-danger">
                        加载失败: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
}

// 加载板块内的股票列表
async function loadSectorStocks(sectorId) {
    try {
        console.log('开始加载板块股票列表, sectorId:', sectorId);
        const response = await fetch(`/api/get_sector_stocks_with_change/${sectorId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('获取到板块股票数据:', data);
        
        if (!data.success) {
            throw new Error(data.message || '获取板块股票列表失败');
        }

        // 更新股票列表
        const stockList = document.getElementById('sector-stocks');
        if (!stockList) {
            console.error('未找到股票列表容器');
            return;
        }

        // 使用最新日期的数据
        const latestDate = data.dates[data.dates.length - 1];
        const dailyData = data.daily_changes[latestDate];
        
        if (dailyData && dailyData.stocks && dailyData.stocks.length > 0) {
            // 生成股票列表HTML
            stockList.innerHTML = dailyData.stocks.map(stock => `
                <div class="list-group-item d-flex justify-content-between align-items-center" 
                     onclick="showStockDetail('${stock.code}')">
                    <div class="stock-info">
                        ${stock.name} (${stock.code})
                    </div>
                    <span class="badge ${stock.change >= 0 ? 'bg-danger' : 'bg-success'}">
                        ${stock.change ? stock.change.toFixed(2) + '%' : '-'}
                    </span>
                </div>
            `).join('');

            // 更新图表
            updateTimelineChart({
                dates: data.dates,
                daily_changes: data.daily_changes
            });
            
            updateVolumeChart({
                dates: data.dates,
                daily_changes: data.daily_changes
            });
        } else {
            stockList.innerHTML = '<div class="alert alert-info">暂无数据</div>';
        }
        
        console.log('板块股列表加载完成');
        
    } catch (error) {
        console.error('加载板块股票列表失败:', error);
        const stockList = document.getElementById('sector-stocks');
        if (stockList) {
            stockList.innerHTML = `
                <div class="alert alert-danger">
                    加载失败: ${error.message}
                </div>
            `;
        }
    }
}

// 初始化搜索功能
function initializeSearch() {
    // 数据浏览模块搜索框
    const browseSearchInput = document.getElementById('sector-search');
    if (browseSearchInput) {
        console.log('找到数据浏览搜索框，绑定事件');
        
        // 清除现有的事件监听器
        const newBrowseSearchInput = browseSearchInput.cloneNode(true);
        browseSearchInput.parentNode.replaceChild(newBrowseSearchInput, browseSearchInput);
        
        // 用 input 事件实时搜索
        let browseSearchTimeout;
        newBrowseSearchInput.addEventListener('input', function() {
            console.log('数据浏览搜索输入变化:', this.value);
            clearTimeout(browseSearchTimeout);
            browseSearchTimeout = setTimeout(() => {
                searchBrowseSectors();
            }, 200);  // 200ms 延迟
        });
        
        // 添加清除按钮事件
        newBrowseSearchInput.addEventListener('keyup', function(event) {
            if (event.key === 'Escape') {
                this.value = '';
                searchBrowseSectors();
            }
        });
    }
    
    // 数据维护模块搜索框
    const maintainSearchInput = document.getElementById('sector-table-search');
    if (maintainSearchInput) {
        console.log('找到数据维护搜索框，定事件');
        
        // 使用 input 事件实时搜索
        let maintainSearchTimeout;
        maintainSearchInput.addEventListener('input', function() {
            console.log('数据维护搜索输入变化:', this.value);
            clearTimeout(maintainSearchTimeout);
            maintainSearchTimeout = setTimeout(() => {
                searchMaintainSectors();
            }, 200);  // 200ms 延迟
        });
    }
}

// 更新Timeline图表
function updateTimelineChart(data) {
    if (typeof echarts === 'undefined') {
        console.error('ECharts 未加载');
        return;
    }

    const chartContainer = document.getElementById('timeline-chart');
    if (!chartContainer) {
        console.error('未找到图表容器');
        return;
    }

    console.log('开始更新Timeline图表，数据:', data);
    const chart = echarts.init(chartContainer);
    
    // 处理数据
    const dates = data.dates;
    const timelineData = [];
    
    // 为每个日期生成数据
    dates.forEach(date => {
        const dailyData = data.daily_changes[date];
        if (!dailyData || !dailyData.stocks) {
            console.warn(`日期 ${date} 没有数据`);
            return;
        }
        
        console.log(`处理 ${date} ���数据`);
        
        // 按涨幅排序
        const sortedStocks = [...dailyData.stocks].sort((a, b) => a.change - b.change);
        
        // 生成当天的数据
        timelineData.push({
            title: {
                text: `${date} 个股涨跌分布`,
                left: 'center',
                top: 10
            },
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const stock = sortedStocks[params[0].dataIndex];
                    return `${stock.name} (${stock.code})<br/>涨幅: ${stock.change.toFixed(2)}%`;
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: sortedStocks.map(stock => stock.name),
                axisLabel: {
                    interval: 0,
                    rotate: 45,
                    fontSize: 10
                }
            },
            yAxis: {
                type: 'value',
                name: '涨跌幅(%)',
                axisLabel: {
                    formatter: '{value}%'
                }
            },
            series: [{
                name: '涨跌分布',
                type: 'bar',
                data: sortedStocks.map(stock => ({
                    value: stock.change,
                    itemStyle: {
                        color: stock.change >= 0 ? '#c23531' : '#2f4554'
                    }
                })),
                label: {
                    show: true,
                    position: 'top',
                    formatter: '{c}%',
                    fontSize: 10
                }
            }]
        });
    });

    const option = {
        baseOption: {
            timeline: {
                axisType: 'category',
                autoPlay: false,
                playInterval: 2000,
                data: dates,
                left: '10%',
                right: '10%',
                bottom: '2%',
                height: 40,
                label: {
                    formatter: function(s) {
                        return s.slice(5);  // 只显示月-日
                    }
                }
            }
        },
        options: timelineData
    };

    chart.setOption(option);
}

// 新成交额图表
function updateVolumeChart(data) {
    if (typeof echarts === 'undefined') {
        console.error('ECharts 未加载');
        return;
    }

    const chartContainer = document.getElementById('volume-chart');
    if (!chartContainer) {
        console.error('未找到图表容器');
        return;
    }

    const chart = echarts.init(chartContainer);
    
    // 处理数据
    const volumes = data.dates.map(date => {
        const dailyData = data.daily_changes[date];
        return {
            date: date,
            value: dailyData.total_amount,
            display: dailyData.total_amount_str
        };
    });

    const option = {
        title: {
            text: '板块交额统计',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                const data = volumes[params[0].dataIndex];
                return `${data.date}<br/>成交额: ${data.display}`;
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                rotate: 30
            }
        },
        yAxis: {
            type: 'value',
            name: '成额(亿元)',
            axisLabel: {
                formatter: function(value) {
                    return (value).toFixed(2);
                }
            }
        },
        series: [{
            name: '成交额',
            type: 'bar',
            data: volumes.map(v => v.value),
            label: {
                show: true,
                position: 'top',
                formatter: function(params) {
                    return volumes[params.dataIndex].display;
                }
            }
        }]
    };

    chart.setOption(option);
}

// 显示个股详情
async function showStockDetail(stockCode) {
    try {
        console.log('显示个股详情, stockCode:', stockCode);
        const response = await fetch(`/api/get_stock_detail/${stockCode}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || '获取个股详情失败');
        }
        
        // 取图表容器
        const chartContainer = document.getElementById('stock-detail-chart');
        if (!chartContainer) {
            console.error('未找到图表容器');
            return;
        }
        
        // 初始化图表
        const chart = echarts.init(chartContainer);
        
        // 处理数据
        const stockData = data.stock_data;
        if (!stockData || !stockData.dates || !stockData.price_chart || !stockData.volume_chart) {
            throw new Error('数据格式错误');
        }

        // 将成交额从千元转换为亿元（除以10）
        const volumeData = stockData.volume_chart.series[0].data.map(value => {
            if (value != null && !isNaN(value)) {

                const volumeInYi = value;
                console.log(`原始值(亿元): ${value}, 修正后(亿元): ${volumeInYi}`);
                return volumeInYi;
            }
            return 0;
        });
        
        console.log('成交额数据(亿元):', volumeData);
        
        // 置图表选项
        const option = {
            title: {
                text: `${stockData.name} 涨跌幅和成交额`,
                left: 'center',
                top: 10,
                textStyle: {
                    fontSize: 16
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                formatter: function(params) {
                    if (!Array.isArray(params) || params.length < 2) {
                        return '';
                    }
                    const date = params[0].axisValue;
                    const change = params[0].data.value !== undefined ? 
                        params[0].data.value.toFixed(2) : '0.00';
                    const volume = params[1].value !== undefined ? 
                        params[1].value.toFixed(2) : '0.00';
                    return `${date}<br/>
                           涨幅: ${change}%<br/>
                           成交额: ${volume}亿元`;
                }
            },
            legend: {
                data: ['涨跌幅(%)', '成交额(亿元)'],
                top: 40,
                textStyle: {
                    fontSize: 12
                }
            },
            grid: [{
                left: '8%',
                right: '8%',
                top: '25%',
                height: '30%'
            }, {
                left: '8%',
                right: '8%',
                top: '65%',
                height: '30%'
            }],
            xAxis: [{
                type: 'category',
                data: stockData.dates,
                axisLabel: {
                    rotate: 30,
                    fontSize: 10
                },
                gridIndex: 0
            }, {
                type: 'category',
                data: stockData.dates,
                axisLabel: {
                    rotate: 30,
                    fontSize: 10
                },
                gridIndex: 1
            }],
            yAxis: [{
                type: 'value',
                name: '涨跌幅(%)',
                nameTextStyle: {
                    fontSize: 12
                },
                gridIndex: 0,
                axisLabel: {
                    formatter: '{value}%',
                    fontSize: 10
                }
            }, {
                type: 'value',
                name: '成交额(亿元)',
                nameTextStyle: {
                    fontSize: 12
                },
                gridIndex: 1,
                axisLabel: {
                    formatter: function(value) {
                        return value.toFixed(2);
                    },
                    fontSize: 10
                }
            }],
            series: [{
                name: '涨(%)',
                type: 'bar',
                data: stockData.price_chart.series[0].data.map(value => ({
                    value: value,
                    itemStyle: {
                        color: value >= 0 ? '#c23531' : '#2f4554'
                    }
                })),
                gridIndex: 0,
                xAxisIndex: 0,
                yAxisIndex: 0,
                label: {
                    show: true,
                    position: 'top',
                    formatter: '{c}%',
                    fontSize: 10
                }
            }, {
                name: '成交额(亿元)',
                type: 'bar',
                data: volumeData,
                gridIndex: 1,
                xAxisIndex: 1,
                yAxisIndex: 1,
                label: {
                    show: true,
                    position: 'top',
                    formatter: function(params) {
                        return params.value.toFixed(2);
                    },
                    fontSize: 10
                }
            }]
        };
        
        // 设置图表
        chart.setOption(option);
        
        // 显示所属板块信息
        if (data.sectors && data.sectors.length > 0) {
            const sectorInfo = data.sectors.map(s => 
                `<span class="badge bg-info me-1">${s.name}</span>`
            ).join('');
            
            // 查找现有的板块信息div
            let sectorDiv = document.getElementById('stock-sectors-info');
            if (!sectorDiv) {
                // 果不存在则创建新的
                sectorDiv = document.createElement('div');
                sectorDiv.id = 'stock-sectors-info';  // 添加固定ID
                sectorDiv.className = 'mt-2';
                chartContainer.parentNode.appendChild(sectorDiv);
            }
            
            // 更新内容
            sectorDiv.innerHTML = `<small class="text-muted">所属板块：${sectorInfo}</small>`;
        } else {
            // 如果没有板块信息，移除现有的板块信息div
            const existingSectorDiv = document.getElementById('stock-sectors-info');
            if (existingSectorDiv) {
                existingSectorDiv.remove();
            }
        }
        
        // 在显示完基本信息后，显示资金流向
        await showMoneyFlow(stockCode);
        
    } catch (error) {
        console.error('显示个股详情失败:', error);
        const chartContainer = document.getElementById('stock-detail-chart');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="alert alert-danger">
                    加载失败: ${error.message}
                </div>
            `;
        }
        
        // 出错时也清除板块信息
        const existingSectorDiv = document.getElementById('stock-sectors-info');
        if (existingSectorDiv) {
            existingSectorDiv.remove();
        }
    }
}

// 显示个股资金流向
async function showMoneyFlow(stockCode) {
    try {
        console.log('获取个股资金流向数据, stockCode:', stockCode);
        const response = await fetch(`/api/get_money_flow/${stockCode}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || '获取资金流向数据失败');
        }

        // 初始化三个图表容器
        const chartContainer1 = document.getElementById('money-flow-chart1');
        const chartContainer2 = document.getElementById('money-flow-chart2');
        const chartContainer3 = document.getElementById('money-flow-chart3');
        
        if (!chartContainer1 || !chartContainer2 || !chartContainer3) {
            console.error('未找到资金流向图表容器');
            return;
        }

        // 初始化三个图表实例
        const chart1 = echarts.init(chartContainer1);
        const chart2 = echarts.init(chartContainer2);
        const chart3 = echarts.init(chartContainer3);

        // 处理数据
        const dates = data.dates;
        const buySmall = data.buy_sm_vol.map(vol => vol / 100000); // 转换为亿元
        const sellSmall = data.sell_sm_vol.map(vol => vol / 100000);
        const buyMedium = data.buy_md_vol.map(vol => vol / 100000);
        const sellMedium = data.sell_md_vol.map(vol => vol / 100000);
        const buyLarge = data.buy_lg_vol.map(vol => vol / 100000);
        const sellLarge = data.sell_lg_vol.map(vol => vol / 100000);
        const buyExtra = data.buy_elg_vol.map(vol => vol / 100000);
        const sellExtra = data.sell_elg_vol.map(vol => vol / 100000);
        const netFlow = data.net_mf_vol.map(vol => vol / 100000);

        // 买入资金图表配置
        const option1 = {
            title: {
                text: '买入资金(亿元)',
                left: 'center',
                top: 10
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['小单买入', '中单买入', '大单买入', '特大单买入'],
                top: 30
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: dates,
                axisLabel: {
                    rotate: 30
                }
            },
            yAxis: {
                type: 'value',
                name: '金额(亿元)'
            },
            series: [
                {
                    name: '小单买入',
                    type: 'line',
                    data: buySmall,
                    itemStyle: { color: '#c23531' }
                },
                {
                    name: '中单买入',
                    type: 'line',
                    data: buyMedium,
                    itemStyle: { color: '#2f4554' }
                },
                {
                    name: '大单买入',
                    type: 'line',
                    data: buyLarge,
                    itemStyle: { color: '#61a0a8' }
                },
                {
                    name: '特大单买入',
                    type: 'line',
                    data: buyExtra,
                    itemStyle: { color: '#d48265' }
                }
            ]
        };

        // 卖出资金图表配置
        const option2 = {
            title: {
                text: '卖出资金(亿元)',
                left: 'center',
                top: 10
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['小单卖出', '中单卖出', '大单卖出', '特大单卖出'],
                top: 30
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: dates,
                axisLabel: {
                    rotate: 30
                }
            },
            yAxis: {
                type: 'value',
                name: '金额(亿元)'
            },
            series: [
                {
                    name: '小单卖出',
                    type: 'line',
                    data: sellSmall,
                    itemStyle: { color: '#91c7ae' }
                },
                {
                    name: '中单卖出',
                    type: 'line',
                    data: sellMedium,
                    itemStyle: { color: '#749f83' }
                },
                {
                    name: '大单卖出',
                    type: 'line',
                    data: sellLarge,
                    itemStyle: { color: '#ca8622' }
                },
                {
                    name: '特大单卖出',
                    type: 'line',
                    data: sellExtra,
                    itemStyle: { color: '#bda29a' }
                }
            ]
        };

        // 流入图表配置
        const option3 = {
            title: {
                text: '每日净流入金额(亿元)',
                left: 'center',
                top: 10
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: dates,
                axisLabel: {
                    rotate: 30
                }
            },
            yAxis: {
                type: 'value',
                name: '金额(亿元)'
            },
            series: [
                {
                    name: '净流入',
                    type: 'line',
                    data: netFlow,
                    itemStyle: {
                        color: function(params) {
                            return params.value >= 0 ? '#c23531' : '#2f4554';
                        }
                    },
                    areaStyle: {
                        color: function(params) {
                            return params.value >= 0 ? 
                                new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                    { offset: 0, color: 'rgba(194, 53, 49, 0.3)' },
                                    { offset: 1, color: 'rgba(194, 53, 49, 0.1)' }
                                ]) : 
                                new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                    { offset: 0, color: 'rgba(47, 69, 84, 0.3)' },
                                    { offset: 1, color: 'rgba(47, 69, 84, 0.1)' }
                                ]);
                        }
                    }
                }
            ]
        };

        // 设置图表
        chart1.setOption(option1);
        chart2.setOption(option2);
        chart3.setOption(option3);
        
    } catch (error) {
        console.error('显示资金流向失败:', error);
        const containers = [
            document.getElementById('money-flow-chart1'),
            document.getElementById('money-flow-chart2'),
            document.getElementById('money-flow-chart3')
        ];
        
        containers.forEach(container => {
            if (container) {
                container.innerHTML = `
                    <div class="alert alert-danger">
                        加载失败: ${error.message}
                    </div>
                `;
            }
        });
    }
}

// 显示板块成分股列表
async function showSectorStocks(sectorId) {
    try {
        console.log('显示板块成分股, sectorId:', sectorId);
        const response = await fetch(`/api/get_sector_members/${sectorId}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || '获取成分股列表失败');
        }
        
        // 更新标题
        const title = document.getElementById('stock-detail-title');
        if (title) {
            title.textContent = `${data.sector_name} - 成分股列表`;
        }
        
        // 更新表格内容
        const tableBody = document.getElementById('stock-detail-table')?.querySelector('tbody');
        if (!tableBody) {
            console.error('未找到成分股表格容器');
            return;
        }
        
        if (data.stocks && data.stocks.length > 0) {
            console.log(`显示 ${data.stocks.length} 只成分股`);
            const html = data.stocks.map(stock => `
                <tr>
                    <td>${stock.code}</td>
                    <td>${stock.name || stock.code}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger" 
                                onclick="removeStockFromSector('${stock.code}', ${sectorId})">
                            删除
                        </button>
                    </td>
                </tr>
            `).join('');
            tableBody.innerHTML = html;
        } else {
            console.log('没有成分股数据');
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center">暂无数据</td></tr>';
        }
        
    } catch (error) {
        console.error('显示成分股列表失败:', error);
        const tableBody = document.getElementById('stock-detail-table')?.querySelector('tbody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center text-danger">
                        加载失败: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
}

// 从板块中删除股票
async function removeStockFromSector(stockCode, sectorId) {
    try {
        if (!confirm(`确定要从板块中删除股票 ${stockCode} 吗？`)) {
            return;
        }
        
        console.log(`删除股票 ${stockCode} 从板块 ${sectorId}`);
        const response = await fetch('/api/remove_sector_stock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sector_id: sectorId,
                stock_code: stockCode
            })
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '删除失败');
        }
        
        // 重新加载成分股列表
        await showSectorStocks(sectorId);
        // 刷新板块表格
        await refreshSectorTable();
        
    } catch (error) {
        console.error('删除股票失败:', error);
        alert('删除失败: ' + error.message);
    }
}

// 加载板块寻龙的板块列表
async function loadDragonSectorList() {
    try {
        console.log('开始加载板块寻龙列表');
        const response = await fetch('/api/get_sectors');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || '获取板块列表失败');
        }
        
        const sectorList = document.getElementById('dragon-sector-list');
        if (!sectorList) {
            console.error('未找到板块列表容器');
            return;
        }
        
        // 生成板块列表HTML，添加 small 类
        const html = data.sectors.map(sector => `
            <button class="list-group-item list-group-item-action d-flex justify-content-between align-items-center py-1 small"
                    onclick="loadSectorDetails(${sector.id}, '${sector.name}')">
                <span>${sector.name}</span>
                <span class="badge bg-secondary">${sector.stock_count}</span>
            </button>
        `).join('');
        
        sectorList.innerHTML = html;
        console.log('板块寻龙列表加载完成');
        
    } catch (error) {
        console.error('加载板块寻龙列表失败:', error);
        const sectorList = document.getElementById('dragon-sector-list');
        if (sectorList) {
            sectorList.innerHTML = `
                <div class="alert alert-danger">
                    加载失败: ${error.message}
                </div>
            `;
        }
    }
}

// 加载板块成分股详细信息
async function loadSectorDetails(sectorId, sectorName) {
    try {
        console.log('加载板块详细信息:', sectorId, sectorName);
        const response = await fetch(`/api/get_sector_details/${sectorId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('获取到成分股数据:', data);
        
        if (!data.success) {
            throw new Error(data.message || '获取板块详细信息失败');
        }
        
        // 更新标题
        const title = document.getElementById('dragon-sector-title');
        if (title) {
            title.textContent = `${data.sector_name} - 基本面数据 (${data.report_date})`;
        }
        
        // 保存数据到全局变量
        dragonStockData = data.stocks;
        
        // 应用排序和筛选并更新表格
        updateDragonTable();
        
    } catch (error) {
        console.error('加载板块详细信息失败:', error);
        const tableBody = document.getElementById('dragon-stock-table');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger">
                        加载失败: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
}

// 更新格显示
function updateDragonTable() {
    const tableBody = document.getElementById('dragon-stock-table');
    if (!tableBody) return;
    
    console.log('开始筛选，当前筛选条件:', dragonFilters);
    console.log('原始数据数量:', dragonStockData.length);
    
    // 应用筛选
    let filteredData = dragonStockData.filter(stock => {
        return Object.entries(dragonFilters).every(([field, minValue]) => {
            if (!minValue) return true;  // 如果没有设置筛选值，则不筛选
            const value = stock[field];
            if (value === null || value === undefined) return false;
            
            // 转换为数字进行比较
            const numValue = parseFloat(value);
            const numMinValue = parseFloat(minValue);
            
            if (isNaN(numValue) || isNaN(numMinValue)) return true;
            return numValue >= numMinValue;
        });
    });
    
    console.log('筛选后数据数量:', filteredData.length);
    
    // 应用排序
    filteredData.sort((a, b) => {
        const aValue = a[dragonSortField] ?? -Infinity;
        const bValue = b[dragonSortField] ?? -Infinity;
        const order = dragonSortOrder === 'asc' ? 1 : -1;
        return (aValue - bValue) * order;
    });
    
    // 更新表格
    const html = filteredData.map(stock => `
        <tr>
            <td>${stock.code}</td>
            <td>${stock.name}</td>
            <td class="text-end">${stock.market_value?.toFixed(2) || '-'}</td>
            <td class="text-end">${stock.revenue?.toFixed(2) || '-'}</td>
            <td class="text-end">${stock.net_profit?.toFixed(2) || '-'}</td>
            <td class="text-end">${stock.gross_margin?.toFixed(2) || '-'}</td>
            <td class="text-end">${stock.debt_ratio?.toFixed(2) || '-'}</td>
        </tr>
    `).join('');
    
    tableBody.innerHTML = html || '<tr><td colspan="7" class="text-center">暂无数据</td></tr>';
}

// 初始化排序和筛选功能
function initializeDragonSortAndFilter() {
    // 绑定表头点击排序事件
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const field = th.dataset.sort;
            if (field === dragonSortField) {
                dragonSortOrder = dragonSortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                dragonSortField = field;
                dragonSortOrder = 'desc';
            }
            updateDragonTable();
            
            // 更新排序指示器
            document.querySelectorAll('th[data-sort]').forEach(el => {
                el.classList.remove('sorting-asc', 'sorting-desc');
            });
            th.classList.add(`sorting-${dragonSortOrder}`);
        });
    });
    
    // 绑定筛选输入框事件
    document.querySelectorAll('.dragon-filter').forEach(input => {
        input.addEventListener('input', debounce(() => {
            const field = input.dataset.field;
            const value = input.value.trim();
            
            console.log(`筛选字段 ${field} 设置为 ${value}`);
            
            if (field) {
                dragonFilters[field] = value ? value : null;
                updateDragonTable();
            }
        }, 300));  // 300ms 防抖
    });
    
    // 绑定重置按钮事件
    document.getElementById('reset-filters')?.addEventListener('click', () => {
        // 清空输入框
        document.querySelectorAll('.dragon-filter').forEach(input => {
            input.value = '';
        });
        // 重置筛选条件
        Object.keys(dragonFilters).forEach(key => {
            dragonFilters[key] = null;
        });
        updateDragonTable();
    });
}

// 更新进度条
function updateProgressBar(progressBar, progress) {
    if (!progressBar) return;
    progressBar.style.width = `${progress}%`;
    progressBar.setAttribute('aria-valuenow', progress);
    progressBar.textContent = `${progress}%`;
}

// 监控更新进度
async function monitorUpdateProgress(progressBar) {
    while (true) {
        try {
            const response = await fetch('/api/update_progress');
            const data = await response.json();
            
            if (!data.is_updating) {
                progressBar.parentElement.classList.add('d-none');
                break;
            }
            
            // 更新进度条
            progressBar.style.width = `${data.progress}%`;
            progressBar.setAttribute('aria-valuenow', data.progress);
            progressBar.textContent = `${data.progress}%`;
            
            // 等待一秒后再次检查
            await new Promise(resolve => setTimeout(resolve, 1000));
            
        } catch (error) {
            console.error('获取更新进度失败:', error);
            break;
        }
    }
}

// 更新财务数据
async function updateFinancialData() {
    try {
        const btn = document.getElementById('update-finance-btn');
        const progress = document.getElementById('finance-progress');
        const progressBar = progress.querySelector('.progress-bar');
        
        btn.disabled = true;
        progress.classList.remove('d-none');
        
        // 开始监控进度
        monitorUpdateProgress(progressBar);
        
        const response = await fetch('/api/update_financial_data', {
            method: 'POST'
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message);
        }
        
        alert(data.message);
        
    } catch (error) {
        console.error('更新财务数据失败:', error);
        alert('更新失败: ' + error.message);
    } finally {
        btn.disabled = false;
    }
}

async function updateSingleStock() {
    try {
        const input = document.getElementById('single-stock-code');
        const stockCode = input.value.trim();
        
        if (!stockCode) {
            alert('请输入股票代码');
            return;
        }
        
        const btn = document.getElementById('update-single-stock-btn');
        btn.disabled = true;
        
        const response = await fetch(`/api/update_single_stock/${stockCode}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message);
        }
        
        alert('股票数据更新完成');
        input.value = '';
        
    } catch (error) {
        console.error('更新单只股票数据失败:', error);
        alert('更新失败: ' + error.message);
    } finally {
        document.getElementById('update-single-stock-btn').disabled = false;
    }
}

async function updateDailyBasic(date = null) {
    try {
        const btn = date ? 
            document.getElementById('update-history-daily-btn') :
            document.getElementById('update-daily-btn');
        
        btn.disabled = true;
        
        const url = date ? 
            `/api/update_daily_basic/${date}` :
            '/api/update_daily_basic';
            
        const response = await fetch(url, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message);
        }
        
        alert('每日指标更新完成');
        
    } catch (error) {
        console.error('更新每日指标失败:', error);
        alert('更新失败: ' + error.message);
    } finally {
        document.getElementById('update-daily-btn').disabled = false;
        document.getElementById('update-history-daily-btn').disabled = false;
    }
}

// 保存板块和成分股
async function saveSectorStocks() {
    try {
        const sectorName = document.getElementById('sector-name').value.trim();
        const stocksInput = document.getElementById('sector-stocks').value.trim();
        
        if (!sectorName) {
            alert('请输入板块名称');
            return;
        }
        
        const stockCodes = stocksInput ? stocksInput.split(',').map(code => code.trim()).filter(code => code) : [];
        
        console.log('保存板块:', sectorName, '股票:', stockCodes);
        
        const response = await fetch('/api/save_sector_stocks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: sectorName,
                stocks: stockCodes
            })
        });
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '保存失败');
        }
        
        // 清空输入框
        document.getElementById('sector-name').value = '';
        document.getElementById('sector-stocks').value = '';
        
        // 刷新板块列表
        await refreshSectorTable();
        
        alert('保存成功');
        
    } catch (error) {
        console.error('保存板块失败:', error);
        alert('保存板块失败: ' + error.message);
    }
}

// 更新历史数据
async function updateHistoricalData() {
    try {
        console.log('开始更新历史数据');
        const startBtn = document.getElementById('start-update-btn');
        const stopBtn = document.getElementById('stop-update-btn');
        const progressBar = document.querySelector('.progress-bar');
        
        if (!startBtn || !stopBtn || !progressBar) {
            console.error('未找到必要的 DOM 元素');
            return;
        }
        
        // 禁用开始按钮，启用停止按钮
        startBtn.disabled = true;
        stopBtn.disabled = false;
        
        // 显示进度条
        progressBar.parentElement.classList.remove('d-none');
        
        // 发送更新请求
        const response = await fetch('/api/update_historical_data', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 开始轮询进度
        await monitorUpdateProgress(progressBar);
        
    } catch (error) {
        console.error('更新历史数据失败:', error);
        alert('更新失败: ' + error.message);
    } finally {
        // 恢复按钮状态
        const startBtn = document.getElementById('start-update-btn');
        const stopBtn = document.getElementById('stop-update-btn');
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
    }
}

// 停止更新
async function stopHistoricalData() {
    try {
        console.log('停止更新历史数据');
        const response = await fetch('/api/stop_update', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 恢复按钮状态
        const startBtn = document.getElementById('start-update-btn');
        const stopBtn = document.getElementById('stop-update-btn');
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        
    } catch (error) {
        console.error('停止更新失败:', error);
        alert('停止失败: ' + error.message);
    }
}