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
        this.setupTooltips();
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

    setupTooltips() {
        // Tooltip content definitions
        const tooltipContent = {
            'ticker': '<strong>Ticker del bono</strong><br>Código identificatorio del bono o letra del Tesoro Nacional.',
            'precio': '<strong>Precio de mercado</strong><br>Precio actual del bono en pesos argentinos. Es el valor al cual se puede comprar hoy.',
            'fecha': '<strong>Fecha de vencimiento</strong><br>Fecha en la cual el bono paga su valor nominal (100 pesos por cada bono).',
            'dias': '<strong>Días al vencimiento</strong><br>Cantidad de días que faltan desde hoy hasta la fecha de vencimiento del bono.',
            'tem': '<strong>TEM - Tasa Efectiva Mensual</strong><br>Rendimiento mensual efectivo del bono en pesos. Indica cuánto rinde el bono cada mes.',
            'tna': '<strong>TNA - Tasa Nominal Anual</strong><br>Tasa anual nominal simple. Es la TEM × 12, sin capitalización.',
            'tea': '<strong>TEA - Tasa Efectiva Anual</strong><br>Rendimiento anual efectivo con capitalización. Refleja el rendimiento real anualizado del bono.',
            'carry1300': '<strong>Carry con MEP $1300</strong><br>Rendimiento en dólares si el MEP está a $1300 al vencimiento. Muestra "-" si este escenario excede el techo de la banda cambiaria.',
            'carry1400': '<strong>Carry con MEP $1400</strong><br>Rendimiento en dólares si el MEP está a $1400 al vencimiento. Muestra "-" si este escenario excede el techo de la banda cambiaria.',
            'carry1500': '<strong>Carry con MEP $1500</strong><br>Rendimiento en dólares si el MEP está a $1500 al vencimiento. Muestra "-" si este escenario excede el techo de la banda cambiaria.',
            'carry1600': '<strong>Carry con MEP $1600</strong><br>Rendimiento en dólares si el MEP está a $1600 al vencimiento. Muestra "-" si este escenario excede el techo de la banda cambiaria.',
            'carry1700': '<strong>Carry con MEP $1700</strong><br>Rendimiento en dólares si el MEP está a $1700 al vencimiento. Muestra "-" si este escenario excede el techo de la banda cambiaria.',
            'carry1800': '<strong>Carry con MEP $1800</strong><br>Rendimiento en dólares si el MEP está a $1800 al vencimiento. Muestra "-" si este escenario excede el techo de la banda cambiaria.',
            'carrytecho': '<strong>Carry al Techo de Banda</strong><br>Rendimiento en dólares en el escenario más conservador: MEP al techo de la banda cambiaria del BCRA al vencimiento. Este es el "peor caso" asumiendo que el MEP suba hasta el límite superior permitido.'
        };

        // Initialize tooltips for all table headers with data-tooltip attribute
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            const tooltipKey = element.getAttribute('data-tooltip');
            const content = tooltipContent[tooltipKey];

            if (content) {
                tippy(element, {
                    content: content,
                    allowHTML: true,
                    theme: 'light',
                    placement: 'top',
                    arrow: true,
                    interactive: true,
                    maxWidth: 350,
                    delay: [100, 0],
                    animation: 'fade',
                });
            }
        });
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
            // Load REM data after table/chart (uses same cached REM data from backend)
            await this.loadRemData();
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
            tableBody.innerHTML = '<tr><td colspan="14">No hay datos disponibles</td></tr>';
            return;
        }

        // Helper function to format percentage or show dash
        const formatPct = (value) => {
            // Check for null, undefined, NaN, or Infinity
            if (value === null || value === undefined || !isFinite(value)) {
                return '-';
            }
            return (value * 100).toFixed(1) + '%';
        };

        // Debug: log first row data to see what's available
        if (data.length > 0) {
            console.log('First row data keys:', Object.keys(data[0]));
            console.log('Carry 1400:', data[0].carry_1400);
            console.log('Carry techo:', data[0].carry_techo);
        }

        tableBody.innerHTML = data.map(row => {
            return `
                <tr class="fade-in">
                    <td style="font-weight: 600; color: #1e3c72;">${row.ticker}</td>
                    <td>$${row.precio.toFixed(2)}</td>
                    <td>${row.fecha_vencimiento}</td>
                    <td>${row.dias_vencimiento}</td>
                    <td>${formatPct(row.tem)}</td>
                    <td>${formatPct(row.tna)}</td>
                    <td>${formatPct(row.tea)}</td>
                    <td class="${this.getCarryClass(row.carry_1300, colorLimits)}">${formatPct(row.carry_1300)}</td>
                    <td class="${this.getCarryClass(row.carry_1400, colorLimits)}">${formatPct(row.carry_1400)}</td>
                    <td class="${this.getCarryClass(row.carry_1500, colorLimits)}">${formatPct(row.carry_1500)}</td>
                    <td class="${this.getCarryClass(row.carry_1600, colorLimits)}">${formatPct(row.carry_1600)}</td>
                    <td class="${this.getCarryClass(row.carry_1700, colorLimits)}">${formatPct(row.carry_1700)}</td>
                    <td class="${this.getCarryClass(row.carry_1800, colorLimits)}">${formatPct(row.carry_1800)}</td>
                    <td class="${this.getCarryClass(row.carry_techo, colorLimits)}">${formatPct(row.carry_techo)}</td>
                </tr>
            `;
        }).join('');
    }

    getCarryClass(value, colorLimits) {
        // If value is "-" (non-calculated scenario), return no class
        if (value === "-" || value === null || value === undefined || typeof value === 'string') {
            return '';
        }

        // Check for NaN or Infinity
        if (!isFinite(value)) {
            return '';
        }

        if (!colorLimits || colorLimits.limit === 0) return '';

        // Use actual value instead of normalized for more realistic coloring
        // Negative values < -11% are concerning, others are opportunities

        if (value > 0.02) {
            // Clearly positive (> 2%)
            const intensity = Math.min(1, value / 0.15); // Cap at 15% for max color
            return `carry-positive-${Math.floor(intensity * 5) + 1}`;
        } else if (value > -0.05) {
            // Slightly positive or slightly negative (-5% to 2%) - neutral/light
            return 'carry-neutral';
        } else if (value > -0.11) {
            // Moderate negative (-11% to -5%) - yellow/amber warning
            return 'carry-negative-1'; // Lightest negative shade
        } else {
            // Significant negative (< -11%) - red alert
            const intensity = Math.min(1, Math.abs(value + 0.11) / 0.15); // Start from -11%
            return `carry-negative-${Math.floor(intensity * 3) + 2}`; // Use shades 2-5
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

        // Parse expiration dates and create temporal data points
        const bondDataPoints = chartData.expiration_dates.map((dateStr, index) => ({
            x: new Date(dateStr),
            y: chartData.mep_breakeven[index],
            ticker: chartData.tickers[index],
            bandCeiling: chartData.band_ceiling[index],
            daysToExp: chartData.days_to_exp[index]
        }));

        // Use band projection from backend (monthly calculated values)
        const bandProjection = chartData.band_projection_dates.map((dateStr, index) => ({
            x: new Date(dateStr),
            y: chartData.band_projection_values[index]
        }));

        // Create dynamic point colors based on breakeven vs band ceiling
        const breakeven_colors = bondDataPoints.map(point => {
            const diff_pct = (point.y - point.bandCeiling) / point.bandCeiling;

            if (diff_pct > 0) {
                return '#4caf50'; // Verde - positivo (breakeven > techo)
            } else if (diff_pct > -0.11) {
                return '#ffa726'; // Amarillo/Naranja - negativo leve (0% a -11%)
            } else {
                return '#ef5350'; // Rojo - negativo fuerte (< -11% drawdown)
            }
        });

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Techo de Banda Cambiaria',
                        data: bandProjection,
                        borderColor: '#2196f3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        order: 2
                    },
                    {
                        label: 'MEP Breakeven por Bono',
                        data: bondDataPoints,
                        borderColor: '#ffffff',
                        backgroundColor: 'rgba(255, 255, 255, 0.8)',
                        borderWidth: 0,
                        pointRadius: 8,
                        pointHoverRadius: 10,
                        pointBackgroundColor: breakeven_colors,
                        pointBorderColor: '#1e3c72',
                        pointBorderWidth: 2,
                        showLine: false,
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'MEP Breakeven vs Techo de Banda Cambiaria (Escala Temporal)',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        color: '#1e3c72',
                        padding: {
                            bottom: 20
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            font: {
                                size: 12
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        padding: 12,
                        callbacks: {
                            title: function(context) {
                                const dataPoint = context[0].raw;
                                if (dataPoint.ticker) {
                                    const date = new Date(dataPoint.x);
                                    return `${dataPoint.ticker} - ${date.toLocaleDateString('es-AR')}`;
                                }
                                const date = new Date(context[0].parsed.x);
                                return `${date.toLocaleDateString('es-AR', { day: '2-digit', month: 'short', year: 'numeric' })}`;
                            },
                            label: function(context) {
                                const value = context.parsed.y;
                                const label = context.dataset.label;
                                const dataPoint = context.raw;

                                if (dataPoint.ticker) {
                                    // MEP Breakeven point
                                    const bandCeiling = dataPoint.bandCeiling;
                                    const diff = value - bandCeiling;
                                    const diff_pct = (diff / bandCeiling) * 100;
                                    const status = diff > 0 ? '🟢 Positivo' : '🔴 Negativo';

                                    return [
                                        `MEP Breakeven: $${value.toFixed(0)}`,
                                        `Techo Banda: $${bandCeiling.toFixed(0)}`,
                                        `Diferencia: $${diff.toFixed(0)} (${diff_pct.toFixed(1)}%)`,
                                        `Estado: ${status}`
                                    ];
                                }

                                // Band ceiling point - show date and value
                                return `Techo Banda: $${value.toFixed(2)}`;
                            },
                            footer: function(context) {
                                const dataPoint = context[0].raw;
                                if (!dataPoint.ticker) {
                                    // For band projection points, show calculation info
                                    return '(Calculado con inflación T-2)';
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: {
                                month: 'MMM yyyy'
                            },
                            tooltipFormat: 'dd/MM/yyyy'
                        },
                        title: {
                            display: true,
                            text: 'Fecha de Vencimiento',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        ticks: {
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
                    mode: 'nearest'
                }
            }
        });
    }

    async loadRemData() {
        try {
            const response = await fetch('/api/rem-data');
            const result = await response.json();

            if (!response.ok || result.status !== 'success') {
                this.showRemError('Error al obtener datos del REM');
                return;
            }

            this.renderRemTable(result);
        } catch (error) {
            console.error('Error loading REM data:', error);
            this.showRemError('No se pudieron cargar los datos del REM');
        }
    }

    showRemError(message) {
        const thead = document.getElementById('rem-table-head');
        const tbody = document.getElementById('rem-table-body');
        const infoEl = document.getElementById('rem-update-info');
        if (thead) thead.innerHTML = '<tr><th>Estado</th></tr>';
        if (tbody) tbody.innerHTML = `<tr><td>${message}</td></tr>`;
        if (infoEl) infoEl.textContent = message;
    }

    renderRemTable(remData) {
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

        // Build header and data rows
        const monthly = remData.monthly_projections || [];
        const annual = remData.annual_projections || [];

        if (monthly.length === 0 && annual.length === 0) {
            this.showRemError('Sin datos de proyecciones REM disponibles');
            return;
        }

        // Build columns: monthly + annual
        let headerCells = '<th>Indicador</th>';
        let dataCells = '<td><strong>Mediana (%)</strong></td>';

        monthly.forEach(m => {
            const parts = m.periodo.split('-');
            const monthName = months[parseInt(parts[1]) - 1];
            headerCells += `<th>${monthName} ${parts[0]}</th>`;
            dataCells += `<td>${m.mediana}%</td>`;
        });

        annual.forEach(a => {
            const label = a.periodo.length === 4 ? `Anual ${a.periodo}` : a.periodo;
            headerCells += `<th>${label}</th>`;
            dataCells += `<td><strong>${a.mediana}%</strong></td>`;
        });

        const thead = document.getElementById('rem-table-head');
        const tbody = document.getElementById('rem-table-body');
        if (thead) thead.innerHTML = `<tr>${headerCells}</tr>`;
        if (tbody) tbody.innerHTML = `<tr>${dataCells}</tr>`;

        // Update metadata info
        const infoEl = document.getElementById('rem-update-info');
        if (infoEl && remData.metadata) {
            const date = new Date(remData.metadata.ultima_actualizacion);
            const periodoRem = remData.metadata.periodo || '';
            const meses = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
            const parts = periodoRem.split('-');
            const mesNombre = parts.length === 2 ? meses[parseInt(parts[1]) - 1] : '';
            const anio = parts[0] || '';
            infoEl.innerHTML = `Fuente: <strong>REM BCRA</strong> — Último relevamiento: <strong>${mesNombre} ${anio}</strong> (actualizado ${date.toLocaleDateString('es-AR')}) — ${remData.monthly_projections?.[0]?.participantes || '~45'} participantes`;
        }
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
        const amountInput = document.getElementById('investment-amount');
        const ticker = document.getElementById('bond-selector').value;
        const amount = parseFloat(amountInput.value);

        // Validations
        if (!ticker) {
            this.showError('Por favor seleccione un bono', 'simulation');
            return;
        }

        if (!amount || isNaN(amount)) {
            this.showError('Por favor ingrese un monto válido', 'simulation');
            amountInput.focus();
            return;
        }

        if (amount < 1) {
            this.showError('El monto debe ser mayor a 1 USD', 'simulation');
            amountInput.focus();
            return;
        }

        if (amount > 1000000) {
            this.showError('El monto debe ser menor a 1,000,000 USD', 'simulation');
            amountInput.focus();
            return;
        }

        if (!this.carryData || !this.mepRate) {
            this.showError('Datos de mercado no disponibles. Por favor recargue la página.', 'simulation');
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
        const payoffTotal = bondsQuantity * 100; // Cada bono paga 100 al vencimiento (assuming normalized payoff)

        // Scenarios - CORRECTED to match table (1300, 1400, 1500, 1600, 1700, 1800, Techo)
        const scenarios = [
            { label: 'MEP 1300', mep: 1300, carry: bondData.carry_1300 },
            { label: 'MEP 1400', mep: 1400, carry: bondData.carry_1400 },
            { label: 'MEP 1500', mep: 1500, carry: bondData.carry_1500 },
            { label: 'MEP 1600', mep: 1600, carry: bondData.carry_1600 },
            { label: 'MEP 1700', mep: 1700, carry: bondData.carry_1700 },
            { label: 'MEP 1800', mep: 1800, carry: bondData.carry_1800 },
            { label: 'Techo Banda', mep: null, carry: bondData.carry_techo }
        ];

        // Filter out invalid scenarios (NaN or "-")
        const validScenarios = scenarios.filter(s => {
            if (typeof s.carry === 'string' && s.carry === '-') return false;
            if (typeof s.carry === 'number' && !isFinite(s.carry)) return false;
            return true;
        });

        // Check if there are no valid scenarios
        if (validScenarios.length === 0) {
            simulationBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 20px;">
                        <strong>No hay escenarios válidos para este bono.</strong><br>
                        Todos los escenarios exceden el techo de la banda cambiaria.
                    </td>
                </tr>
            `;
            resultsSection.classList.add('show');
            return;
        }

        // Build rows with comprehensive metrics
        const rows = [
            {
                metric: 'MEP al vencimiento',
                values: validScenarios.map(s => s.mep ? `$${s.mep}` : 'Techo'),
                cssClass: 'metric-scenario'
            },
            {
                metric: 'Rendimiento en USD (%)',
                values: validScenarios.map(s => {
                    const carry = typeof s.carry === 'string' ? 0 : s.carry;
                    return `${(carry * 100).toFixed(2)}%`;
                }),
                cssClass: 'metric-carry'
            },
            {
                metric: 'USD invertidos (hoy)',
                values: validScenarios.map(s => `$${amountUSD.toFixed(2)}`),
                cssClass: 'metric-base'
            },
            {
                metric: 'Pesos invertidos (hoy)',
                values: validScenarios.map(s => `$${pesosInvested.toFixed(2)}`),
                cssClass: 'metric-base'
            },
            {
                metric: 'Cantidad de bonos',
                values: validScenarios.map(s => bondsQuantity.toFixed(4)),
                cssClass: 'metric-base'
            },
            {
                metric: 'USD al vencimiento',
                values: validScenarios.map(s => {
                    const carry = typeof s.carry === 'string' ? 0 : s.carry;
                    return `$${(amountUSD * (1 + carry)).toFixed(2)}`;
                }),
                cssClass: 'metric-result'
            },
            {
                metric: 'Ganancia/Pérdida en USD',
                values: validScenarios.map(s => {
                    const carry = typeof s.carry === 'string' ? 0 : s.carry;
                    const gain = amountUSD * carry;
                    const sign = gain >= 0 ? '+' : '';
                    return `${sign}$${gain.toFixed(2)}`;
                }),
                cssClass: 'metric-gain'
            }
        ];

        // Update table header dynamically
        const tableHeader = document.querySelector('#simulation-table thead tr');
        if (tableHeader) {
            tableHeader.innerHTML = `
                <th>Métrica</th>
                ${validScenarios.map(s => `<th>${s.label}</th>`).join('')}
            `;
        }

        // Render table body
        simulationBody.innerHTML = rows.map(row => `
            <tr class="${row.cssClass || ''}">
                <td style="font-weight: 600;">${row.metric}</td>
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