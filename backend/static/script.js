// Gold Price Prediction Frontend
class GoldPriceApp {
    constructor() {
        this.livePrices = null;
        this.predictions = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadLivePrices();
        this.loadHistoricalPrices();
    }

    bindEvents() {
        const predictBtn = document.getElementById('predict-btn');
        const karatSelect = document.getElementById('karat-select');

        predictBtn.addEventListener('click', () => this.getPredictions());
        karatSelect.addEventListener('change', () => this.updateKaratDisplay());
    }

    async loadLivePrices() {
        try {
            this.showLoading('live-prices', 'Fetching live gold prices...');
            const response = await fetch('/api/live-price');
            const data = await response.json();

            if (data.success) {
                this.livePrices = data.data;
                this.displayLivePrices();
            } else {
                this.showError('live-prices', 'Failed to load live prices');
            }
        } catch (error) {
            console.error('Error loading live prices:', error);
            this.showError('live-prices', 'Network error loading prices');
        }
    }

    displayLivePrices() {
        const container = document.getElementById('live-prices');
        container.innerHTML = '';

        if (!this.livePrices) return;

        const baseData = this.livePrices.base_data;
        const allKarats = this.livePrices.all_karats;

        // Header info
        const header = document.createElement('div');
        header.className = 'source-info';
        const sourceText = baseData.source.includes('Sample') ? 
            `<strong>⚠️ Source:</strong> ${baseData.source} (Demo Data)` : 
            `<strong>📍 Source:</strong> ${baseData.source}`;
        header.innerHTML = `
            ${sourceText} |
            <strong>⏰ Updated:</strong> ${baseData.date}
        `;
        container.appendChild(header);

        // Price grid
        const priceGrid = document.createElement('div');
        priceGrid.className = 'price-grid';

        Object.entries(allKarats).forEach(([karat, data]) => {
            const priceItem = document.createElement('div');
            priceItem.className = 'price-item';
            priceItem.innerHTML = `
                <span class="price-label">${karat} (${data.purity})</span>
                <span class="price-value">₹${data.price_per_gram}/g</span>
            `;
            priceGrid.appendChild(priceItem);
        });

        container.appendChild(priceGrid);
    }

    async loadHistoricalPrices() {
        try {
            this.showLoading('historical-prices', 'Loading historical prices...');
            const response = await fetch('/api/historical-prices');
            const data = await response.json();

            if (data.success) {
                this.displayHistoricalPrices(data.data);
            } else {
                this.showError('historical-prices', 'Failed to load historical prices');
            }
        } catch (error) {
            console.error('Error loading historical prices:', error);
            this.showError('historical-prices', 'Network error loading historical data');
        }
    }

    displayHistoricalPrices(historicalData) {
        const container = document.getElementById('historical-prices');
        container.innerHTML = '';

        if (!historicalData || historicalData.length === 0) {
            container.innerHTML = '<div>No historical data available</div>';
            return;
        }

        const historicalGrid = document.createElement('div');
        historicalGrid.className = 'historical-grid';

        historicalData.forEach(item => {
            const historicalItem = document.createElement('div');
            historicalItem.className = 'historical-item';
            historicalItem.innerHTML = `
                <span class="historical-date">${item.date}</span>
                <span class="historical-price">₹${item.price_inr}/g</span>
            `;
            historicalGrid.appendChild(historicalItem);
        });

        container.appendChild(historicalGrid);
    }

    async getPredictions() {
        const karat = document.getElementById('karat-select').value;
        const predictBtn = document.getElementById('predict-btn');

        console.log('Starting prediction request for karat:', karat);

        try {
            predictBtn.disabled = true;
            predictBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Predicting...';

            this.showLoading('prediction-results', 'Generating predictions...');

            const response = await fetch(`/api/predict?karat=${karat}&live=true`);
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);

            if (data.success) {
                console.log('Prediction successful, displaying data');
                this.predictions = data.data;
                this.displayPredictions();
            } else {
                console.log('Prediction failed:', data.error);
                this.showError('prediction-results', data.error || 'Failed to generate predictions');
            }
        } catch (error) {
            console.error('Error getting predictions:', error);
            this.showError('prediction-results', 'Network error generating predictions');
        } finally {
            predictBtn.disabled = false;
            predictBtn.innerHTML = '<i class="fas fa-chart-line"></i> Get Predictions';
        }
    }

    displayPredictions() {
        const container = document.getElementById('prediction-results');
        container.innerHTML = '';
        container.classList.remove('hidden');

        if (!this.predictions) return;

        const header = document.createElement('h3');
        header.innerHTML = `<i class="fas fa-chart-line"></i> ${this.predictions.karat_type} Predictions`;
        container.appendChild(header);

        const todayDiv = document.createElement('div');
        todayDiv.className = 'prediction-item';
        todayDiv.innerHTML = `
            <span class="prediction-date">📅 TODAY</span>
            <span class="prediction-value">₹${this.predictions.today_price}/g</span>
        `;
        container.appendChild(todayDiv);

        const predictionList = document.createElement('div');
        predictionList.id = 'prediction-list';

        this.predictions.predictions.forEach((pred, index) => {
            const date = new Date();
            date.setDate(date.getDate() + index + 1);
            const dateStr = date.toLocaleDateString();

            const change = pred - this.predictions.today_price;
            const changePct = (change / this.predictions.today_price) * 100;
            const changeClass = change >= 0 ? 'change-positive' : 'change-negative';
            const arrow = change >= 0 ? '↑' : '↓';

            const item = document.createElement('div');
            item.className = 'prediction-item';
            item.innerHTML = `
                <span class="prediction-date">Day ${index + 1} (${dateStr})</span>
                <div style="text-align: right;">
                    <div class="prediction-value">₹${pred.toFixed(2)}/g</div>
                    <div class="prediction-change ${changeClass}">
                        ${arrow} ${changePct.toFixed(2)}%
                    </div>
                </div>
            `;
            predictionList.appendChild(item);
        });

        container.appendChild(predictionList);
    }

    updateKaratDisplay() {
        const karat = document.getElementById('karat-select').value;
        const display = document.getElementById('selected-karat');
        display.textContent = karat;
    }

    showLoading(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="loading">
                <div><i class="fas fa-spinner fa-spin"></i></div>
                <div>${message}</div>
            </div>
        `;
    }

    showError(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GoldPriceApp();
});
