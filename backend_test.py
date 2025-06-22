#!/usr/bin/env python3
import requests
import json
import numpy as np
import pandas as pd
from scipy import stats
import unittest
import sys
import os
from dotenv import load_dotenv

# Load environment variables from frontend/.env to get the backend URL
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
API_URL = f"{BACKEND_URL}/api"

class StockStatisticsAPITest(unittest.TestCase):
    
    def setUp(self):
        """Set up test case"""
        self.api_url = API_URL
        self.analyze_url = f"{self.api_url}/analyze-stocks"
        
        # Sample test data
        self.comma_separated = "421.5, 430.2, 419.8, 425.1, 433.5"
        self.space_separated = "421.5 430.2 419.8 425.1 433.5"
        self.newline_separated = "421.5\n430.2\n419.8\n425.1\n433.5"
        self.mixed_format = "421.5, 430.2 419.8\n425.1, 433.5"
        self.single_price = "421.5"
        self.empty_input = ""
        self.negative_prices = "421.5, -430.2, 419.8"
        self.invalid_format = "421.5, abc, 419.8"
        self.with_currency = "₹421.5, ₹430.2, ₹419.8"
        
        # Expected values for the comma_separated test case
        self.expected_prices = [421.5, 430.2, 419.8, 425.1, 433.5]
        
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        response = requests.get(self.api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("Stock Statistics API", data["message"])
        
    def test_analyze_comma_separated(self):
        """Test analyzing comma-separated prices"""
        payload = {"prices_text": self.comma_separated}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify structure
        self.assertIn("basic_stats", data)
        self.assertIn("advanced_stats", data)
        self.assertIn("raw_prices", data)
        self.assertIn("price_count", data)
        
        # Verify parsed prices
        self.assertEqual(data["price_count"], len(self.expected_prices))
        self.assertEqual(data["raw_prices"], self.expected_prices)
        
        # Verify basic stats
        self.verify_basic_stats(data["basic_stats"], self.expected_prices)
        
        # Verify advanced stats
        self.verify_advanced_stats(data["advanced_stats"], self.expected_prices)
        
    def test_analyze_space_separated(self):
        """Test analyzing space-separated prices"""
        payload = {"prices_text": self.space_separated}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify parsed prices
        self.assertEqual(data["price_count"], len(self.expected_prices))
        self.assertEqual(data["raw_prices"], self.expected_prices)
        
    def test_analyze_newline_separated(self):
        """Test analyzing newline-separated prices"""
        payload = {"prices_text": self.newline_separated}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify parsed prices
        self.assertEqual(data["price_count"], len(self.expected_prices))
        self.assertEqual(data["raw_prices"], self.expected_prices)
        
    def test_analyze_mixed_format(self):
        """Test analyzing mixed format prices"""
        payload = {"prices_text": self.mixed_format}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify we have the correct number of prices
        self.assertEqual(data["price_count"], 5)
        
    def test_analyze_with_currency(self):
        """Test analyzing prices with currency symbols"""
        payload = {"prices_text": self.with_currency}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify parsed prices
        expected = [421.5, 430.2, 419.8]
        self.assertEqual(data["price_count"], len(expected))
        self.assertEqual(data["raw_prices"], expected)
        
    def test_empty_input(self):
        """Test error handling for empty input"""
        payload = {"prices_text": self.empty_input}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("No input provided", data["detail"])
        
    def test_single_price(self):
        """Test error handling for single price"""
        payload = {"prices_text": self.single_price}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("At least 2 prices are required", data["detail"])
        
    def test_negative_prices(self):
        """Test error handling for negative prices"""
        payload = {"prices_text": self.negative_prices}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Negative price not allowed", data["detail"])
        
    def test_invalid_format(self):
        """Test error handling for invalid format"""
        payload = {"prices_text": self.invalid_format}
        response = requests.post(self.analyze_url, json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Invalid number format", data["detail"])
        
    def verify_basic_stats(self, basic_stats, prices):
        """Verify basic statistical calculations"""
        prices_array = np.array(prices)
        
        # Verify each statistic
        self.assertAlmostEqual(basic_stats["mean"], float(np.mean(prices_array)), places=5)
        self.assertAlmostEqual(basic_stats["median"], float(np.median(prices_array)), places=5)
        self.assertAlmostEqual(basic_stats["minimum"], float(np.min(prices_array)), places=5)
        self.assertAlmostEqual(basic_stats["maximum"], float(np.max(prices_array)), places=5)
        self.assertAlmostEqual(basic_stats["range"], float(np.max(prices_array) - np.min(prices_array)), places=5)
        self.assertAlmostEqual(basic_stats["std_deviation"], float(np.std(prices_array, ddof=1)), places=5)
        self.assertAlmostEqual(basic_stats["variance"], float(np.var(prices_array, ddof=1)), places=5)
        
        # Mode is None if all values are unique, otherwise it's the most common value
        if len(set(prices)) < len(prices):
            self.assertAlmostEqual(basic_stats["mode"], float(stats.mode(prices_array, keepdims=True).mode[0]), places=5)
        else:
            self.assertIsNone(basic_stats["mode"])
        
    def verify_advanced_stats(self, advanced_stats, prices):
        """Verify advanced statistical calculations"""
        prices_array = np.array(prices)
        
        # Verify quartiles
        self.assertAlmostEqual(advanced_stats["quartiles"]["q1"], float(np.percentile(prices_array, 25)), places=5)
        self.assertAlmostEqual(advanced_stats["quartiles"]["q2"], float(np.percentile(prices_array, 50)), places=5)
        self.assertAlmostEqual(advanced_stats["quartiles"]["q3"], float(np.percentile(prices_array, 75)), places=5)
        
        # Verify IQR
        q1 = float(np.percentile(prices_array, 25))
        q3 = float(np.percentile(prices_array, 75))
        self.assertAlmostEqual(advanced_stats["iqr"], float(q3 - q1), places=5)
        
        # Verify skewness and kurtosis
        self.assertAlmostEqual(advanced_stats["skewness"], float(stats.skew(prices_array)), places=5)
        self.assertAlmostEqual(advanced_stats["kurtosis"], float(stats.kurtosis(prices_array)), places=5)
        
        # Verify percentiles
        self.assertAlmostEqual(advanced_stats["percentiles"]["p10"], float(np.percentile(prices_array, 10)), places=5)
        self.assertAlmostEqual(advanced_stats["percentiles"]["p25"], float(np.percentile(prices_array, 25)), places=5)
        self.assertAlmostEqual(advanced_stats["percentiles"]["p50"], float(np.percentile(prices_array, 50)), places=5)
        self.assertAlmostEqual(advanced_stats["percentiles"]["p75"], float(np.percentile(prices_array, 75)), places=5)
        self.assertAlmostEqual(advanced_stats["percentiles"]["p90"], float(np.percentile(prices_array, 90)), places=5)
        self.assertAlmostEqual(advanced_stats["percentiles"]["p95"], float(np.percentile(prices_array, 95)), places=5)
        self.assertAlmostEqual(advanced_stats["percentiles"]["p99"], float(np.percentile(prices_array, 99)), places=5)
        
        # Verify outlier detection
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        self.assertAlmostEqual(advanced_stats["outliers"]["lower_bound"], float(lower_bound), places=5)
        self.assertAlmostEqual(advanced_stats["outliers"]["upper_bound"], float(upper_bound), places=5)
        
        # Verify outlier count and values
        outliers = prices_array[(prices_array < lower_bound) | (prices_array > upper_bound)]
        self.assertEqual(advanced_stats["outliers"]["outlier_count"], len(outliers))
        
        # If there are outliers, verify their values
        if len(outliers) > 0:
            for i, outlier in enumerate(advanced_stats["outliers"]["outlier_values"]):
                self.assertAlmostEqual(outlier, float(outliers[i]), places=5)

if __name__ == "__main__":
    print(f"Testing Stock Statistics API at: {API_URL}")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)