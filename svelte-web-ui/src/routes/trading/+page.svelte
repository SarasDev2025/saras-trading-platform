/* File: src/routes/trading/+page.svelte */
<script>
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  import Header from '$lib/components/layout/Header.svelte';
//   import PlaceOrder from '$lib/components/trading/PlaceOrder.svelte';
//   import MarketData from '$lib/components/trading/MarketData.svelte';
//   import OrderTabs from '$lib/components/trading/OrderTabs.svelte';
</script>

<div class="flex h-screen bg-gray-900 text-white">
  <Sidebar />
  <div class="flex flex-col flex-1">
    <Header title="Trading" subtitle="Execute trades and manage orders" />
    <main class="flex flex-1 gap-4 p-6 bg-gray-900 overflow-hidden">
      <div class="flex flex-col gap-4 w-full max-w-sm">
        <!-- <PlaceOrder />
        <MarketData /> -->
      </div>
      <div class="flex-1">
        <!-- <OrderTabs /> -->
      </div>
    </main>
  </div>
</div>
