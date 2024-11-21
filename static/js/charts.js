// 全局图表实例
let timelineChart = null;
let volumeChart = null;
let stockDailyChart = null;
let moneyFlowChart = null;

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
    bottom: 60,
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

// 初始化图表
function initializeCharts() {
    console.log('初始化图表...');
    
    // 清除旧的图表实例
    [timelineChart, volumeChart, stockDailyChart, moneyFlowChart].forEach(chart => {
        if (chart) {
            chart.dispose();
        }
    });

    // 获取容器宽度和高度
    const chartsContainer = document.querySelector('.charts-container');
    if (!chartsContainer) return;

    const containerWidth = chartsContainer.clientWidth;
    const containerHeight = chartsContainer.clientHeight;

    // 计算各图表的高度
    const timelineHeight = Math.floor(containerHeight * 0.4);
    const volumeHeight = Math.floor(containerHeight * 0.2);
    const stockChartHeight = Math.floor(containerHeight * 0.3);

    // 初始化时间轴图表
    const timelineElement = document.getElementById('timeline-chart');
    if (timelineElement) {
        timelineElement.style.width = containerWidth + 'px';
        timelineElement.style.height = timelineHeight + 'px';
        timelineChart = echarts.init(timelineElement);
    }

    // 初始化成交量图表
    const volumeElement = document.getElementById('volume-chart');
    if (volumeElement) {
        volumeElement.style.width = containerWidth + 'px';
        volumeElement.style.height = volumeHeight + 'px';
        volumeChart = echarts.init(volumeElement);
    }

    // 初始化个股日线图表
    const stockDailyElement = document.getElementById('stock-daily-chart');
    if (stockDailyElement) {
        stockDailyElement.style.width = (containerWidth / 2 - 5) + 'px';
        stockDailyElement.style.height = stockChartHeight + 'px';
        stockDailyChart = echarts.init(stockDailyElement);
    }

    // 初始化资金流向图表
    const moneyFlowElement = document.getElementById('money-flow-chart');
    if (moneyFlowElement) {
        moneyFlowElement.style.width = (containerWidth / 2 - 5) + 'px';
        moneyFlowElement.style.height = stockChartHeight + 'px';
        moneyFlowChart = echarts.init(moneyFlowElement);
    }

    // 调整所有图表大小
    resizeAllCharts();
}

// 调整图表大小
function resizeAllCharts() {
    const chartsContainer = document.querySelector('.charts-container');
    if (!chartsContainer) return;

    const containerWidth = chartsContainer.clientWidth;
    const containerHeight = chartsContainer.clientHeight;

    // 计算各图表的高度
    const timelineHeight = Math.floor(containerHeight * 0.4);
    const volumeHeight = Math.floor(containerHeight * 0.2);
    const stockChartHeight = Math.floor(containerHeight * 0.3);

    const charts = [
        { chart: timelineChart, element: 'timeline-chart', width: containerWidth, height: timelineHeight },
        { chart: volumeChart, element: 'volume-chart', width: containerWidth, height: volumeHeight },
        { chart: stockDailyChart, element: 'stock-daily-chart', width: containerWidth / 2 - 5, height: stockChartHeight },
        { chart: moneyFlowChart, element: 'money-flow-chart', width: containerWidth / 2 - 5, height: stockChartHeight }
    ];

    charts.forEach(({ chart, element, width, height }) => {
        if (chart) {
            const container = document.getElementById(element);
            if (container) {
                container.style.width = width + 'px';
                container.style.height = height + 'px';
                chart.resize();
            }
        }
    });
}

// 更新个股日线图表
function updateStockDailyChart(data) {
    console.log('更新个股日线图表数据:', data);

    // 确保图表已初始化
    if (!stockDailyChart) {
        const stockDailyElement = document.getElementById('stock-daily-chart');
        if (stockDailyElement) {
            const chartsContainer = document.querySelector('.charts-container');
            const containerWidth = chartsContainer ? chartsContainer.clientWidth : 800;
            stockDailyElement.style.width = (containerWidth / 2 - 5) + 'px';
            stockDailyElement.style.height = '30vh';
            stockDailyChart = echarts.init(stockDailyElement);
            console.log('个股日线图表初始化完成');
        } else {
            console.warn('未找到个股日线图表容器');
            return;
        }
    }

    if (!data) {
        console.warn('无效的数据');
        return;
    }

    const option = {
        ...CHART_CONFIG,
        title: {
            ...CHART_CONFIG.title,
            text: `${data.name}走势`
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['涨跌幅', '成交额'],
            top: 30,
            right: 10,
            textStyle: {
                fontSize: 12
            }
        },
        grid: {
            top: 70,
            right: '8%',
            bottom: 30,
            left: '8%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.dates || [],
            boundaryGap: false,
            axisLabel: {
                fontSize: 10,
                rotate: 30,
                formatter: value => value.substring(5)
            }
        },
        yAxis: [{
            type: 'value',
            name: '涨跌幅(%)',
            position: 'left',
            nameTextStyle: {
                fontSize: 10,
                padding: [0, 0, 0, 0]
            },
            axisLabel: {
                fontSize: 10,
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
            nameTextStyle: {
                fontSize: 10,
                padding: [0, 0, 0, 0]
            },
            axisLabel: {
                fontSize: 10,
                formatter: value => (value/100000000).toFixed(1)
            },
            splitLine: {
                show: false
            }
        }],
        series: [{
            name: '涨跌幅',
            type: 'line',
            data: data.changes || [],
            itemStyle: {
                color: CHART_COLORS.UP
            },
            lineStyle: {
                width: 1
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
            }
        }, {
            name: '成交额',
            type: 'bar',
            yAxisIndex: 1,
            data: data.volumes || [],
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
            ...CHART_CONFIG,
            timeline: {
                axisType: 'category',
                autoPlay: false,
                playInterval: 3000,
                data: dates.map(date => date.substring(5)),
                label: {
                    ...AXIS_LABEL_STYLE,
                    formatter: value => value
                },
                top: 'bottom',
                height: 40,
                emphasis: {
                    itemStyle: {
                        color: CHART_COLORS.VOLUME.MIDDLE
                    }
                },
                controlStyle: {
                    showNextBtn: true,
                    showPrevBtn: true,
                    normal: {
                        color: CHART_COLORS.VOLUME.MIDDLE,
                        borderColor: CHART_COLORS.VOLUME.MIDDLE
                    }
                }
            },
            title: {
                text: '板块累计涨幅',
                ...CHART_TITLE_STYLE,
                subtext: '(相对9月20日)',
                subtextStyle: {
                    fontSize: 12,
                    color: '#666'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            grid: CHART_GRID,
            xAxis: {
                type: 'category',
                axisLabel: {
                    ...AXIS_LABEL_STYLE,
                    rotate: 30
                }
            },
            yAxis: {
                type: 'value',
                name: '累计涨幅',
                nameTextStyle: { 
                    ...AXIS_LABEL_STYLE,
                    padding: [0, 30, 0, 0]
                },
                axisLabel: {
                    ...AXIS_LABEL_STYLE,
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
    if (!moneyFlowChart) {
        console.warn('资金流向图表未初始化');
        return;
    }

    console.log('更新资金流向图表数据:', data);

    const option = {
        ...CHART_CONFIG,
        title: {
            ...CHART_CONFIG.title,
            text: '资金流向'
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['超大单流入', '超大单流出', '大单流入', '大单流出'],
            top: 30,
            right: 10,
            textStyle: {
                fontSize: 12
            }
        },
        grid: {
            top: 70,
            right: '3%',
            bottom: 30,
            left: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.dates || [],
            boundaryGap: false,
            axisLabel: {
                fontSize: 10,
                rotate: 30,
                formatter: value => value.substring(5)
            }
        },
        yAxis: {
            type: 'value',
            name: '金额(万元)',
            nameTextStyle: {
                fontSize: 10,
                padding: [0, 30, 0, 0]
            },
            axisLabel: {
                fontSize: 10,
                formatter: value => (value / 10000).toFixed(1)
            },
            splitLine: {
                show: true,
                lineStyle: {
                    type: 'dashed',
                    color: '#eee'
                }
            }
        },
        series: [
            {
                name: '超大单流入',
                type: 'line',
                data: data.super_large_inflow || [],
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: '#ff4d4f' },
                itemStyle: { color: '#ff4d4f' }
            },
            {
                name: '超大单流出',
                type: 'line',
                data: (data.super_large_outflow || []).map(v => -v),
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: '#ff7875' },
                itemStyle: { color: '#ff7875' }
            },
            {
                name: '大单流入',
                type: 'line',
                data: data.large_inflow || [],
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: '#52c41a' },
                itemStyle: { color: '#52c41a' }
            },
            {
                name: '大单流出',
                type: 'line',
                data: (data.large_outflow || []).map(v => -v),
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2, color: '#73d13d' },
                itemStyle: { color: '#73d13d' }
            }
        ]
    };
    
    moneyFlowChart.setOption(option);
}

// 导出全局函数和变量
window.initializeCharts = initializeCharts;
window.updateTimelineChart = updateTimelineChart;
window.updateVolumeChart = updateVolumeChart;
window.updateStockDailyChart = updateStockDailyChart;
window.updateMoneyFlowChart = updateMoneyFlowChart;
window.timelineChart = timelineChart;
window.volumeChart = volumeChart;
window.stockDailyChart = stockDailyChart;
window.moneyFlowChart = moneyFlowChart;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，初始化图表');
    setTimeout(() => {
        initializeCharts();
    }, 100);
});

// 监听标签页切换
document.addEventListener('shown.bs.tab', function() {
    console.log('标签页切换，重新初始化图表');
    setTimeout(() => {
        initializeCharts();
    }, 100);
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
  