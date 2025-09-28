
async function testClosure() {
  const loginResponse = await fetch("http://localhost:8000/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: "username=john.doe@example.com&password=password123"
  });
  const loginData = await loginResponse.json();
  const token = loginData.access_token || loginData.data?.access_token;
  
  const investmentsResponse = await fetch("http://localhost:8000/smallcases/user/investments", {
    headers: { "Authorization": `Bearer ${token}` }
  });
  const investmentsData = await investmentsResponse.json();
  const latestInvestment = investmentsData.data[0];
  
  console.log(`Testing closure for investment: ${latestInvestment.id}`);
  
  const closureResponse = await fetch(`http://localhost:8000/smallcases/investments/${latestInvestment.id}/closure-preview`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  
  if (closureResponse.ok) {
    const closureData = await closureResponse.json();
    console.log("✅ Closure preview successful\!");
    console.log(`💰 Current value: $${closureData.data.current_value}`);
    console.log(`📊 Holdings found: ${closureData.data.holdings_to_close?.length || "unknown"}`);
  } else {
    const errorData = await closureResponse.json();
    console.log("❌ Closure preview failed:", errorData);
  }
}
testClosure().catch(console.error);

