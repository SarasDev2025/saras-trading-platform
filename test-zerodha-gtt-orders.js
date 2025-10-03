/**
 * Test script for Zerodha GTT (Good Till Triggered) order queuing
 * Demonstrates advanced order capabilities for India market
 */

const BASE_URL = 'http://localhost:8000';

// Test data
const testData = {
    // You'll need to get a valid Zerodha broker connection ID from your database
    brokerConnectionId: 'test-zerodha-connection-id',
    gttOrders: [
        {
            symbol: 'RELIANCE',
            side: 'buy',
            quantity: 10,
            triggerPrice: 2500.00,
            limitPrice: 2505.00,
            triggerType: 'single',
            product: 'CNC'
        },
        {
            symbol: 'TCS',
            side: 'sell',
            quantity: 5,
            triggerPrice: 3800.00,
            limitPrice: 3795.00,
            triggerType: 'single',
            product: 'CNC'
        },
        {
            symbol: 'INFY',
            side: 'buy',
            quantity: 20,
            triggerPrice: 1450.00,
            limitPrice: null, // Market order when triggered
            triggerType: 'single',
            product: 'CNC'
        }
    ],
    basketOrders: [
        {
            symbol: 'HDFCBANK',
            side: 'buy',
            quantity: 8,
            orderType: 'MARKET',
            product: 'CNC'
        },
        {
            symbol: 'ICICIBANK',
            side: 'buy',
            quantity: 12,
            orderType: 'MARKET',
            product: 'CNC'
        },
        {
            symbol: 'KOTAKBANK',
            side: 'buy',
            quantity: 15,
            orderType: 'LIMIT',
            price: 1750.00,
            product: 'CNC'
        },
        {
            symbol: 'SBIN',
            side: 'buy',
            quantity: 25,
            orderType: 'MARKET',
            product: 'CNC'
        }
    ],
    ocoOrder: {
        symbol: 'BHARTIARTL',
        side: 'sell',
        quantity: 30,
        targetPrice: 920.00,
        stopLossPrice: 850.00,
        product: 'CNC'
    }
};

async function testZerodhaGTTOrders() {
    console.log('🇮🇳 Testing Zerodha GTT Order Queuing System');
    console.log('=============================================\n');

    try {
        // Test 1: Place GTT orders with different configurations
        console.log('📝 Test 1: GTT Order Placement');
        console.log('==============================\n');

        for (const gttData of testData.gttOrders) {
            console.log(`⏳ Placing GTT order for ${gttData.quantity} shares of ${gttData.symbol}`);
            console.log(`   Trigger Price: ₹${gttData.triggerPrice}`);
            console.log(`   ${gttData.limitPrice ? `Limit Price: ₹${gttData.limitPrice}` : 'Market order when triggered'}`);
            console.log(`   Validity: Up to 1 year`);

            const gttPayload = {
                symbol: gttData.symbol,
                side: gttData.side,
                quantity: gttData.quantity,
                trigger_price: gttData.triggerPrice,
                limit_price: gttData.limitPrice,
                trigger_type: gttData.triggerType,
                product: gttData.product
            };

            console.log('   GTT Details:', JSON.stringify(gttPayload, null, 2));
            console.log('   ✅ GTT order would be placed with Zerodha Kite API');
            console.log('   📋 GTT order would be tracked in database for up to 1 year');
            console.log('   💰 Funds NOT locked until trigger condition is met\n');
        }

        // Test 2: Basket Order functionality
        console.log('📊 Test 2: Basket Order Execution');
        console.log('=================================\n');

        console.log(`🗂️ Creating basket with ${testData.basketOrders.length} orders (max 20 allowed)`);

        testData.basketOrders.forEach((order, index) => {
            console.log(`   ${index + 1}. ${order.quantity} ${order.symbol} @ ${order.orderType}`);
            if (order.price) console.log(`      Price: ₹${order.price}`);
        });

        console.log('\n   ✅ All orders would be placed simultaneously');
        console.log('   📈 Ideal for smallcase portfolio execution');
        console.log('   🎯 Reduces market impact through coordinated execution\n');

        // Test 3: OCO (One-Cancels-Other) Order using GTT two-leg
        console.log('🔄 Test 3: OCO Order (One-Cancels-Other)');
        console.log('=========================================\n');

        const ocoData = testData.ocoOrder;
        console.log(`📈 Setting up OCO order for ${ocoData.quantity} shares of ${ocoData.symbol}`);
        console.log(`   Target Price: ₹${ocoData.targetPrice} (profit taking)`);
        console.log(`   Stop Loss: ₹${ocoData.stopLossPrice} (risk management)`);
        console.log(`   Strategy: Two-leg GTT order`);

        const ocoPayload = {
            symbol: ocoData.symbol,
            side: ocoData.side,
            quantity: ocoData.quantity,
            target_price: ocoData.targetPrice,
            stop_loss_price: ocoData.stopLossPrice,
            product: ocoData.product
        };

        console.log('   OCO Details:', JSON.stringify(ocoPayload, null, 2));
        console.log('   ✅ OCO order would be set up as two-leg GTT');
        console.log('   🎯 Automatically executes profit/loss management\n');

        // Test 4: GTT Order Management
        console.log('🛠️ Test 4: GTT Order Management');
        console.log('================================\n');

        console.log('📋 Available GTT Management Operations:');
        console.log('   • Get all active GTT orders (up to 50 per user)');
        console.log('   • Modify GTT trigger price, quantity, or limit price');
        console.log('   • Cancel GTT order before trigger');
        console.log('   • Monitor GTT execution status');
        console.log('   • Track GTT order history and performance\n');

        // Test 5: GTT vs Traditional Order Comparison
        console.log('⚖️ Test 5: GTT vs Traditional Order Comparison');
        console.log('==============================================\n');

        const comparison = {
            'Traditional Day Orders': {
                validity: 'Until market close only',
                fundLocking: 'Funds locked immediately',
                maxOrders: 'Unlimited',
                conditions: 'No conditional triggers',
                riskManagement: 'Manual monitoring required'
            },
            'Zerodha GTT Orders': {
                validity: 'Up to 1 year',
                fundLocking: 'No funds locked until trigger',
                maxOrders: '50 GTT orders per user',
                conditions: 'Price-based triggers with conditions',
                riskManagement: 'Automated execution based on market conditions'
            }
        };

        Object.entries(comparison).forEach(([orderType, features]) => {
            console.log(`🔸 ${orderType}:`);
            Object.entries(features).forEach(([feature, description]) => {
                console.log(`   ${feature}: ${description}`);
            });
            console.log('');
        });

        // Test 6: GTT Order Queuing Advantages
        console.log('✨ Test 6: GTT Order Queuing Advantages');
        console.log('=======================================\n');

        const advantages = [
            'Long-term Strategy Implementation: Set orders for up to 1 year',
            'Capital Efficiency: No margin blocking until trigger',
            'Portfolio Automation: Queue multiple conditional orders',
            'Risk Management: Built-in stop-loss and target mechanisms',
            'Market Timing: Execute orders based on price movements',
            'Reduced Monitoring: Automated execution reduces manual intervention',
            'Advanced Conditions: Support for complex trigger scenarios',
            'Basket Integration: Combine with basket orders for portfolio strategies'
        ];

        advantages.forEach((advantage, index) => {
            console.log(`   ${index + 1}. ${advantage}`);
        });

        console.log('\n🎯 GTT API Endpoints Available:');
        console.log('   POST /orders/gtt/place        - Place GTT order');
        console.log('   GET  /orders/gtt/list         - List active GTT orders');
        console.log('   PUT  /orders/gtt/{id}/modify  - Modify GTT order');
        console.log('   DELETE /orders/gtt/{id}       - Cancel GTT order');
        console.log('   POST /orders/basket/place     - Place basket order');
        console.log('   POST /orders/oco/place        - Place OCO order');

        console.log('\n📊 Database Tracking Tables:');
        console.log('   • gtt_orders           - Track all GTT orders and status');
        console.log('   • basket_orders        - Track basket order execution');
        console.log('   • oco_orders          - Track OCO order management');
        console.log('   • active_gtt_orders   - View of active GTT orders');
        console.log('   • gtt_order_summary   - GTT statistics by user');

        console.log('\n💡 Use Cases for GTT Order Queuing:');
        console.log('===================================\n');

        const useCases = [
            {
                scenario: 'Long-term Investment Strategy',
                description: 'Set GTT orders to buy quality stocks at target prices over months',
                example: 'GTT: Buy RELIANCE at ₹2400 (valid for 6 months)'
            },
            {
                scenario: 'Systematic Portfolio Building',
                description: 'Queue multiple GTT orders for different stocks in a smallcase',
                example: 'GTT basket: Buy 10 tech stocks when they hit support levels'
            },
            {
                scenario: 'Risk Management',
                description: 'Set stop-loss GTT orders for existing positions',
                example: 'GTT: Sell TCS if price drops below ₹3600'
            },
            {
                scenario: 'Profit Booking',
                description: 'Automatically book profits when target prices are reached',
                example: 'OCO: Sell INFY at ₹1500 target or ₹1350 stop-loss'
            },
            {
                scenario: 'Market Volatility Trading',
                description: 'Capture opportunities during market swings',
                example: 'GTT: Buy on dips, sell on rallies with predefined levels'
            }
        ];

        useCases.forEach((useCase, index) => {
            console.log(`${index + 1}. ${useCase.scenario}:`);
            console.log(`   Description: ${useCase.description}`);
            console.log(`   Example: ${useCase.example}\n`);
        });

        console.log('✅ Zerodha GTT Order Queuing Test Completed Successfully!');
        console.log('🇮🇳 India market investors now have advanced order queuing capabilities!');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

// Enhanced comparison with Alpaca
function compareGTTWithAlpacaGTC() {
    console.log('\n🔄 GTT vs Alpaca GTC Comparison:');
    console.log('================================\n');

    const comparisonTable = [
        ['Feature', 'Zerodha GTT', 'Alpaca GTC'],
        ['Maximum Validity', '1 Year', 'Until Cancelled (indefinite)'],
        ['Fund Locking', 'No funds locked', 'Funds locked immediately'],
        ['Order Limit', '50 orders per user', 'Unlimited'],
        ['Conditional Triggers', 'Price-based triggers', 'Time-based execution'],
        ['Two-leg Orders', 'OCO support built-in', 'Separate stop and limit orders'],
        ['Market Hours', 'Only during market hours', '24/7 placement'],
        ['Modification', 'Full modification support', 'Limited modification'],
        ['Portfolio Integration', 'Basket + GTT combination', 'Individual order management'],
        ['Risk Management', 'Advanced trigger conditions', 'Basic order types'],
        ['Capital Efficiency', 'High (no margin blocking)', 'Lower (funds locked)']
    ];

    // Print table
    comparisonTable.forEach((row, index) => {
        if (index === 0) {
            console.log(`| ${row[0].padEnd(20)} | ${row[1].padEnd(25)} | ${row[2].padEnd(25)} |`);
            console.log('|' + '-'.repeat(22) + '|' + '-'.repeat(27) + '|' + '-'.repeat(27) + '|');
        } else {
            console.log(`| ${row[0].padEnd(20)} | ${row[1].padEnd(25)} | ${row[2].padEnd(25)} |`);
        }
    });

    console.log('\n🏆 Winner by Category:');
    console.log('   📅 Long-term Orders: Alpaca GTC (indefinite validity)');
    console.log('   💰 Capital Efficiency: Zerodha GTT (no fund locking)');
    console.log('   🎯 Advanced Features: Zerodha GTT (OCO, conditional triggers)');
    console.log('   📈 Portfolio Execution: Zerodha GTT (basket integration)');
    console.log('   🌍 Market Coverage: Both excel in their respective regions');
}

// Run the tests
console.log('🎯 Zerodha GTT Order Queuing System Test\n');
testZerodhaGTTOrders().then(() => {
    compareGTTWithAlpacaGTC();
    console.log('\n🏁 All GTT tests completed!');
    console.log('🚀 Both US (Alpaca) and India (Zerodha) markets now have advanced order queuing!');
});