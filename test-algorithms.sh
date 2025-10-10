#!/bin/bash

# Test Algorithm API Endpoints
# This script tests the newly implemented algorithm trading feature

API_BASE="http://localhost:8000"

echo "====================================="
echo "Algorithm Trading API Tests"
echo "====================================="
echo ""

# Test 1: Get Algorithm Dashboard (no auth required for testing)
echo "Test 1: Get Algorithm Dashboard"
echo "GET /api/v1/algorithms/dashboard"
curl -s "$API_BASE/api/v1/algorithms/dashboard" | jq '.'
echo ""
echo ""

# Test 2: List Algorithms (no auth required for testing)
echo "Test 2: List Algorithms"
echo "GET /api/v1/algorithms"
curl -s "$API_BASE/api/v1/algorithms" | jq '.'
echo ""
echo ""

# Test 3: Validate Algorithm Code
echo "Test 3: Validate Algorithm Code"
echo "POST /api/v1/algorithms/validate"
curl -s -X POST "$API_BASE/api/v1/algorithms/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_code": "# Simple test\nfor symbol, data in market_data.items():\n    pass"
  }' | jq '.'
echo ""
echo ""

# Test 4: Check OpenAPI docs for algorithm endpoints
echo "Test 4: Check if Algorithm Trading endpoints are in OpenAPI"
echo "GET /openapi.json (filtered for algorithm)"
curl -s "$API_BASE/openapi.json" | jq '.paths | keys | map(select(contains("algorithm")))'
echo ""
echo ""

echo "====================================="
echo "Tests Complete!"
echo "====================================="
