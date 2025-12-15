#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Distance Service - Korean region distance matrix
Provides distance calculations between Korean regions
"""

# Approximate road distances between Korean regions (in km)
# Based on major cities: 서울(서울중앙), 인천, 수원(경기), 춘천(강원), 대전(대전.세종.충남), 
# 청주(충북), 전주(전북), 광주(광주.전남), 대구(대구.경북), 부산, 울산, 창원(경남), 제주
DISTANCE_MATRIX = {
    "서울중앙": {
        "서울중앙": 0,
        "인천": 30,
        "경    기": 40,
        "강    원": 120,
        "대전.세종.충남": 160,
        "충    북": 120,
        "전    북": 240,
        "광주.전남": 320,
        "대구.경북": 300,
        "부    산": 400,
        "울    산": 420,
        "경    남": 380,
        "제    주": 450,  # Special: ferry + road
    },
    "인천": {
        "서울중앙": 30,
        "인천": 0,
        "경    기": 50,
        "강    원": 150,
        "대전.세종.충남": 190,
        "충    북": 150,
        "전    북": 270,
        "광주.전남": 350,
        "대구.경북": 330,
        "부    산": 430,
        "울    산": 450,
        "경    남": 410,
        "제    주": 480,
    },
    "경    기": {
        "서울중앙": 40,
        "인천": 50,
        "경    기": 0,
        "강    원": 110,
        "대전.세종.충남": 150,
        "충    북": 110,
        "전    북": 230,
        "광주.전남": 310,
        "대구.경북": 290,
        "부    산": 390,
        "울    산": 410,
        "경    남": 370,
        "제    주": 440,
    },
    "강    원": {
        "서울중앙": 120,
        "인천": 150,
        "경    기": 110,
        "강    원": 0,
        "대전.세종.충남": 200,
        "충    북": 160,
        "전    북": 280,
        "광주.전남": 360,
        "대구.경북": 340,
        "부    산": 440,
        "울    산": 460,
        "경    남": 420,
        "제    주": 490,
    },
    "대전.세종.충남": {
        "서울중앙": 160,
        "인천": 190,
        "경    기": 150,
        "강    원": 200,
        "대전.세종.충남": 0,
        "충    북": 50,
        "전    북": 100,
        "광주.전남": 150,
        "대구.경북": 140,
        "부    산": 240,
        "울    산": 260,
        "경    남": 220,
        "제    주": 290,
    },
    "충    북": {
        "서울중앙": 120,
        "인천": 150,
        "경    기": 110,
        "강    원": 160,
        "대전.세종.충남": 50,
        "충    북": 0,
        "전    북": 120,
        "광주.전남": 200,
        "대구.경북": 180,
        "부    산": 280,
        "울    산": 300,
        "경    남": 260,
        "제    주": 330,
    },
    "전    북": {
        "서울중앙": 240,
        "인천": 270,
        "경    기": 230,
        "강    원": 280,
        "대전.세종.충남": 100,
        "충    북": 120,
        "전    북": 0,
        "광주.전남": 80,
        "대구.경북": 150,
        "부    산": 250,
        "울    산": 270,
        "경    남": 230,
        "제    주": 300,
    },
    "광주.전남": {
        "서울중앙": 320,
        "인천": 350,
        "경    기": 310,
        "강    원": 360,
        "대전.세종.충남": 150,
        "충    북": 200,
        "전    북": 80,
        "광주.전남": 0,
        "대구.경북": 200,
        "부    산": 200,
        "울    산": 220,
        "경    남": 180,
        "제    주": 250,
    },
    "대구.경북": {
        "서울중앙": 300,
        "인천": 330,
        "경    기": 290,
        "강    원": 340,
        "대전.세종.충남": 140,
        "충    북": 180,
        "전    북": 150,
        "광주.전남": 200,
        "대구.경북": 0,
        "부    산": 100,
        "울    산": 80,
        "경    남": 100,
        "제    주": 170,
    },
    "부    산": {
        "서울중앙": 400,
        "인천": 430,
        "경    기": 390,
        "강    원": 440,
        "대전.세종.충남": 240,
        "충    북": 280,
        "전    북": 250,
        "광주.전남": 200,
        "대구.경북": 100,
        "부    산": 0,
        "울    산": 30,
        "경    남": 50,
        "제    주": 120,
    },
    "울    산": {
        "서울중앙": 420,
        "인천": 450,
        "경    기": 410,
        "강    원": 460,
        "대전.세종.충남": 260,
        "충    북": 300,
        "전    북": 270,
        "광주.전남": 220,
        "대구.경북": 80,
        "부    산": 30,
        "울    산": 0,
        "경    남": 40,
        "제    주": 110,
    },
    "경    남": {
        "서울중앙": 380,
        "인천": 410,
        "경    기": 370,
        "강    원": 420,
        "대전.세종.충남": 220,
        "충    북": 260,
        "전    북": 230,
        "광주.전남": 180,
        "대구.경북": 100,
        "부    산": 50,
        "울    산": 40,
        "경    남": 0,
        "제    주": 70,
    },
    "제    주": {
        "서울중앙": 450,
        "인천": 480,
        "경    기": 440,
        "강    원": 490,
        "대전.세종.충남": 290,
        "충    북": 330,
        "전    북": 300,
        "광주.전남": 250,
        "대구.경북": 170,
        "부    산": 120,
        "울    산": 110,
        "경    남": 70,
        "제    주": 0,
    },
}

# Maximum practical transfer distance (km)
# Regions beyond this distance should be excluded or heavily penalized
MAX_TRANSFER_DISTANCE = 500

# Special case: 제주 is isolated, so transfers to/from 제주 should be limited
JEJU_PENALTY = 200  # Additional distance penalty for 제주 transfers


def get_distance(from_region: str, to_region: str) -> float:
    """
    Get distance between two regions in kilometers
    
    Args:
        from_region: Source region name
        to_region: Destination region name
    
    Returns:
        Distance in kilometers, or float('inf') if not found
    """
    # Normalize region names (remove extra spaces)
    from_region = from_region.strip()
    to_region = to_region.strip()
    
    if from_region not in DISTANCE_MATRIX:
        return float('inf')
    
    if to_region not in DISTANCE_MATRIX[from_region]:
        return float('inf')
    
    distance = DISTANCE_MATRIX[from_region][to_region]
    
    # Apply 제주 penalty if either region is 제주
    if "제    주" in [from_region, to_region] and from_region != to_region:
        distance += JEJU_PENALTY
    
    return distance


def is_transfer_feasible(from_region: str, to_region: str) -> bool:
    """
    Check if transfer between two regions is feasible
    
    Args:
        from_region: Source region name
        to_region: Destination region name
    
    Returns:
        True if transfer is feasible, False otherwise
    """
    distance = get_distance(from_region, to_region)
    
    # Exclude transfers beyond maximum distance
    if distance > MAX_TRANSFER_DISTANCE:
        return False
    
    # Special case: 제주 transfers are generally not feasible
    # (unless it's a very special case, but for now we'll exclude them)
    if "제    주" in [from_region, to_region] and from_region != to_region:
        return False  # 제주 is isolated, exclude from regular transfers
    
    return True


def get_nearby_regions(region: str, max_distance: float = None) -> list:
    """
    Get list of nearby regions sorted by distance
    
    Args:
        region: Source region name
        max_distance: Maximum distance to include (default: MAX_TRANSFER_DISTANCE)
    
    Returns:
        List of tuples (region_name, distance) sorted by distance
    """
    if max_distance is None:
        max_distance = MAX_TRANSFER_DISTANCE
    
    region = region.strip()
    nearby = []
    
    for other_region in DISTANCE_MATRIX.keys():
        if other_region == region:
            continue
        
        distance = get_distance(region, other_region)
        if distance <= max_distance and is_transfer_feasible(region, other_region):
            nearby.append((other_region, distance))
    
    # Sort by distance
    nearby.sort(key=lambda x: x[1])
    
    return nearby

