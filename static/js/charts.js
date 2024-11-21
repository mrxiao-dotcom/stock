// 全局图表实例
let timelineChart = null;
let volumeChart = null;
let stockDailyChart = null;
let moneyFlowChart = null;
let netInflowChart = null;

// 全局图表配置
const CHART_COLORS = {
    UP: '#ff4d4f',
    DOWN: '#52c41a',
    VOLUME: {
        START: '#83bff6',
        MIDDLE: '#188df0',
        END: '#188df0'
    }
};

const CHART_TITLE_STYLE = {
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center'
};

const CHART_GRID = {
    top: 70,
    right: '3%',
    bottom: 30,
    left: '3%',
    containLabel: true
};

const AXIS_LABEL_STYLE = {
    fontSize: 10,
    color: '#666'
};

// 图表基础配置
const CHART_CONFIG = {
    grid: CHART_GRID,
    title: {
        ...CHART_TITLE_STYLE,
        left: 'center',
        top: 10
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross'
        }
    },
    axisLabel: AXIS_LABEL_STYLE
};

// 确保图表实例存在
function ensureChartInitialized(chartInstance, elementId) {
    if (!chartInstance) {
        const element = document.getElementById(elementId);
        if (element) {
            console.log(`初始化图表: ${elementId}`);
            const rect = element.getBoundingClientRect();
            console.log(`图表容器尺寸: ${rect.width}x${rect.height}`);
            if (rect.width > 0 && rect.height > 0) {
                return echarts.init(element);
            } else {
                console.warn(`图表容器尺寸无效: ${elementId}`);
            }
        } else {
            console.warn(`未找到图表容器: ${elementId}`);
        }
    }
    return chartInstance;
}

// 初始化图表
function initializeCharts() {
    console.log('初始化所有图表...');
    
    // 清除旧的图表实例
    [timelineChart, volumeChart, stockDailyChart, moneyFlowChart, netInflowChart].forEach(chart => {
        if (chart) {
            chart.dispose();
        }
    });

    // 重置图表实例
    timelineChart = null;
    volumeChart = null;
    stockDailyChart = null;
    moneyFlowChart = null;
    netInflowChart = null;

    // 等待DOM更新
    setTimeout(() => {
        // 初始化所有图表
        timelineChart = ensureChartInitialized(timelineChart, 'timeline-chart');
        volumeChart = ensureChartInitialized(volumeChart, 'volume-chart');
        stockDailyChart = ensureChartInitialized(stockDailyChart, 'stock-daily-chart');
        moneyFlowChart = ensureChartInitialized(moneyFlowChart, 'money-flow-chart');
        netInflowChart = ensureChartInitialized(netInflowChart, 'net-inflow-chart');

        // 调整所有图表大小
        resizeAllCharts();
    }, 0);
}

// 调整图表大小
function resizeAllCharts() {
    const charts = [
        { instance: timelineChart, id: 'timeline-chart' },
        { instance: volumeChart, id: 'volume-chart' },
        { instance: stockDailyChart, id: 'stock-daily-chart' },
        { instance: moneyFlowChart, id: 'money-flow-chart' },
        { instance: netInflowChart, id: 'net-inflow-chart' }
    ];

    charts.forEach(({ instance, id }) => {
        if (!instance) {
            instance = ensureChartInitialized(instance, id);
        }
        if (instance) {
            try {
                instance.resize();
            } catch (e) {
                console.error(`调整图表大小失败 ${id}:`, e);
            }
        }
    });
}

// 更新个股日线图表
function updateStockDailyChart(data) {
    stockDailyChart = ensureChartInitialized(stockDailyChart, 'stock-daily-chart');
    if (!stockDailyChart) {
        console.warn('个股日线图表初始化失败');
        return;
    }

    console.log('更新K线图数据:', data);

    // 计算涨跌幅
    const changes = [];
    for (let i = 1; i < data.dates.length; i++) {
        const prevClose = data.closes[i-1];
        const currClose = data.closes[i];
        const change = ((currClose - prevClose) / prevClose * 100).toFixed(2);
        changes.push(parseFloat(change));
    }
    changes.unshift(0);  // 第一天的涨跌幅为0

    const option = {
        title: {
            text: `${data.name}K线`,
            ...CHART_TITLE_STYLE,
            left: 'center',
            top: 5
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            formatter: function(params) {
                const date = params[0].axisValue;
                let html = `${date}<br/>`;
                params.forEach(param => {
                    if (param.seriesName === '涨跌幅') {
                        const color = param.value >= 0 ? CHART_COLORS.UP : CHART_COLORS.DOWN;
                        html += `<span style="color:${color}">
                            ${param.seriesName}: ${param.value.toFixed(2)}%
                        </span><br/>`;
                    } else if (param.seriesName === '成交额') {
                        html += `${param.seriesName}: ${(param.value/100000000).toFixed(2)}亿<br/>`;
                    }
                });
                return html;
            }
        },
        legend: {
            data: ['涨跌幅', '成交额'],
            top: 30,
            right: 10,
            textStyle: { fontSize: 12 }
        },
        grid: CHART_GRID,
        xAxis: {
            type: 'category',
            data: data.dates,
            boundaryGap: false,
            axisLabel: {
                ...AXIS_LABEL_STYLE,
                rotate: 30,
                formatter: value => value.substring(5)
            }
        },
        yAxis: [{
            type: 'value',
            name: '涨跌幅(%)',
            position: 'left',
            nameTextStyle: AXIS_LABEL_STYLE,
            axisLabel: {
                ...AXIS_LABEL_STYLE,
                formatter: '{value}%'
            },
            splitLine: {
                show: true,
                lineStyle: {
                    type: 'dashed',
                    color: '#eee'
                }
            }
        }, {
            type: 'value',
            name: '成交额(亿元)',
            position: 'right',
            nameTextStyle: AXIS_LABEL_STYLE,
            axisLabel: {
                ...AXIS_LABEL_STYLE,
                formatter: value => (value/100000000).toFixed(1)
            },
            splitLine: {
                show: false
            }
        }],
        series: [{
            name: '涨跌幅',
            type: 'line',
            data: changes,
            itemStyle: {
                color: params => params.value >= 0 ? CHART_COLORS.UP : CHART_COLORS.DOWN
            },
            lineStyle: {
                width: 1,
                color: CHART_COLORS.UP
            },
            areaStyle: {
                opacity: 0.2,
                color: params => params.value >= 0 ? CHART_COLORS.UP : CHART_COLORS.DOWN
            },
            markPoint: {
                data: [
                    {type: 'max', name: '最大值'},
                    {type: 'min', name: '最小值'}
                ],
                label: {
                    fontSize: 10
                },
                symbolSize: 30
            },
            markLine: {
                data: [{
                    type: 'average',
                    name: '平均值'
                }],
                label: {
                    fontSize: 10
                }
            }
        }, {
            name: '成交额',
            type: 'bar',
            yAxisIndex: 1,
            data: data.volumes,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    {offset: 0, color: CHART_COLORS.VOLUME.START},
                    {offset: 0.5, color: CHART_COLORS.VOLUME.MIDDLE},
                    {offset: 1, color: CHART_COLORS.VOLUME.END}
                ])
            }
        }],
        dataZoom: [{
            type: 'inside',
            start: 0,
            end: 100
        }, {
            type: 'slider',
            show: true,
            bottom: 5,
            height: 20,
            borderColor: 'transparent'
        }]
    };
    
    stockDailyChart.setOption(option);
}

// 更新时间轴图表
function updateTimelineChart(data) {
    if (!timelineChart) {
        console.warn('时间轴图表未初始化');
        return;
    }

    console.log('更新时间轴图表数据:', data);

    if (!data || !data.daily_changes || !data.dates) {
        console.error('无效的数据格式:', data);
        return;
    }

    // 处理数据
    const dates = data.dates;
    const timelineData = [];

    // 获取第一天的数据作为基准
    const firstDate = dates[0];
    const firstDayData = data.daily_changes[firstDate];
    
    if (!firstDayData || !firstDayData.stocks) {
        console.error('无效的首日数据:', firstDayData);
        return;
    }

    // 创建基准价格映射
    const basePrices = {};
    firstDayData.stocks.forEach(stock => {
        if (stock.close) {
            basePrices[stock.code] = parseFloat(stock.close);
        }
    });

    // 对每一天的数据进行处理
    dates.forEach(date => {
        const dayData = data.daily_changes[date];
        if (dayData && dayData.stocks) {
            // 计算每只股票相对于首日的涨跌幅
            const stockChanges = dayData.stocks
                .filter(stock => basePrices[stock.code] && stock.close)  // 确保有基准价和当日收盘价
                .map(stock => {
                    const basePrice = basePrices[stock.code];
                    const currentPrice = parseFloat(stock.close);
                    const change = ((currentPrice - basePrice) / basePrice * 100);
                    return {
                        name: stock.name,
                        code: stock.code,
                        value: parseFloat(change.toFixed(1))
                    };
                });

            // 按涨跌幅从小到大排序
            stockChanges.sort((a, b) => a.value - b.value);

            timelineData.push({
                date: date,
                stocks: stockChanges
            });
        }
    });

    const option = {
        baseOption: {
            timeline: {
                axisType: 'category',
                autoPlay: false,
                playInterval: 3000,
                data: dates.map(date => date.substring(5)),  // 只显示月-日
                label: {
                    formatter: function(s) {
                        return s;
                    },
                    fontSize: 12
                },
                bottom: 5,  // 调整时间轴位置
                height: 30,
                emphasis: {
                    itemStyle: {
                        color: '#188df0'
                    }
                },
                controlStyle: {
                    showNextBtn: true,
                    showPrevBtn: true,
                    normal: {
                        color: '#188df0',
                        borderColor: '#188df0'
                    }
                }
            },
            title: [{
                text: '板块累计涨幅',
                ...CHART_TITLE_STYLE,
                left: 'center',
                top: 10
            }, {
                text: '(相对9月20日)',
                top: 30,
                left: 'center',
                textStyle: {
                    fontSize: 12,
                    color: '#666',
                    fontWeight: 'normal'
                }
            }],
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            grid: {
                top: 70,      // 增加顶部空间
                right: '3%',
                bottom: 60,   // 增加底部空间
                left: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                axisLabel: {
                    interval: 0,
                    rotate: 30,
                    fontSize: 10
                }
            },
            yAxis: {
                type: 'value',
                name: '累计涨幅',
                nameTextStyle: { 
                    fontSize: 12,
                    padding: [0, 30, 0, 0]
                },
                axisLabel: {
                    fontSize: 12,
                    formatter: value => value.toFixed(1)
                },
                splitLine: {
                    show: true,
                    lineStyle: {
                        type: 'dashed',
                        color: '#eee'
                    }
                }
            }
        },
        options: timelineData.map(dayData => ({
            title: {
                subtext: `(${dayData.date})`
            },
            xAxis: {
                data: dayData.stocks.map(stock => stock.name)
            },
            series: [{
                type: 'bar',
                data: dayData.stocks.map(stock => ({
                    name: stock.name,
                    value: stock.value,
                    itemStyle: {
                        color: stock.value >= 0 ? CHART_COLORS.UP : CHART_COLORS.DOWN
                    }
                })),
                label: {
                    show: true,
                    position: 'top',
                    formatter: params => params.data.value.toFixed(1),
                    fontSize: 10,
                    color: params => params.data.value >= 0 ? CHART_COLORS.UP : CHART_COLORS.DOWN
                },
                barWidth: '60%'
            }]
        }))
    };
    
    timelineChart.setOption(option);
}

// 更新成交额图表
function updateVolumeChart(data) {
    if (!volumeChart) {
        console.warn('成交额图表未初始化');
        return;
    }

    console.log('更新成交额图表数据:', data);

    const option = {
        ...CHART_CONFIG,
        title: {
            ...CHART_CONFIG.title,
            text: '板块成交额'
        },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                return `${params[0].axisValue}<br/>
                        成交额: ${(params[0].value/100000000).toFixed(2)}亿元`;
            }
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                fontSize: 10,
                rotate: 30,
                formatter: value => value.substring(5)
            }
        },
        yAxis: {
            type: 'value',
            name: '成交额(亿元)',
            nameTextStyle: {
                fontSize: 12,
                padding: [0, 30, 0, 0]
            },
            axisLabel: {
                fontSize: 10,
                formatter: value => (value/100000000).toFixed(1)
            },
            splitLine: {
                show: true,
                lineStyle: {
                    type: 'dashed',
                    color: '#eee'
                }
            }
        },
        series: [{
            type: 'bar',
            data: data.volumes,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    {offset: 0, color: CHART_COLORS.VOLUME.START},
                    {offset: 0.5, color: CHART_COLORS.VOLUME.MIDDLE},
                    {offset: 1, color: CHART_COLORS.VOLUME.END}
                ])
            }
        }]
    };
    
    volumeChart.setOption(option);
}

// 更新资金流向图表
function updateMoneyFlowChart(data) {
    moneyFlowChart = ensureChartInitialized(moneyFlowChart, 'money-flow-chart');
    if (!moneyFlowChart) {
        console.warn('资金流向图表初始化失败');
        return;
    }

    console.log('更新资金流向图表:', data);

    const option = {
        ...CHART_CONFIG,
        title: {
            ...CHART_CONFIG.title,
            text: '资金流向'
        },
        legend: {
            data: ['超大单流入', '超大单流出', '大单流入', '大单流出'],
            top: 30,
            right: 10,
            textStyle: { fontSize: 12 }
        },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                let html = `${params[0].axisValue}<br/>`;
                params.forEach(param => {
                    const value = (param.value / 10000).toFixed(2);
                    const color = param.seriesName.includes('流入') ? CHART_COLORS.UP : CHART_COLORS.DOWN;
                    html += `<span style="color:${color}">${param.seriesName}: ${value}万</span><br/>`;
                });
                return html;
            }
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                ...AXIS_LABEL_STYLE,
                rotate: 30,
                formatter: value => value.substring(5)
            }
        },
        yAxis: {
            type: 'value',
            name: '金额(万)',
            nameTextStyle: AXIS_LABEL_STYLE,
            axisLabel: {
                ...AXIS_LABEL_STYLE,
                formatter: value => (value / 10000).toFixed(1)
            }
        },
        series: [
            {
                name: '超大单流入',
                type: 'line',
                data: data.super_large_inflow,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: CHART_COLORS.UP }
            },
            {
                name: '超大单流出',
                type: 'line',
                data: data.super_large_outflow,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: '#ff7875' }
            },
            {
                name: '大单流入',
                type: 'line',
                data: data.large_inflow,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: '#52c41a' }
            },
            {
                name: '大单流出',
                type: 'line',
                data: data.large_outflow,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: '#73d13d' }
            }
        ]
    };
    
    moneyFlowChart.setOption(option);
}

// 更新资金净流入图表
function updateNetInflowChart(data) {
    netInflowChart = ensureChartInitialized(netInflowChart, 'net-inflow-chart');
    if (!netInflowChart) {
        console.warn('资金净流入图表初始化失败');
        return;
    }

    console.log('更新资金净流入图表:', data);

    const option = {
        ...CHART_CONFIG,
        title: {
            ...CHART_CONFIG.title,
            text: '资金净流入'
        },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                const value = params[0].value;
                const color = value >= 0 ? CHART_COLORS.UP : CHART_COLORS.DOWN;
                return `${params[0].axisValue}<br/>
                        <span style="color:${color}">净流入: ${(value/10000).toFixed(2)}万</span>`;
            }
        },
        xAxis: {
            type: 'category',
            data: data.dates,
            axisLabel: {
                ...AXIS_LABEL_STYLE,
                rotate: 30,
                formatter: value => value.substring(5)
            }
        },
        yAxis: {
            type: 'value',
            name: '金额(万)',
            nameTextStyle: AXIS_LABEL_STYLE,
            axisLabel: {
                ...AXIS_LABEL_STYLE,
                formatter: value => (value/10000).toFixed(1)
            }
        },
        series: [{
            type: 'bar',
            data: data.net_inflow,
            itemStyle: {
                color: params => params.value >= 0 ? CHART_COLORS.UP : CHART_COLORS.DOWN
            },
            label: {
                show: true,
                position: 'top',
                formatter: params => (params.value/10000).toFixed(1),
                fontSize: 10,
                color: params => params.value >= 0 ? CHART_COLORS.UP : CHART_COLORS.DOWN
            }
        }]
    };
    
    netInflowChart.setOption(option);
}

// 导出全局函数和变量
window.initializeCharts = initializeCharts;
window.updateTimelineChart = updateTimelineChart;
window.updateVolumeChart = updateVolumeChart;
window.updateStockDailyChart = updateStockDailyChart;
window.updateMoneyFlowChart = updateMoneyFlowChart;
window.updateNetInflowChart = updateNetInflowChart;
window.timelineChart = timelineChart;
window.volumeChart = volumeChart;
window.stockDailyChart = stockDailyChart;
window.moneyFlowChart = moneyFlowChart;
window.netInflowChart = netInflowChart;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，初始化图表');
    setTimeout(initializeCharts, 100);
});

// 监听标签页切换
document.addEventListener('shown.bs.tab', function() {
    console.log('标签页切换，重新初始化图表');
    setTimeout(initializeCharts, 100);
});

// 监听窗口大小变化
let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        console.log('窗口大小改变，重置图表大小');
        resizeAllCharts();
    }, 100);
});
  