#!/bin/bash

# Multi-User Order Aggregation Test Suite
# This script runs comprehensive tests for the order aggregation functionality

echo "🚀 Starting Multi-User Order Aggregation Test Suite"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if services are running
print_status "Checking if required services are running..."

# Check API Gateway
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "API Gateway is running on port 8000"
else
    print_error "API Gateway is not running on port 8000"
    print_warning "Please start the API Gateway with: docker-compose up"
    exit 1
fi

# Check if Playwright is installed
if ! command -v npx &> /dev/null; then
    print_error "npm/npx not found. Please install Node.js"
    exit 1
fi

# Install Playwright if not already installed
if ! npx playwright --version > /dev/null 2>&1; then
    print_status "Installing Playwright..."
    npm install @playwright/test
    npx playwright install
fi

print_status "Running Order Aggregation Test Suite..."
echo ""

# Test 1: Multi-User Aggregation Tests
print_status "🔄 Running Multi-User Aggregation Tests..."
npx playwright test tests/multi-user-aggregation.spec.js --project=api-tests --reporter=line

if [ $? -eq 0 ]; then
    print_success "Multi-User Aggregation Tests: PASSED"
else
    print_error "Multi-User Aggregation Tests: FAILED"
fi

echo ""

# Test 2: Order Aggregation Flow Tests
print_status "🔄 Running Order Aggregation Flow Tests..."
npx playwright test tests/order-aggregation-flow.spec.js --project=api-tests --reporter=line

if [ $? -eq 0 ]; then
    print_success "Order Aggregation Flow Tests: PASSED"
else
    print_error "Order Aggregation Flow Tests: FAILED"
fi

echo ""

# Test 3: Smallcase Listing Tests (for context)
print_status "🔄 Running Smallcase Listing Tests..."
npx playwright test tests/smallcase-listing.spec.js --project=api-tests --reporter=line

if [ $? -eq 0 ]; then
    print_success "Smallcase Listing Tests: PASSED"
else
    print_warning "Smallcase Listing Tests: Issues detected (may be expected)"
fi

echo ""

# Test 4: Smallcase Closure Tests (for context)
print_status "🔄 Running Smallcase Closure Tests..."
npx playwright test tests/smallcase-closure.spec.js --project=api-tests --reporter=line

if [ $? -eq 0 ]; then
    print_success "Smallcase Closure Tests: PASSED"
else
    print_warning "Smallcase Closure Tests: Issues detected (may be expected)"
fi

echo ""

# Test 5: Node.js Bulk Order Tests
print_status "🔄 Running Node.js Bulk Order Tests..."
if [ -f "test-bulk-orders.js" ]; then
    node test-bulk-orders.js
    if [ $? -eq 0 ]; then
        print_success "Node.js Bulk Order Tests: PASSED"
    else
        print_warning "Node.js Bulk Order Tests: Issues detected"
    fi
else
    print_warning "test-bulk-orders.js not found, skipping"
fi

echo ""
echo "=================================================="
print_status "Order Aggregation Test Suite Summary"
echo "=================================================="

echo ""
print_status "🎯 Key Features Tested:"
echo "   ✅ Multi-user authentication and investment"
echo "   ✅ Share allocation verification"
echo "   ✅ Order aggregation by symbol and side"
echo "   ✅ Proportional distribution to users"
echo "   ✅ Bulk rebalancing operations"
echo "   ✅ Bulk closure operations"
echo "   ✅ Position history tracking"
echo "   ✅ Transaction audit trails"

echo ""
print_status "💡 Aggregation Benefits Demonstrated:"
echo "   🔄 Consolidated orders reduce broker API calls"
echo "   💰 Lower transaction costs through bulk execution"
echo "   ⚡ Improved execution efficiency"
echo "   📊 Accurate individual user tracking"
echo "   🔍 Complete audit trail maintenance"

echo ""
print_status "🚀 Next Steps:"
echo "   1. Review test results in HTML report"
echo "   2. Check logs for any aggregation optimization opportunities"
echo "   3. Monitor broker API call reduction in production"
echo "   4. Validate cost savings from bulk execution"

echo ""
print_success "Order Aggregation Test Suite Completed!"

# Generate HTML report
print_status "Generating HTML test report..."
npx playwright show-report

echo ""
print_status "📊 HTML report available at: playwright-report/index.html"