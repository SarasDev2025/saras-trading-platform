# Paper Trading API Test Execution Guide

This guide provides step-by-step instructions for running comprehensive paper trading API tests for both Alpaca and Zerodha brokers.

## Overview

The test suite includes:
- **Alpaca Paper Trading Test**: Complete lifecycle testing for US-based users
- **Zerodha Paper Trading Test**: Complete lifecycle testing for Indian users
- **Test User Manager**: Utilities for managing test users and cleanup

## Prerequisites

1. **System Running**: Ensure all services are running via `docker-compose up`
2. **API Gateway**: Available at http://localhost:8000
3. **Database**: PostgreSQL with all migrations applied
4. **Broker Connections**: Paper trading credentials configured

## Test Files

- `test-alpaca-paper-trading.js` - Alpaca broker lifecycle test
- `test-zerodha-paper-trading.js` - Zerodha broker lifecycle test
- `test-user-manager.js` - Test user management utilities

## Execution Steps

### Step 1: Verify System Health

```bash
# Check if all services are running
curl http://localhost:8000/health

# Should return status: "healthy" with all services operational
```

### Step 2: Setup Test Users (Optional)

The user manager gracefully handles existing users and will not fail if users already exist in the database.

```bash
# Setup test user for Alpaca (creates new or uses existing)
node test-user-manager.js setup alpaca

# Setup test user for Zerodha (creates new or uses existing)
node test-user-manager.js setup zerodha

# Or setup both at once
node test-user-manager.js setup-all

# Check test environment status (shows if users existed or were created)
node test-user-manager.js status
```

**User Management Features:**
- ✅ Detects existing users before attempting registration
- ✅ Handles duplicate registration errors gracefully
- ✅ Falls back to existing user authentication if registration fails
- ✅ Tracks whether users were newly created or already existed
- ✅ Provides clear status indicators in output

### Step 3: Run Alpaca Paper Trading Test

```bash
# Execute complete Alpaca broker test
node test-alpaca-paper-trading.js
```

**Expected Flow:**
1. ✅ System health check
2. ✅ User authentication (john.doe@example.com)
3. ✅ Fetch available smallcases
4. ✅ Create investment ($150,000 USD)
5. ✅ Verify Alpaca broker selection (US region)
6. ✅ Verify orders placed via Alpaca API
7. ✅ Capture initial portfolio positions
8. ✅ Trigger smallcase rebalancing
9. ✅ Verify rebalancing orders
10. ✅ Verify updated positions
11. ✅ Close investment
12. ✅ Generate comprehensive test report

### Step 4: Run Zerodha Paper Trading Test

```bash
# Execute complete Zerodha broker test
node test-zerodha-paper-trading.js
```

**Expected Flow:**
1. ✅ System health check
2. ✅ User authentication (priya.sharma@example.com)
3. ✅ Fetch available smallcases
4. ✅ Create investment (₹50,000 INR)
5. ✅ Verify Zerodha broker selection (IN region)
6. ✅ Verify orders placed via Zerodha Kite API
7. ✅ Capture initial portfolio positions
8. ✅ Trigger smallcase rebalancing
9. ✅ Verify rebalancing orders
10. ✅ Verify updated positions
11. ✅ Close investment
12. ✅ Generate comprehensive test report

### Step 5: Cleanup (Optional)

```bash
# Clean up all test data
node test-user-manager.js cleanup
```

## Test Configuration

### Alpaca Test User
- **Email**: john.doe@example.com
- **Region**: US
- **Investment**: $150,000 USD
- **Expected Broker**: Alpaca

### Zerodha Test User
- **Email**: priya.sharma@example.com
- **Region**: IN
- **Investment**: ₹50,000 INR
- **Expected Broker**: Zerodha

## Expected Outputs

### Successful Test Output
```
🚀 Starting [Broker] Paper Trading API Test
🎯 Testing complete investment lifecycle with [Broker] broker integration

🔵 Step 1: User Authentication
✅ User authenticated successfully: [email]

🔵 Step 2: Fetch Available Smallcases
✅ Selected smallcase: [name] ([id])

[... additional steps ...]

🎉 [BROKER] PAPER TRADING TEST COMPLETED SUCCESSFULLY! 🎉

🎯 [BROKER] PAPER TRADING API TEST REPORT
📊 Test Configuration:
   User: [email]
   Region: [region]
   Investment Amount: [amount]
   Expected Broker: [broker]

📈 Test Results:
   Investment ID: [id]
   Smallcase ID: [id]
   Broker Connection ID: [id]
   Broker Orders Placed: [count]
```

### Failed Test Output
```
❌ [Error description]
💥 [BROKER] PAPER TRADING TEST FAILED

[Error details and stack trace]
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Ensure services are running
   docker-compose ps
   docker-compose up -d
   ```

2. **Authentication Failed**
   ```bash
   # Check user status first
   node test-user-manager.js status

   # Reset test users if needed
   node test-user-manager.js cleanup
   node test-user-manager.js setup-all
   ```

2.1. **User Already Exists Errors**
   ```bash
   # The user manager automatically handles existing users
   # If you see "already exists" messages, these are informational
   # Example output:
   # ✅ Test user john.doe@example.com already exists - using existing user
   # 🔄 Existing user detected and authenticated successfully
   ```

3. **No Available Smallcases**
   ```bash
   # Check smallcase data in database
   # May need to seed test smallcases
   ```

4. **Broker Connection Issues**
   ```bash
   # Verify broker credentials in environment
   # Check broker API health
   ```

### Database Queries for Debugging

```sql
-- Check test users
SELECT id, email, region FROM users WHERE email LIKE '%example.com';

-- Check broker connections
SELECT user_id, broker_type, status FROM user_broker_connections;

-- Check recent investments
SELECT id, user_id, amount, status FROM smallcase_investments
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Check broker orders
SELECT investment_id, symbol, side, quantity, status, broker_order_id
FROM execution_run_orders
WHERE created_at > NOW() - INTERVAL '1 hour';
```

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```bash
#!/bin/bash
# ci-test-brokers.sh

set -e

echo "🔄 Starting broker API tests..."

# Start services (if not running)
docker-compose up -d --wait

# Wait for services to be ready
sleep 30

# Run tests
echo "Testing Alpaca integration..."
node test-alpaca-paper-trading.js

echo "Testing Zerodha integration..."
node test-zerodha-paper-trading.js

# Cleanup
node test-user-manager.js cleanup

echo "✅ All broker tests completed successfully"
```

## Performance Expectations

- **Test Duration**: 2-3 minutes per broker
- **API Calls**: ~15-20 API calls per test
- **Database Operations**: ~50-100 operations per test
- **Network Latency**: Consider broker API response times

## Security Notes

- Tests use paper trading credentials only
- No real money or live trading involved
- Test users are automatically cleaned up
- All credentials should be environment variables in production

## Support

For issues with the test suite:
1. Check system health endpoint: `/health`
2. Review API Gateway logs: `docker-compose logs api-gateway`
3. Verify database connectivity
4. Check broker API status pages