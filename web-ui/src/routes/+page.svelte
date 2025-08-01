<script>
    let alpacaAccount = null;
    let showAlpaca = false;
    let alpacaError = '';
    let alpacaLoading = false;

    async function loadAlpacaAccount() {
        alpacaLoading = true;
        alpacaError = '';
        alpacaAccount = null;
        try {
            const apiBase = import.meta.env.VITE_API_BASE_URL;
            const res = await fetch(`${apiBase}/alpaca/account`);
            if (!res.ok) throw new Error("Failed to fetch Alpaca account");
            alpacaAccount = await res.json();
            showAlpaca = true;
        } catch (err) {
            alpacaError = err.message;
        } finally {
            alpacaLoading = false;
        }
    }

    import { onMount } from 'svelte';
  
    let portfolio = [];
    let error = '';
    let loading = true;

    onMount(async () => {
        const apiBase = import.meta.env.VITE_API_BASE_URL;
    
        if (!apiBase) {
            error = "VITE_API_BASE_URL is not defined";
            loading = false;
            return;
        }

        try {
            const res = await fetch(apiBase + '/portfolio/status');
            if (!res.ok) throw new Error('Failed to load portfolio');
            portfolio = await res.json();
        } catch (err) {
            error = `Failed to fetch portfolio: ${err.message}`;
        } finally {
            loading = false;
        }
    });
  </script>
  
  
  <div class="h-screen grid grid-rows-[auto_1fr_auto] grid-cols-[200px_1fr_200px]">
    <!-- Top (Header) -->
    <header class="col-span-3 bg-gray-900 text-white p-4 text-2xl font-bold shadow">
      Saras Trading
    </header>
  
    <!-- Left Sidebar -->
    <aside class="row-span-1 bg-gray-100 p-4 border-r">
      <!-- Watchlist / Gainers / Losers -->
      <p class="font-semibold mb-2">Sidebar Left</p>
      <ul>
        <li>Watchlist</li>
        <li>Gainers</li>
        <li>Losers</li>
      </ul>
    </aside>
  
    <!-- Main Content -->
    <main class="bg-white p-4">
        <h2 class="text-xl font-semibold mb-4">Portfolio</h2>
        <button class="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700 mb-4"
            on:click={loadAlpacaAccount}>
            Show Alpaca Account
        </button>
        {#if showAlpaca}
          <button class="text-sm text-blue-600 mt-2" on:click={() => showAlpaca = false}>Hide</button>
        {/if}
        {#if error}
          <p class="text-red-500">{error}</p>
        {:else if portfolio.length === 0}
          <p>Loading portfolio...</p>
        {:else}
          <table class="table-auto w-full border">
            <thead>
              <tr class="bg-gray-100">
                <th class="px-4 py-2 border">Symbol</th>
                <th class="px-4 py-2 border">Quantity</th>
                <th class="px-4 py-2 border">Value</th>
              </tr>
            </thead>
            <tbody>
              {#each portfolio as item}
                <tr>
                  <td class="px-4 py-2 border">{item.symbol}</td>
                  <td class="px-4 py-2 border">{item.quantity}</td>
                  <td class="px-4 py-2 border">{item.value}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}

        {#if showAlpaca}
            <h2 class="text-xl font-semibold mt-8 mb-4">Alpaca Account Info</h2>

            {#if alpacaLoading}
                <p>Loading Alpaca account...</p>
            {:else if alpacaError}
                <p class="text-red-500">{alpacaError}</p>
            {:else if alpacaAccount}
            <table class="table-auto w-full border">
                <tbody>
                  <tr>
                    <td class="font-semibold">Account Number:</td>
                    <td>{alpacaAccount.account_number}</td>
                  </tr>
                  <tr>
                    <td class="font-semibold">Status:</td>
                    <td>{alpacaAccount.status}</td>
                  </tr>
                  <tr>
                    <td class="font-semibold">Buying Power:</td>
                    <td>{alpacaAccount.buying_power}</td>
                  </tr>
                  <tr>
                    <td class="font-semibold">Cash:</td>
                    <td>{alpacaAccount.cash}</td>
                  </tr>
                  <tr>
                    <td class="font-semibold">Equity:</td>
                    <td>{alpacaAccount.equity}</td>
                  </tr>
                </tbody>
              </table>            
            {/if}
        {/if}

      </main>
      
  
    <!-- Right Sidebar -->
    <aside class="row-span-1 bg-gray-50 p-4 border-l">
      <!-- News / Other Widgets -->
      <p class="font-semibold mb-2">Sidebar Right</p>
      <ul>
        <li>News Window</li>
        <li>Other widgets</li>
      </ul>
    </aside>
  
    <!-- Bottom (Charts) -->
    <footer class="col-span-3 bg-gray-200 p-4 text-center border-t">
      Charts and other summary info here
    </footer>
  </div>
  