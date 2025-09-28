
async function checkInvestments() {
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
  
  console.log("📊 Current investments:", JSON.stringify(investmentsData, null, 2));
}
checkInvestments().catch(console.error);

