"""
SerpAPI Travel MCP Server
Provides flight and hotel search capabilities using SerpAPI's Google Flights and Google Hotels engines.
"""

import os
import sys
import json
import logging
from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Set up logging to help debug issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Check for API key early
if not os.environ.get('SERPAPI_API_KEY'):
    logger.warning("SERPAPI_API_KEY not found in environment variables!")
    logger.info("Please set SERPAPI_API_KEY in your .env file or environment")
else:
    logger.info("SERPAPI_API_KEY found in environment")

# Initialize FastMCP server
try:
    mcp = FastMCP("serpapi-travel")
    logger.info("FastMCP server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize FastMCP: {e}")
    sys.exit(1)

# Constants
SERPAPI_BASE_URL = "https://serpapi.com/search"

async def make_serpapi_request(params: dict[str, Any]) -> dict[str, Any] | None:
    """Make a request to the SerpAPI with proper error handling."""
    # Add API key to params
    params['api_key'] = os.environ.get('SERPAPI_API_KEY')
    
    if not params['api_key']:
        error_msg = "SERPAPI_API_KEY environment variable is not set. Please add it to your .env file or configuration."
        logger.error(error_msg)
        return {"error": error_msg}
    
    logger.info(f"Making SerpAPI request with engine: {params.get('engine', 'unknown')}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                SERPAPI_BASE_URL,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            logger.info("SerpAPI request successful")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from SerpAPI: {e}")
            # Try to get error details from response
            try:
                error_data = e.response.json()
                return {"error": f"SerpAPI error: {error_data.get('error', str(e))}"}
            except:
                return {"error": f"HTTP error occurred: {str(e)}"}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": f"Request failed: {str(e)}"}

@mcp.tool()
async def search_flights(
    departure_airport: str,
    arrival_airport: str,
    outbound_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0
) -> str:
    """
    Search for flights using Google Flights engine via SerpAPI.

    Args:
        departure_airport: Departure airport code (e.g., 'NYC', 'LAX', 'JFK')
        arrival_airport: Arrival airport code (e.g., 'LON', 'NRT', 'CDG')
        outbound_date: Departure date in YYYY-MM-DD format (e.g., '2025-12-15')
        return_date: Return date in YYYY-MM-DD format (optional for one-way trips)
        adults: Number of adult passengers (default: 1)
        children: Number of child passengers (default: 0)
    
    Returns:
        JSON string containing flight search results with best flights
    """
    logger.info(f"Searching flights: {departure_airport} -> {arrival_airport} on {outbound_date}")
    
    params = {
        'engine': 'google_flights',
        'hl': 'en',
        'gl': 'us',
        'departure_id': departure_airport,
        'arrival_id': arrival_airport,
        'outbound_date': outbound_date,
        'currency': 'USD',
        'adults': adults,
        'children': children
    }
    
    # Set flight type: 1 = Round trip, 2 = One way
    if return_date:
        params['type'] = '1'  # Round trip
        params['return_date'] = return_date
        logger.info(f"Round trip with return on {return_date}")
    else:
        params['type'] = '2'  # One way
        logger.info("One way trip")
    
    try:
        data = await make_serpapi_request(params)
        
        if not data:
            return json.dumps({"error": "Unable to fetch flight data"}, indent=2)
        
        if "error" in data:
            return json.dumps(data, indent=2)
        
        # Get best flights from results
        best_flights = data.get('best_flights', [])
        
        if not best_flights:
            # If no best_flights, try to get other_flights
            other_flights = data.get('other_flights', [])
            if other_flights:
                logger.info(f"Found {len(other_flights)} other flights (no best flights)")
                return json.dumps({
                    "message": "No best flights found, showing other options",
                    "flights": other_flights[:10]
                }, indent=2)
            logger.warning("No flights found in response")
            return json.dumps({
                "message": "No flights found",
                "available_keys": list(data.keys())
            }, indent=2)
        
        logger.info(f"Found {len(best_flights)} best flights")
        return json.dumps(best_flights, indent=2)
        
    except Exception as e:
        logger.error(f"Flight search failed: {e}")
        return json.dumps({"error": f"Flight search failed: {str(e)}"}, indent=2)

@mcp.tool()
async def search_hotels(
    location: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 1,
    children: int = 0,
    rooms: int = 1,
    hotel_class: Optional[str] = None,
    sort_by: int = 8
) -> str:
    """
    Search for hotels using Google Hotels engine via SerpAPI.

    Args:
        location: Location to search for hotels (e.g., 'New York', 'Paris', 'Tokyo')
        check_in_date: Check-in date in YYYY-MM-DD format (e.g., '2025-12-15')
        check_out_date: Check-out date in YYYY-MM-DD format (e.g., '2025-12-20')
        adults: Number of adults (default: 1)
        children: Number of children (default: 0)
        rooms: Number of rooms (default: 1)
        hotel_class: Hotel star rating filter as comma-separated string (e.g., '2,3,4' for 2-4 star hotels, optional)
        sort_by: Sort parameter - 8 for highest rating (default), 3 for lowest price, 13 for highest price
    
    Returns:
        JSON string containing top 5 hotel search results
    """
    logger.info(f"Searching hotels in {location} from {check_in_date} to {check_out_date}")
    
    # Ensure proper integer types
    adults = int(float(adults)) if adults else 1
    children = int(float(children)) if children else 0
    rooms = int(float(rooms)) if rooms else 1
    sort_by = int(float(sort_by)) if sort_by else 8
    
    params = {
        'engine': 'google_hotels',
        'hl': 'en',
        'gl': 'us',
        'q': location,
        'check_in_date': check_in_date,
        'check_out_date': check_out_date,
        'currency': 'USD',
        'adults': adults,
        'children': children,
        'rooms': rooms,
        'sort_by': sort_by
    }
    
    # Only add hotel_class if provided
    if hotel_class:
        params['hotel_class'] = hotel_class
        logger.info(f"Filtering by hotel class: {hotel_class}")
    
    try:
        data = await make_serpapi_request(params)
        
        if not data:
            return json.dumps({"error": "Unable to fetch hotel data"}, indent=2)
        
        if "error" in data:
            return json.dumps(data, indent=2)
        
        # Get properties from results
        properties = data.get('properties', [])
        
        if not properties:
            logger.warning("No hotels found in response")
            return json.dumps({
                "message": "No hotels found",
                "available_keys": list(data.keys())
            }, indent=2)
        
        logger.info(f"Found {len(properties)} hotels, returning top 5")
        # Return top 5 results
        return json.dumps(properties[:5], indent=2)
        
    except Exception as e:
        logger.error(f"Hotel search failed: {e}")
        return json.dumps({"error": f"Hotel search failed: {str(e)}"}, indent=2)

def main():
    """Initialize and run the server."""
    try:
        logger.info("Starting SerpAPI Travel MCP Server...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Check if .env file exists
        if os.path.exists('.env'):
            logger.info(".env file found")
        else:
            logger.warning(".env file not found in current directory")
        
        # Run the server
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()