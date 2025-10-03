/**
 * Simple GTT Order Test - Direct API testing
 */

const BASE_URL = 'http://localhost:8000';

async function test() {
    console.log('🚀 Simple GTT Order Test\n');

    // Step 1: Login
    console.log('Step 1: Login');
    const formData = new URLSearchParams();
    formData.append('username', 'gtt_test@example.com');
    formData.append('password', 'Password123');

    const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    });

    const loginData = await loginResponse.json();
    const token = loginData.data.access_token;
    const userId = loginData.data.user.id;
    console.log(`✅ Logged in as ${userId}\n`);

    // Step 2: Get or create Zerodha broker connection (paper trading)
    console.log('Step 2: Get/Create Zerodha Paper Trading Connection');

    // First, try to get existing connections
    const getResponse = await fetch(`${BASE_URL}/brokers/connections`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    const existingData = await getResponse.json();
    const existingConnections = existingData.data || [];

    // Find existing Zerodha paper trading connection
    let brokerConnectionId = null;
    const zerodhaConnection = existingConnections.find(c =>
        c.broker_type === 'zerodha' && c.paper_trading
    );

    if (zerodhaConnection) {
        brokerConnectionId = zerodhaConnection.id;
        console.log(`✅ Using existing connection: ${brokerConnectionId}\n`);
    } else {
        // Create new connection
        const brokerResponse = await fetch(`${BASE_URL}/brokers/connections`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                broker_type: 'zerodha',
                api_key: process.env.ZERODHA_API_KEY || 'test_key',
                api_secret: process.env.ZERODHA_SECRET_KEY || 'test_secret',
                access_token: 'paper_trading_token',
                paper_trading: false, 
                alias: `Zerodha Paper ${Date.now()}`
            })
        });

        if (!brokerResponse.ok) {
            const error = await brokerResponse.text();
            console.error('❌ Failed to create broker connection:', error);
            return;
        }

        const brokerData = await brokerResponse.json();
        brokerConnectionId = brokerData.data?.id || brokerData.id;
        console.log(`✅ Broker connection created: ${brokerConnectionId}\n`);
    }

    if (!brokerConnectionId) {
        console.error('❌ No broker connection available');
        return;
    }

    // Step 3: Place GTT Order
    console.log('Step 3: Place GTT Order');
    const gttResponse = await fetch(`${BASE_URL}/orders/gtt/place`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            broker_connection_id: brokerConnectionId,
            symbol: 'RELIANCE',
            side: 'BUY',
            quantity: 10,
            trigger_price: 2500.00,
            limit_price: 2505.00,
            trigger_type: 'single',
            product: 'CNC'
        })
    });

    if (!gttResponse.ok) {
        const error = await gttResponse.text();
        console.error('❌ Failed to place GTT order:', error);
        return;
    }

    const gttData = await gttResponse.json();
    console.log('✅ GTT Order placed successfully!');
    console.log(JSON.stringify(gttData.data, null, 2));
    console.log();

    // Step 4: List GTT Orders
    console.log('Step 4: List GTT Orders');
    const listResponse = await fetch(
        `${BASE_URL}/orders/gtt/list?broker_connection_id=${brokerConnectionId}`,
        {
            headers: { 'Authorization': `Bearer ${token}` }
        }
    );

    if (!listResponse.ok) {
        const error = await listResponse.text();
        console.error('❌ Failed to list GTT orders:', error);
    } else {
        const listData = await listResponse.json();
        const orders = listData.data || [];
        console.log(`✅ Found ${orders.length} GTT orders`);
        console.log(JSON.stringify(orders, null, 2));
    }
    console.log();

    // Step 5: Place Basket Order
    console.log('Step 5: Place Basket Order');
    const basketResponse = await fetch(`${BASE_URL}/orders/gtt/basket/place`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            broker_connection_id: brokerConnectionId,
            orders: [
                {
                    symbol: 'TCS',
                    side: 'BUY',
                    quantity: 5,
                    order_type: 'MARKET',
                    product: 'CNC'
                },
                {
                    symbol: 'INFY',
                    side: 'BUY',
                    quantity: 10,
                    order_type: 'MARKET',
                    product: 'CNC'
                }
            ]
        })
    });

    if (!basketResponse.ok) {
        const error = await basketResponse.text();
        console.error('❌ Failed to place basket order:', error);
    } else {
        const basketData = await basketResponse.json();
        console.log('✅ Basket Order placed successfully!');
        console.log(JSON.stringify(basketData.data, null, 2));
    }
    console.log();

    // Step 6: Place OCO Order
    console.log('Step 6: Place OCO Order');
    const ocoResponse = await fetch(`${BASE_URL}/orders/gtt/oco/place`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            broker_connection_id: brokerConnectionId,
            symbol: 'BHARTIARTL',
            side: 'SELL',
            quantity: 30,
            target_price: 920.00,
            stop_loss_price: 850.00,
            product: 'CNC'
        })
    });

    const ocoData = await ocoResponse.json();
    console.log('✅ OCO Order placed successfully!');
    console.log(JSON.stringify(ocoData.data, null, 2));
    console.log();

    console.log('🎉 All GTT tests passed successfully!');
}

test().catch(err => {
    console.error('❌ Test failed:', err.message);
    process.exit(1);
});
