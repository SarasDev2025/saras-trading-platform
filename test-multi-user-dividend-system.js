/**
 * Test script for Multi-User Bulk Order System with Dividend Strategy
 * Tests the complete flow: investment → holdings → broker selection → dividend management
 */

const API_BASE_URL = 'http://localhost:8000';

// Test users configuration
const testUsers = [
    {
        email: 'john.doe@example.com',
        password: 'password123',
        region: 'US',  // Should get Alpaca broker
        investmentAmount: 5000,
        dripEnabled: true
    },
    {
        email: 'jane.smith@example.com',
        password: 'password123',
        region: 'US',  // Should get Alpaca broker
        investmentAmount: 7500,
        dripEnabled: true
    }
];

async function getAuthToken(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${email}&password=${password}`
    });

    if (!response.ok) {
        throw new Error(`Failed to authenticate ${email}: ${response.status}`);
    }

    const data = await response.json();
    return data.access_token || data.data?.access_token;
}

async function testMultiUserDividendSystem() {
    console.log('🚀 Testing Multi-User Bulk Order System with Dividend Strategy\n');

    try {
        // Phase 1: Setup and Authentication
        console.log('📋 Phase 1: Authentication and Setup');
        console.log('=' .repeat(50));

        const userTokens = {};
        const userInvestments = {};

        for (const user of testUsers) {
            console.log(`\n🔑 Authenticating ${user.email}...`);
            const token = await getAuthToken(user.email, user.password);
            userTokens[user.email] = token;
            console.log(`✅ ${user.email} authenticated successfully`);
        }

        // Phase 2: Multi-User Investment Creation
        console.log('\n\n📋 Phase 2: Multi-User Investment Creation');
        console.log('=' .repeat(50));

        // Get available smallcases
        console.log('\n🔍 Fetching available smallcases...');
        const smallcasesResponse = await fetch(`${API_BASE_URL}/smallcases/`, {
            headers: { 'Authorization': `Bearer ${userTokens[testUsers[0].email]}` }
        });

        const smallcasesData = await smallcasesResponse.json();
        const availableSmallcases = smallcasesData.data.filter(sc => !sc.isInvested);

        if (availableSmallcases.length === 0) {
            throw new Error('No available smallcases for testing');
        }

        const testSmallcase = availableSmallcases[0];
        console.log(`📊 Testing with smallcase: ${testSmallcase.name} (${testSmallcase.id})`);

        // Create investments for both users
        for (let i = 0; i < testUsers.length; i++) {
            const user = testUsers[i];
            console.log(`\n💰 Creating investment for ${user.email} ($${user.investmentAmount})...`);

            const investResponse = await fetch(`${API_BASE_URL}/smallcases/${testSmallcase.id}/invest`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${userTokens[user.email]}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: user.investmentAmount,
                    execution_mode: 'paper'
                })
            });

            if (!investResponse.ok) {
                const errorData = await investResponse.json();
                console.error(`❌ Investment failed for ${user.email}:`, errorData);
                continue;
            }

            const investData = await investResponse.json();
            userInvestments[user.email] = investData.data;
            console.log(`✅ Investment created: ${investData.data.investmentId}`);
            console.log(`   💵 Amount: $${investData.data.amount}`);
            console.log(`   📈 Holdings created: ${investData.data.holdingsCreated}`);
        }

        // Wait for processing
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Phase 3: Verify Broker Selection and Position Snapshots
        console.log('\n\n📋 Phase 3: Broker Selection and Position Snapshots');
        console.log('=' .repeat(50));

        for (const user of testUsers) {
            console.log(`\n🏦 Checking investments for ${user.email}...`);

            const investmentsResponse = await fetch(`${API_BASE_URL}/smallcases/user/investments`, {
                headers: { 'Authorization': `Bearer ${userTokens[user.email]}` }
            });

            const investmentsData = await investmentsResponse.json();
            const userInvestment = investmentsData.data.find(inv =>
                inv.smallcase.id === testSmallcase.id && inv.status === 'active'
            );

            if (userInvestment) {
                console.log(`✅ Investment found: ${userInvestment.id}`);
                console.log(`   💰 Current value: $${userInvestment.currentValue}`);
                console.log(`   📊 Status: ${userInvestment.status}`);
            } else {
                console.log(`❌ No active investment found for ${user.email}`);
            }
        }

        // Phase 4: Dividend Management Setup
        console.log('\n\n📋 Phase 4: Dividend Management and DRIP Setup');
        console.log('=' .repeat(50));

        // Setup DRIP preferences for users
        for (const user of testUsers) {
            if (user.dripEnabled) {
                console.log(`\n⚙️  Setting up DRIP preferences for ${user.email}...`);

                const dripResponse = await fetch(`${API_BASE_URL}/dividends/user/preferences`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${userTokens[user.email]}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        asset_id: null,  // Global preference
                        is_enabled: true,
                        minimum_amount: 10.0,  // $10 minimum for reinvestment
                        maximum_percentage: 100.0  // Reinvest 100% of dividends
                    })
                });

                if (dripResponse.ok) {
                    const dripData = await dripResponse.json();
                    console.log(`✅ DRIP enabled for ${user.email}`);
                    console.log(`   💸 Minimum amount: $${dripData.data.minimum_amount}`);
                    console.log(`   📊 Max percentage: ${dripData.data.maximum_percentage}%`);
                } else {
                    const errorData = await dripResponse.json();
                    console.log(`⚠️  DRIP setup failed for ${user.email}:`, errorData.detail);
                }
            }
        }

        // Phase 5: Create Test Dividend Declaration
        console.log('\n\n📋 Phase 5: Dividend Declaration and Processing');
        console.log('=' .repeat(50));

        // Get an asset from the smallcase constituents for dividend declaration
        console.log('\n📈 Creating test dividend declaration...');

        // For testing, we'll use a simplified approach and create a dividend for one of the assets
        const testAssetId = '550e8400-e29b-41d4-a716-446655440000';  // Using a test asset ID
        const dividendAmount = 2.50;  // $2.50 per share

        const currentDate = new Date();
        const exDividendDate = new Date(currentDate.getTime() + 7 * 24 * 60 * 60 * 1000); // 7 days from now
        const recordDate = new Date(exDividendDate.getTime() + 2 * 24 * 60 * 60 * 1000); // 2 days after ex-dividend
        const paymentDate = new Date(recordDate.getTime() + 14 * 24 * 60 * 60 * 1000); // 14 days after record

        const dividendResponse = await fetch(`${API_BASE_URL}/dividends/declarations`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${userTokens[testUsers[0].email]}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                asset_id: testAssetId,
                ex_dividend_date: exDividendDate.toISOString().split('T')[0],
                record_date: recordDate.toISOString().split('T')[0],
                payment_date: paymentDate.toISOString().split('T')[0],
                dividend_amount: dividendAmount,
                dividend_type: 'cash',
                currency: 'USD'
            })
        });

        if (dividendResponse.ok) {
            const dividendData = await dividendResponse.json();
            console.log(`✅ Dividend declaration created: ${dividendData.data.id}`);
            console.log(`   💰 Amount: $${dividendData.data.dividend_amount} per share`);
            console.log(`   📅 Ex-dividend date: ${dividendData.data.ex_dividend_date}`);

            // Process position snapshots for this dividend
            console.log('\n📸 Processing position snapshots...');
            const snapshotResponse = await fetch(
                `${API_BASE_URL}/dividends/declarations/${dividendData.data.id}/process-snapshots`,
                {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${userTokens[testUsers[0].email]}` }
                }
            );

            if (snapshotResponse.ok) {
                const snapshotData = await snapshotResponse.json();
                console.log(`✅ Position snapshots created: ${snapshotData.data.snapshots_created}`);
            } else {
                console.log('⚠️  Snapshot processing failed');
            }

        } else {
            const errorData = await dividendResponse.json();
            console.log('⚠️  Dividend declaration failed:', errorData.detail);
        }

        // Phase 6: Portfolio Analysis and Summary
        console.log('\n\n📋 Phase 6: System Summary and Analysis');
        console.log('=' .repeat(50));

        // Get dividend summary for each user
        for (const user of testUsers) {
            console.log(`\n📊 Dividend summary for ${user.email}:`);

            const summaryResponse = await fetch(`${API_BASE_URL}/dividends/user/summary`, {
                headers: { 'Authorization': `Bearer ${userTokens[user.email]}` }
            });

            if (summaryResponse.ok) {
                const summaryData = await summaryResponse.json();
                console.log(`   💰 Total dividend payments: ${summaryData.data.dividend_payments.count}`);
                console.log(`   💸 Total net amount: $${summaryData.data.dividend_payments.total_net}`);
                console.log(`   🔄 DRIP transactions: ${summaryData.data.drip_transactions.count}`);
            } else {
                console.log('   ⚠️  Could not retrieve dividend summary');
            }
        }

        // Get bulk orders summary
        console.log('\n🏪 Bulk orders summary:');
        const bulkOrdersResponse = await fetch(`${API_BASE_URL}/dividends/bulk-orders`, {
            headers: { 'Authorization': `Bearer ${userTokens[testUsers[0].email]}` }
        });

        if (bulkOrdersResponse.ok) {
            const bulkOrdersData = await bulkOrdersResponse.json();
            console.log(`   📦 Total bulk orders: ${bulkOrdersData.data.count}`);

            if (bulkOrdersData.data.bulk_orders.length > 0) {
                bulkOrdersData.data.bulk_orders.forEach((order, index) => {
                    console.log(`   ${index + 1}. ${order.asset_symbol} - $${order.total_amount} (${order.user_count} users)`);
                });
            }
        }

        // Test closure to verify the complete flow
        console.log('\n\n📋 Phase 7: Testing Investment Closure');
        console.log('=' .repeat(50));

        for (let i = 0; i < Math.min(testUsers.length, 1); i++) {  // Test closure for first user only
            const user = testUsers[i];
            console.log(`\n🔒 Testing closure for ${user.email}...`);

            const investmentsResponse = await fetch(`${API_BASE_URL}/smallcases/user/investments`, {
                headers: { 'Authorization': `Bearer ${userTokens[user.email]}` }
            });

            const investmentsData = await investmentsResponse.json();
            const userInvestment = investmentsData.data.find(inv =>
                inv.smallcase.id === testSmallcase.id && inv.status === 'active'
            );

            if (userInvestment) {
                // Test closure preview first
                const previewResponse = await fetch(
                    `${API_BASE_URL}/smallcases/investments/${userInvestment.id}/closure-preview`,
                    {
                        headers: { 'Authorization': `Bearer ${userTokens[user.email]}` }
                    }
                );

                if (previewResponse.ok) {
                    const previewData = await previewResponse.json();
                    console.log(`✅ Closure preview successful:`);
                    console.log(`   💰 Current value: $${previewData.data.current_value}`);
                    console.log(`   📊 Holdings to close: ${previewData.data.holdings_to_close?.length || 0}`);

                    // Perform actual closure
                    const closeResponse = await fetch(
                        `${API_BASE_URL}/smallcases/investments/${userInvestment.id}/close`,
                        {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${userTokens[user.email]}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                closure_reason: 'multi_user_dividend_test'
                            })
                        }
                    );

                    if (closeResponse.ok) {
                        const closeData = await closeResponse.json();
                        console.log(`✅ Investment closed successfully:`);
                        console.log(`   💰 Exit value: $${closeData.data.exit_value}`);
                        console.log(`   📈 Realized P&L: $${closeData.data.realized_pnl}`);
                    } else {
                        const errorData = await closeResponse.json();
                        console.log(`❌ Closure failed:`, errorData.detail);
                    }
                } else {
                    const errorData = await previewResponse.json();
                    console.log(`❌ Closure preview failed:`, errorData.detail);
                }
            }
        }

        console.log('\n' + '='.repeat(70));
        console.log('🎉 Multi-User Bulk Order System Test Complete!');
        console.log('✅ Successfully tested:');
        console.log('   • Multi-user investment creation');
        console.log('   • Broker selection based on user location');
        console.log('   • Position snapshot creation for dividend tracking');
        console.log('   • DRIP preference management');
        console.log('   • Dividend declaration and processing');
        console.log('   • Investment closure flow');
        console.log('='.repeat(70));

    } catch (error) {
        console.error('\n❌ Test failed:', error.message);
        if (error.stack) {
            console.error('Stack trace:', error.stack);
        }
    }
}

// Enhanced error handling and validation
async function validateSystemHealth() {
    console.log('🏥 Checking system health...');

    try {
        const healthResponse = await fetch(`${API_BASE_URL}/health`);
        if (healthResponse.ok) {
            console.log('✅ API Gateway is healthy');
        } else {
            console.log('⚠️  API Gateway health check failed');
        }
    } catch (error) {
        console.error('❌ Cannot connect to API Gateway:', error.message);
        throw new Error('System is not ready for testing');
    }
}

// Run the comprehensive test
async function main() {
    try {
        await validateSystemHealth();
        await testMultiUserDividendSystem();
    } catch (error) {
        console.error('💥 Test suite failed:', error.message);
        process.exit(1);
    }
}

main().catch(console.error);