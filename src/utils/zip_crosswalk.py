"""
ZIP to County crosswalk utility
Loads and caches ZIP to county mappings from CSV file
"""
import csv
import os
from typing import Dict, List, Optional, Tuple

# Cache for crosswalk data
_crosswalk_cache: Optional[Dict[str, Dict[str, str]]] = None
_county_to_zips_cache: Optional[Dict[Tuple[str, str], List[str]]] = None


def _load_crosswalk() -> Dict[str, Dict[str, str]]:
    """Load ZIP to county crosswalk from CSV file"""
    global _crosswalk_cache
    
    if _crosswalk_cache is not None:
        return _crosswalk_cache
    
    _crosswalk_cache = {}
    
    # Get path to crosswalk file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    crosswalk_path = os.path.join(project_root, 'data', 'zip_county_crosswalk.csv')
    
    if not os.path.exists(crosswalk_path):
        raise FileNotFoundError(f"Crosswalk file not found at {crosswalk_path}")
    
    with open(crosswalk_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            zip_code = row['zip'].strip()
            _crosswalk_cache[zip_code] = {
                'county': row['county'].strip(),
                'state': row['state'].strip(),
                'state_abbr': row['state_abbr'].strip()
            }
    
    return _crosswalk_cache


def _load_county_to_zips() -> Dict[Tuple[str, str], List[str]]:
    """Build reverse mapping from county to ZIP codes"""
    global _county_to_zips_cache
    
    if _county_to_zips_cache is not None:
        return _county_to_zips_cache
    
    _county_to_zips_cache = {}
    crosswalk = _load_crosswalk()
    
    for zip_code, info in crosswalk.items():
        key = (info['county'], info['state_abbr'])
        if key not in _county_to_zips_cache:
            _county_to_zips_cache[key] = []
        _county_to_zips_cache[key].append(zip_code)
    
    return _county_to_zips_cache


def get_county_for_zip(zip_code: str) -> Optional[Dict[str, str]]:
    """
    Get county information for a ZIP code
    
    Args:
        zip_code: 5-digit ZIP code as string
        
    Returns:
        Dictionary with 'county', 'state', and 'state_abbr', or None if not found
    """
    crosswalk = _load_crosswalk()
    return crosswalk.get(zip_code)


def get_zips_for_county(county: str, state_abbr: str) -> List[str]:
    """
    Get all ZIP codes for a given county and state
    
    Args:
        county: County name (e.g., "Los Angeles")
        state_abbr: State abbreviation (e.g., "CA")
        
    Returns:
        List of ZIP codes in the county
    """
    county_to_zips = _load_county_to_zips()
    return county_to_zips.get((county, state_abbr), [])
