<script>
    let activePage = "Trading";
  </script>
  
  <aside class="w-56 h-full bg-[#1E1E2D] text-white flex flex-col">
    <div class="text-2xl font-bold px-4 py-6 border-b border-gray-700">
      <div class="flex items-center space-x-2">
        <span class="bg-blue-600 px-2 py-1 rounded">\u25B2</span>
        <span>TradePro</span>
      </div>
    </div>
  
    <nav class="flex-1 px-4 py-4 space-y-2 text-sm">
      <div class="cursor-pointer px-3 py-2 rounded hover:bg-gray-700" class:bg-blue-700={activePage === 'Dashboard'}>Dashboard</div>
      <div class="cursor-pointer px-3 py-2 rounded hover:bg-gray-700" class:bg-blue-700={activePage === 'Portfolio'}>Portfolio</div>
      <div class="cursor-pointer px-3 py-2 rounded bg-blue-700">Trading</div>
      <div class="cursor-pointer px-3 py-2 rounded hover:bg-gray-700">Algorithms</div>
      <div class="cursor-pointer px-3 py-2 rounded hover:bg-gray-700">Strategies</div>
      <div class="cursor-pointer px-3 py-2 rounded hover:bg-gray-700">Analytics</div>
      <div class="cursor-pointer px-3 py-2 rounded hover:bg-gray-700">Settings</div>
    </nav>
  </aside>
  
  <style>
    aside div.active {
      background-color: #2563EB; /* Tailwind blue-600 */
    }
  </style>
  