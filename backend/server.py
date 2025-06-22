from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import numpy as np
import pandas as pd
from scipy import stats
import re
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StockPricesInput(BaseModel):
    prices_text: str

class StockAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prices: List[float]
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    basic_stats: dict
    advanced_stats: dict
    
class StockAnalysisCreate(BaseModel):
    prices: List[float]
    basic_stats: dict
    advanced_stats: dict

class StockStatistics(BaseModel):
    basic_stats: dict
    advanced_stats: dict
    raw_prices: List[float]
    price_count: int

def parse_stock_prices(prices_text: str) -> List[float]:
    """Parse stock prices from various input formats."""
    if not prices_text.strip():
        raise ValueError("No input provided")
    
    # Clean the input
    cleaned_text = prices_text.strip()
    
    # Try different separators
    prices = []
    
    # First try comma-separated
    if ',' in cleaned_text:
        parts = cleaned_text.split(',')
    # Then try space-separated
    elif ' ' in cleaned_text:
        parts = re.split(r'\s+', cleaned_text)
    # Then try newline-separated
    elif '\n' in cleaned_text:
        parts = cleaned_text.split('\n')
    else:
        # Single number
        parts = [cleaned_text]
    
    for part in parts:
        part = part.strip()
        if part:  # Skip empty parts
            try:
                # Remove any currency symbols or commas within numbers
                clean_part = re.sub(r'[₹,$]', '', part)
                clean_part = clean_part.replace(',', '')
                price = float(clean_part)
                if price < 0:
                    raise ValueError(f"Negative price not allowed: {price}")
                prices.append(price)
            except ValueError as e:
                raise ValueError(f"Invalid number format: '{part}'")
    
    if not prices:
        raise ValueError("No valid prices found")
    
    if len(prices) < 2:
        raise ValueError("At least 2 prices are required for statistical analysis")
    
    return prices

def calculate_basic_statistics(prices: List[float]) -> dict:
    """Calculate basic descriptive statistics."""
    prices_array = np.array(prices)
    
    return {
        "mean": float(np.mean(prices_array)),
        "median": float(np.median(prices_array)),
        "mode": float(stats.mode(prices_array, keepdims=True).mode[0]) if len(set(prices)) < len(prices) else None,
        "minimum": float(np.min(prices_array)),
        "maximum": float(np.max(prices_array)), 
        "range": float(np.max(prices_array) - np.min(prices_array)),
        "std_deviation": float(np.std(prices_array, ddof=1)),
        "variance": float(np.var(prices_array, ddof=1))
    }

def calculate_advanced_statistics(prices: List[float]) -> dict:
    """Calculate advanced descriptive statistics."""
    prices_array = np.array(prices)
    
    # Quartiles and percentiles
    q1 = float(np.percentile(prices_array, 25))
    q2 = float(np.percentile(prices_array, 50))  # Same as median
    q3 = float(np.percentile(prices_array, 75))
    
    return {
        "quartiles": {
            "q1": q1,
            "q2": q2,
            "q3": q3
        },
        "iqr": float(q3 - q1),
        "skewness": float(stats.skew(prices_array)),
        "kurtosis": float(stats.kurtosis(prices_array)),
        "percentiles": {
            "p10": float(np.percentile(prices_array, 10)),
            "p25": float(np.percentile(prices_array, 25)),
            "p50": float(np.percentile(prices_array, 50)),
            "p75": float(np.percentile(prices_array, 75)),
            "p90": float(np.percentile(prices_array, 90)),
            "p95": float(np.percentile(prices_array, 95)),
            "p99": float(np.percentile(prices_array, 99))
        },
        "outliers": detect_outliers(prices_array)
    }

def detect_outliers(prices_array: np.ndarray) -> dict:
    """Detect outliers using IQR method."""
    q1 = np.percentile(prices_array, 25)
    q3 = np.percentile(prices_array, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = prices_array[(prices_array < lower_bound) | (prices_array > upper_bound)]
    
    return {
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
        "outlier_values": [float(x) for x in outliers],
        "outlier_count": len(outliers)
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Stock Statistics API - Netflix Edition 📈"}

@api_router.post("/analyze-stocks", response_model=StockStatistics)
async def analyze_stock_prices(input_data: StockPricesInput):
    """Analyze stock prices and return comprehensive statistics."""
    try:
        # Parse the input prices
        prices = parse_stock_prices(input_data.prices_text)
        
        # Calculate statistics
        basic_stats = calculate_basic_statistics(prices)
        advanced_stats = calculate_advanced_statistics(prices)
        
        return StockStatistics(
            basic_stats=basic_stats,
            advanced_stats=advanced_stats,
            raw_prices=prices,
            price_count=len(prices)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.post("/save-analysis", response_model=StockAnalysis)
async def save_analysis(analysis_data: StockAnalysisCreate):
    """Save stock analysis to database."""
    try:
        analysis_obj = StockAnalysis(**analysis_data.dict())
        await db.stock_analyses.insert_one(analysis_obj.dict())
        return analysis_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")

@api_router.get("/saved-analyses", response_model=List[StockAnalysis])
async def get_saved_analyses():
    """Get all saved stock analyses."""
    try:
        analyses = await db.stock_analyses.find().sort("analysis_date", -1).to_list(100)
        return [StockAnalysis(**analysis) for analysis in analyses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()