#!/usr/bin/env node

const API_BASE_URL = 'http://localhost:8000';

async function testClosureAPI() {
    console.log('🚀 Testing Smallcase Closure API Functionality\n');

    try {
        // Test 1: Login
        console.log('1. Testing Authentication...');
        const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'username=john.doe@example.com&password=password123'
        });

        if (!loginResponse.ok) {
            console.error('❌ Login failed:', await loginResponse.text());
            return;
        }

        const loginData = await loginResponse.json();
        const token = loginData.data?.access_token || loginData.access_token;
        if (!token) {
            console.error('❌ No access token received:', loginData);
            return;
        }

        console.log('✅ Login successful');
        console.log(`👤 User: ${loginData.data.user.username} (${loginData.data.user.email})`);

        // Test 2: Get user investments
        console.log('\n2. Fetching user investments...');
        const investmentsResponse = await fetch(`${API_BASE_URL}/smallcases/user/investments`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!investmentsResponse.ok) {
            console.error('❌ Failed to get investments:', await investmentsResponse.text());
            return;
        }

        const investmentsData = await investmentsResponse.json();
        console.log(`✅ Found ${investmentsData.data.length} active investments`);

        if (investmentsData.data.length === 0) {
            console.log('⚠️ No investments found to test closure');
            return;
        }

        const investment = investmentsData.data[0];
        console.log('📊 Investment object:', JSON.stringify(investment, null, 2));
        console.log(`📊 Testing with investment ID: ${investment.id}`);

        // Test 3: Closure preview
        console.log('\n3. Testing closure preview...');
        const previewResponse = await fetch(`${API_BASE_URL}/smallcases/investments/${investment.id}/closure-preview`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!previewResponse.ok) {
            console.error('❌ Closure preview failed:', await previewResponse.text());
            return;
        }

        const previewData = await previewResponse.json();
        console.log('✅ Closure preview successful');
        console.log('📈 Preview data:', {
            investment_amount: previewData.data.investment_amount,
            current_value: previewData.data.current_value,
            unrealized_pnl: previewData.data.unrealized_pnl,
            roi_percentage: previewData.data.roi_percentage,
            holding_period_days: previewData.data.holding_period_days
        });

        // Test 4: Test closure (only for paper mode to be safe)
        if (investment.execution_mode === 'paper') {
            console.log('\n4. Testing position closure (paper mode)...');
            const closeResponse = await fetch(`${API_BASE_URL}/smallcases/investments/${investment.id}/close`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    closure_reason: 'test_closure_api'
                })
            });

            if (!closeResponse.ok) {
                console.error('❌ Position closure failed:', await closeResponse.text());
                return;
            }

            const closeData = await closeResponse.json();
            console.log('✅ Position closed successfully');
            console.log('💰 Closure results:', {
                position_closed: closeData.data.position_closed,
                realized_pnl: closeData.data.realized_pnl,
                exit_value: closeData.data.exit_value,
                holding_period_days: closeData.data.holding_period_days
            });
        } else {
            console.log('\n4. ⚠️ Skipping closure test (not paper mode - safety first!)');
        }

        // Test 5: Position history
        console.log('\n5. Testing position history...');
        const historyResponse = await fetch(`${API_BASE_URL}/smallcases/user/positions/history`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!historyResponse.ok) {
            console.error('❌ Position history failed:', await historyResponse.text());
            return;
        }

        const historyData = await historyResponse.json();
        console.log(`✅ Found ${historyData.data.length} historical positions`);

        // Test 6: Transaction history
        console.log('\n6. Testing enhanced transaction history...');
        const transactionsResponse = await fetch(`${API_BASE_URL}/trading/transactions?limit=5`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!transactionsResponse.ok) {
            console.error('❌ Transaction history failed:', await transactionsResponse.text());
            return;
        }

        const transactionsData = await transactionsResponse.json();
        console.log(`✅ Found ${transactionsData.data.transactions.length} recent transactions`);

        // Test 7: Smallcase listing with investment status
        console.log('\n7. Testing smallcase listing with investment status...');
        const smallcasesResponse = await fetch(`${API_BASE_URL}/smallcases/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!smallcasesResponse.ok) {
            console.error('❌ Smallcase listing failed:', await smallcasesResponse.text());
            return;
        }

        const smallcasesData = await smallcasesResponse.json();
        const investedCount = smallcasesData.data.filter(sc => sc.isInvested).length;
        const totalCount = smallcasesData.data.length;
        console.log(`✅ Found ${totalCount} smallcases, ${investedCount} invested`);

        console.log('\n🎉 All tests completed successfully!');
        console.log('\n📋 Closure functionality summary:');
        console.log('✅ User authentication working');
        console.log('✅ Investment listing working');
        console.log('✅ Closure preview working');
        console.log('✅ Position history working');
        console.log('✅ Transaction history enhanced');
        console.log('✅ Smallcase listing shows investment status');
        if (investment.execution_mode === 'paper') {
            console.log('✅ Position closure working (tested in paper mode)');
        }

    } catch (error) {
        console.error('❌ Test failed with error:', error.message);
    }
}

// Run the tests
testClosureAPI();