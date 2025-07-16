// Analizador de Carry Trade - Bonos Argentinos - Frontend JavaScript

class CarryTradeApp {
    constructor() {
        this.chart = null;
        this.lastUpdateTime = null;
        this.isLoading = false;
        this.carryData = null;
        this.mepRate = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadData();
        // Auto-refresh every 5 minutes
        setInterval(() => this.loadData(), 300000);
    }

    setupEventListeners() {
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn.addEventListener('click', () => this.loadData());
        
        const simulateBtn = document.getElementById('simulate-btn');
        simulateBtn.addEventListener('click', () => this.runSimulation());
        
        const bondSelector = document.getElementById('bond-selector');
        bondSelector.addEventListener('change', () => this.updateSimulateButton());
        
        const investmentAmount = document.getElementById('investment-amount');
        investmentAmount.addEventListener('input', () => this.updateSimulateButton());
    }

    updateSimulateButton() {
        const amount = document.getElementById('investment-amount').value;
        const bond = document.getElementById('bond-selector').value;
        const btn = document.getElementById('simulate-btn');
        
        btn.disabled = !amount || !bond || amount <= 0;
    }

    async loadData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        this.hideErrors();
        
        try {
            await Promise.all([
                this.loadTableData(),
                this.loadChartData()
            ]);
            this.updateLastUpdateTime();
            this.populateBondSelector();
            // Ensure MEP value is updated even on refresh
            this.updateMepValue(this.mepRate);
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Error al cargar los datos. Verificando conexión con el servidor...', 'table');
            this.showError('Error al generar visualización. Verificando fuente de datos...', 'chart');
            // Update MEP value to show placeholder on error
            this.updateMepValue(null);
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    async loadTableData() {
        try {
            const response = await fetch('/api/carry-data');
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || 'Error fetching data');
            }
            
            this.carryData = result.data;
            this.mepRate = result.mep_rate || null;
            this.renderTable(result.data, result.color_limits);
            this.updateMepValue(this.mepRate);
        } catch (error) {
            console.error('Error loading table data:', error);
            throw error;
        }
    }

    updateMepValue(mepRate) {
        const mepElement = document.getElementById('mep-value');
        if (mepElement && mepRate) {
            mepElement.textContent = mepRate.toFixed(0);
        } else if (mepElement) {
            // Show placeholder if MEP rate is not available
            mepElement.textContent = '--';
        }
    }

    populateBondSelector() {
        const selector = document.getElementById('bond-selector');
        const defaultOption = selector.querySelector('option[value=""]');
        
        // Clear existing options except default
        selector.innerHTML = '';
        selector.appendChild(defaultOption);
        
        if (this.carryData && this.carryData.length > 0) {
            this.carryData.forEach(bond => {
                const option = document.createElement('option');
                option.value = bond.ticker;
                option.textContent = `${bond.ticker} - Vence: ${bond.fecha_vencimiento}`;
                selector.appendChild(option);
            });
        }
        
        this.updateSimulateButton();
    }

    async loadChartData() {
        try {
            const response = await fetch('/api/chart-data');
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || 'Error fetching chart data');
            }
            
            this.renderChart(result.chart_data);
        } catch (error) {
            console.error('Error loading chart data:', error);
            throw error;
        }
    }

    renderTable(data, colorLimits) {
        const tableBody = document.getElementById('table-body');
        
        if (!data || data.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="13">No hay datos disponibles</td></tr>';
            return;
        }

        tableBody.innerHTML = data.map(row => {
            return `
                <tr class="fade-in">
                    <td style="font-weight: 600; color: #1e3c72;">${row.ticker}</td>
                    <td>$${row.precio.toFixed(2)}</td>
                    <td>${row.fecha_vencimiento}</td>
                    <td>${row.dias_vencimiento}</td>
                    <td>${(row.tem * 100).toFixed(2)}%</td>
                    <td>${(row.tna * 100).toFixed(2)}%</td>
                    <td>${(row.tea * 100).toFixed(2)}%</td>
                    <td class="${this.getCarryClass(row.carry_1000, colorLimits)}">${(row.carry_1000 * 100).toFixed(1)}%</td>
                    <td class="${this.getCarryClass(row.carry_1100, colorLimits)}">${(row.carry_1100 * 100).toFixed(1)}%</td>
                    <td class="${this.getCarryClass(row.carry_1200, colorLimits)}">${(row.carry_1200 * 100).toFixed(1)}%</td>
                    <td class="${this.getCarryClass(row.carry_1300, colorLimits)}">${(row.carry_1300 * 100).toFixed(1)}%</td>
                    <td class="${this.getCarryClass(row.carry_1400, colorLimits)}">${(row.carry_1400 * 100).toFixed(1)}%</td>
                    <td class="${this.getCarryClass(row.carry_techo, colorLimits)}">${(row.carry_techo * 100).toFixed(1)}%</td>
                </tr>
            `;
        }).join('');
    }

    getCarryClass(value, colorLimits) {
        if (!colorLimits || colorLimits.limit === 0) return '';
        
        const limit = colorLimits.limit;
        
        // Normalize value to -1 to 1 range based on limits
        const normalized = Math.max(-1, Math.min(1, value / limit));
        
        if (normalized > 0.1) {
            // Green gradient for positive values
            const intensity = Math.min(1, normalized / 0.7);
            return `carry-positive-${Math.floor(intensity * 5) + 1}`;
        } else if (normalized < -0.1) {
            // Red gradient for negative values
            const intensity = Math.min(1, Math.abs(normalized) / 0.7);
            return `carry-negative-${Math.floor(intensity * 5) + 1}`;
        } else {
            // White/neutral for values close to zero
            return 'carry-neutral';
        }
    }

    renderChart(chartData) {
        if (!chartData || !chartData.tickers || chartData.tickers.length === 0) {
            console.log('No chart data available');
            return;
        }

        const ctx = document.getElementById('breakeven-chart');
        
        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
        }

        // Create x-axis labels (indices)
        const xLabels = chartData.tickers.map((_, index) => index);

        // Create dynamic point colors based on breakeven vs band ceiling
        const breakeven_colors = chartData.mep_breakeven.map((breakeven, index) => {
            const bandCeiling = chartData.band_ceiling[index];
            return breakeven > bandCeiling ? '#4caf50' : '#f44336'; // Green if above, red if below
        });

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: xLabels,
                datasets: [
                    {
                        label: 'Banda Superior',
                        data: chartData.band_ceiling,
                        borderColor: '#2196f3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1
                    },
                    {
                        label: 'MEP Breakeven',
                        data: chartData.mep_breakeven,
                        borderColor: '#ffffff',
                        backgroundColor: 'rgba(255, 255, 255, 0.8)',
                        borderWidth: 0,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        pointBackgroundColor: breakeven_colors,
                        pointBorderColor: '#1e3c72',
                        pointBorderWidth: 2,
                        showLine: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'MEP Breakeven vs Techo de la Banda',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        color: '#1e3c72'
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            title: function(context) {
                                const index = context[0].dataIndex;
                                return chartData.tickers[index];
                            },
                            label: function(context) {
                                const value = context.parsed.y;
                                const label = context.dataset.label;
                                const index = context.dataIndex;
                                
                                if (label === 'MEP Breakeven') {
                                    const bandCeiling = chartData.band_ceiling[index];
                                    const status = value > bandCeiling ? '🟢' : '🔴';
                                    return `${label}: $${value.toFixed(0)} ${status}`;
                                }
                                return `${label}: $${value.toFixed(0)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Bonos ordenados por vencimiento',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            callback: function(value, index) {
                                return chartData.tickers[index] || '';
                            },
                            maxRotation: 45,
                            minRotation: 45,
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Valor en ARS',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    showLoading() {
        const tableLoading = document.getElementById('table-loading');
        const chartLoading = document.getElementById('chart-loading');
        const table = document.getElementById('carry-table');
        const chart = document.getElementById('breakeven-chart');
        
        tableLoading.classList.remove('hidden');
        chartLoading.classList.remove('hidden');
        table.style.opacity = '0.5';
        chart.style.opacity = '0.5';
    }

    hideLoading() {
        const tableLoading = document.getElementById('table-loading');
        const chartLoading = document.getElementById('chart-loading');
        const table = document.getElementById('carry-table');
        const chart = document.getElementById('breakeven-chart');
        
        tableLoading.classList.add('hidden');
        chartLoading.classList.add('hidden');
        table.style.opacity = '1';
        chart.style.opacity = '1';
    }

    updateLastUpdateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-AR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const lastUpdateElement = document.getElementById('last-update');
        lastUpdateElement.textContent = `Última actualización: ${timeString}`;
        this.lastUpdateTime = now;
    }

    runSimulation() {
        const amount = parseFloat(document.getElementById('investment-amount').value);
        const ticker = document.getElementById('bond-selector').value;
        
        if (!amount || !ticker || !this.carryData || !this.mepRate) {
            this.showError('Faltan datos para realizar la simulación', 'simulation');
            return;
        }
        
        const bondData = this.carryData.find(bond => bond.ticker === ticker);
        if (!bondData) {
            this.showError('Bono seleccionado no encontrado', 'simulation');
            return;
        }
        
        this.renderSimulationResults(amount, bondData);
    }

    renderSimulationResults(amountUSD, bondData) {
        const resultsSection = document.getElementById('simulator-results');
        const simulationBody = document.getElementById('simulation-body');
        
        // Calculate base values
        const pesosInvested = amountUSD * this.mepRate;
        const bondsQuantity = pesosInvested / bondData.precio;
        
        // Scenarios
        const scenarios = [
            { label: 'USD 1000', carry: bondData.carry_1000 },
            { label: 'USD 1100', carry: bondData.carry_1100 },
            { label: 'USD 1200', carry: bondData.carry_1200 },
            { label: 'USD 1300', carry: bondData.carry_1300 },
            { label: 'USD 1400', carry: bondData.carry_1400 },
            { label: 'Techo Banda', carry: bondData.carry_techo }
        ];
        
        const rows = [
            {
                metric: 'Rendimiento directo en dólares',
                values: scenarios.map(s => `${(s.carry * 100).toFixed(1)}%`)
            },
            {
                metric: 'Dólares obtenidos (payoff)',
                values: scenarios.map(s => `$${(amountUSD * (1 + s.carry)).toFixed(0)}`)
            }
        ];
        
        simulationBody.innerHTML = rows.map(row => `
            <tr>
                <td>${row.metric}</td>
                ${row.values.map(value => `<td>${value}</td>`).join('')}
            </tr>
        `).join('');
        
        resultsSection.classList.add('show');
    }

    showError(message, section = 'general') {
        if (section === 'table') {
            const errorElement = document.getElementById('table-error');
            errorElement.querySelector('p').textContent = message;
            errorElement.style.display = 'block';
        } else if (section === 'chart') {
            const errorElement = document.getElementById('chart-error');
            errorElement.querySelector('p').textContent = message;
            errorElement.style.display = 'block';
        } else {
            // General error notification
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #e74c3c;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                max-width: 300px;
            `;
            errorDiv.textContent = message;
            
            document.body.appendChild(errorDiv);
            
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        }
    }

    hideErrors() {
        const tableError = document.getElementById('table-error');
        const chartError = document.getElementById('chart-error');
        
        if (tableError) tableError.style.display = 'none';
        if (chartError) chartError.style.display = 'none';
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CarryTradeApp();
});