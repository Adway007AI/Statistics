import React, { useState } from "react";
import "./App.css";
import axios from "axios";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [pricesInput, setPricesInput] = useState("");
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyzeStocks = async () => {
    if (!pricesInput.trim()) {
      setError("Please enter stock prices");
      return;
    }

    setLoading(true);
    setError("");
    
    try {
      const response = await axios.post(`${API}/analyze-stocks`, {
        prices_text: pricesInput
      });
      setStatistics(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setPricesInput("");
    setStatistics(null);
    setError("");
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return "N/A";
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatNumber = (value) => {
    if (value === null || value === undefined) return "N/A";
    return value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  // Chart data for histogram
  const getHistogramData = () => {
    if (!statistics) return null;
    
    const prices = statistics.raw_prices;
    const bins = 10;
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const binWidth = (max - min) / bins;
    
    const histogram = new Array(bins).fill(0);
    const labels = [];
    
    for (let i = 0; i < bins; i++) {
      const binStart = min + i * binWidth;
      const binEnd = min + (i + 1) * binWidth;
      labels.push(`₹${binStart.toFixed(0)}-${binEnd.toFixed(0)}`);
      
      prices.forEach(price => {
        if (price >= binStart && (price < binEnd || i === bins - 1)) {
          histogram[i]++;
        }
      });
    }

    return {
      labels,
      datasets: [
        {
          label: 'Frequency',
          data: histogram,
          backgroundColor: 'rgba(229, 9, 20, 0.7)',
          borderColor: 'rgba(229, 9, 20, 1)',
          borderWidth: 2,
        },
      ],
    };
  };

  // Chart data for price trend
  const getTrendData = () => {
    if (!statistics) return null;
    
    return {
      labels: statistics.raw_prices.map((_, index) => `Price ${index + 1}`),
      datasets: [
        {
          label: 'Stock Prices (₹)',
          data: statistics.raw_prices,
          borderColor: 'rgba(229, 9, 20, 1)',
          backgroundColor: 'rgba(229, 9, 20, 0.2)',
          tension: 0.4,
          pointBackgroundColor: 'rgba(229, 9, 20, 1)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        labels: {
          color: '#ffffff',
        },
      },
      title: {
        display: true,
        color: '#ffffff',
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#ffffff',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
      y: {
        ticks: {
          color: '#ffffff',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
    },
  };

  return (
    <div className="min-h-screen bg-netflix-black text-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-netflix-black to-gray-900 py-6 px-4 border-b border-netflix-red">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold text-netflix-red mb-2">
            📈 StockStats
          </h1>
          <p className="text-gray-300 text-lg">
            Advanced Stock Price Analytics • Indian Markets (₹)
          </p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        {/* Input Section */}
        <div className="bg-netflix-dark rounded-xl p-6 mb-8 border border-gray-800">
          <h2 className="text-2xl font-semibold mb-4 text-netflix-red">
            Enter Stock Prices
          </h2>
          <p className="text-gray-400 mb-4">
            Enter prices separated by commas, spaces, or line breaks (e.g., 421.5, 430.2, 419.8)
          </p>
          
          <textarea
            value={pricesInput}
            onChange={(e) => setPricesInput(e.target.value)}
            placeholder="421.5, 430.2, 419.8, 425.1, 433.5&#10;or&#10;421.5 430.2 419.8&#10;or one per line..."
            className="w-full h-32 bg-gray-800 border border-gray-700 rounded-lg p-4 text-white placeholder-gray-500 focus:border-netflix-red focus:outline-none resize-none"
          />
          
          {error && (
            <div className="mt-3 text-netflix-red bg-red-900/20 border border-red-800 rounded-lg p-3">
              {error}
            </div>
          )}
          
          <div className="flex gap-4 mt-4">
            <button
              onClick={analyzeStocks}
              disabled={loading}
              className="bg-netflix-red hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-8 rounded-lg transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Analyzing...
                </>
              ) : (
                "📊 Analyze Stocks"
              )}
            </button>
            
            <button
              onClick={clearAll}
              className="bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 px-8 rounded-lg transition-colors"
            >
              🗑️ Clear All
            </button>
          </div>
        </div>

        {/* Results Section */}
        {statistics && (
          <div className="space-y-6">
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-netflix-dark rounded-xl p-6 border-l-4 border-netflix-red">
                <h3 className="text-sm font-medium text-gray-400 mb-1">Total Prices</h3>
                <p className="text-3xl font-bold text-white">{statistics.price_count}</p>
              </div>
              
              <div className="bg-netflix-dark rounded-xl p-6 border-l-4 border-green-500">
                <h3 className="text-sm font-medium text-gray-400 mb-1">Average Price</h3>
                <p className="text-3xl font-bold text-white">{formatCurrency(statistics.basic_stats.mean)}</p>
              </div>
              
              <div className="bg-netflix-dark rounded-xl p-6 border-l-4 border-blue-500">
                <h3 className="text-sm font-medium text-gray-400 mb-1">Price Range</h3>
                <p className="text-3xl font-bold text-white">{formatCurrency(statistics.basic_stats.range)}</p>
              </div>
              
              <div className="bg-netflix-dark rounded-xl p-6 border-l-4 border-yellow-500">
                <h3 className="text-sm font-medium text-gray-400 mb-1">Volatility (σ)</h3>
                <p className="text-3xl font-bold text-white">{formatNumber(statistics.basic_stats.std_deviation)}</p>
              </div>
            </div>

            {/* Basic Statistics */}
            <div className="bg-netflix-dark rounded-xl p-6 border border-gray-800">
              <h3 className="text-2xl font-semibold mb-4 text-netflix-red">📊 Basic Statistics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div>
                  <p className="text-gray-400 text-sm">Mean</p>
                  <p className="text-xl font-semibold">{formatCurrency(statistics.basic_stats.mean)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Median</p>
                  <p className="text-xl font-semibold">{formatCurrency(statistics.basic_stats.median)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Mode</p>
                  <p className="text-xl font-semibold">{formatCurrency(statistics.basic_stats.mode)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Standard Deviation</p>
                  <p className="text-xl font-semibold">{formatNumber(statistics.basic_stats.std_deviation)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Minimum</p>
                  <p className="text-xl font-semibold">{formatCurrency(statistics.basic_stats.minimum)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Maximum</p>
                  <p className="text-xl font-semibold">{formatCurrency(statistics.basic_stats.maximum)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Range</p>
                  <p className="text-xl font-semibold">{formatCurrency(statistics.basic_stats.range)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Variance</p>
                  <p className="text-xl font-semibold">{formatNumber(statistics.basic_stats.variance)}</p>
                </div>
              </div>
            </div>

            {/* Advanced Statistics */}
            <div className="bg-netflix-dark rounded-xl p-6 border border-gray-800">
              <h3 className="text-2xl font-semibold mb-4 text-netflix-red">📈 Advanced Statistics</h3>
              
              {/* Quartiles */}
              <div className="mb-6">
                <h4 className="text-lg font-medium mb-3 text-gray-300">Quartiles</h4>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-gray-400 text-sm">Q1 (25%)</p>
                    <p className="text-lg font-semibold">{formatCurrency(statistics.advanced_stats.quartiles.q1)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Q2 (50%)</p>
                    <p className="text-lg font-semibold">{formatCurrency(statistics.advanced_stats.quartiles.q2)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Q3 (75%)</p>
                    <p className="text-lg font-semibold">{formatCurrency(statistics.advanced_stats.quartiles.q3)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">IQR</p>
                    <p className="text-lg font-semibold">{formatCurrency(statistics.advanced_stats.iqr)}</p>
                  </div>
                </div>
              </div>

              {/* Distribution Metrics */}
              <div className="mb-6">
                <h4 className="text-lg font-medium mb-3 text-gray-300">Distribution Analysis</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <p className="text-gray-400 text-sm">Skewness</p>
                    <p className="text-lg font-semibold">{formatNumber(statistics.advanced_stats.skewness)}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {statistics.advanced_stats.skewness > 0 ? "Right-skewed (positive)" : 
                       statistics.advanced_stats.skewness < 0 ? "Left-skewed (negative)" : "Symmetric"}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Kurtosis</p>
                    <p className="text-lg font-semibold">{formatNumber(statistics.advanced_stats.kurtosis)}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {statistics.advanced_stats.kurtosis > 0 ? "Heavy-tailed" : 
                       statistics.advanced_stats.kurtosis < 0 ? "Light-tailed" : "Normal-tailed"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Outliers */}
              <div>
                <h4 className="text-lg font-medium mb-3 text-gray-300">Outlier Analysis</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <p className="text-gray-400 text-sm">Outlier Count</p>
                    <p className="text-lg font-semibold">{statistics.advanced_stats.outliers.outlier_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Outlier Values</p>
                    <p className="text-sm">
                      {statistics.advanced_stats.outliers.outlier_values.length > 0 
                        ? statistics.advanced_stats.outliers.outlier_values.map(val => formatCurrency(val)).join(', ')
                        : 'No outliers detected'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Histogram */}
              <div className="bg-netflix-dark rounded-xl p-6 border border-gray-800">
                <h3 className="text-xl font-semibold mb-4 text-netflix-red">📊 Price Distribution</h3>
                <div className="h-64">
                  <Bar data={getHistogramData()} options={{...chartOptions, plugins: {...chartOptions.plugins, title: {display: false}}}} />
                </div>
              </div>

              {/* Trend Line */}
              <div className="bg-netflix-dark rounded-xl p-6 border border-gray-800">
                <h3 className="text-xl font-semibold mb-4 text-netflix-red">📈 Price Trend</h3>
                <div className="h-64">
                  <Line data={getTrendData()} options={{...chartOptions, plugins: {...chartOptions.plugins, title: {display: false}}}} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;