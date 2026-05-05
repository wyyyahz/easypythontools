#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a JavaScript bookmarklet/script that runs in the Agoda browser tab
to automatically paginate through ALL search results via the GraphQL API.
"""
import json

script = '''
(async function() {
  // ========== STEP 1: Intercept the first graphql/search API call ==========
  const originalFetch = window.fetch;
  let firstRequest = null;
  let firstResponse = null;
  
  window.fetch = function(...args) {
    if (args[0] && args[0].includes && args[0].includes('graphql/search')) {
      const body = args[1]?.body || '';
      if (!firstRequest) {
        firstRequest = body;
      }
      return originalFetch.apply(this, args).then(async response => {
        const clone = response.clone();
        try {
          const data = await clone.json();
          if (!firstResponse) {
            firstResponse = data;
          }
          window.__lastApiData = data;
        } catch(e) {}
        return response;
      });
    }
    return originalFetch.apply(this, args);
  };
  
  // ========== STEP 2: Wait for initial data to load ==========
  console.log('Waiting for initial API response...');
  await new Promise(resolve => {
    let checkCount = 0;
    const check = () => {
      if (firstResponse || checkCount > 30) {
        resolve();
        return;
      }
      checkCount++;
      setTimeout(check, 500);
    };
    // Trigger scroll to force lazy load
    window.scrollTo(0, 500);
    check();
  });
  
  if (!firstResponse) {
    return {error: 'No API response captured after 15 seconds'};
  }
  
  // ========== STEP 3: Prepare the pagination template ==========
  const template = JSON.parse(firstRequest);
  const searchContext = template.variables.CitySearchRequest.searchRequest.searchContext;
  
  // Extract the total count
  const totalCount = firstResponse.data?.citySearch?.searchResult?.searchInfo?.totalCount || 
                     firstResponse.data?.citySearch?.aggregation?.totalCount || 0;
  
  console.log('Total hotels:', totalCount);
  
  // ========== STEP 4: Paginate through all results ==========
  const ALL_HOTELS = [];
  const SEEN_IDS = new Set();
  let pageToken = null;
  let pageNum = 1;
  const MAX_PAGES = Math.ceil((totalCount || 7214) / 11) + 10;
  let consecutiveEmpty = 0;
  
  function extractHotel(property) {
    if (!property || !property.content) return null;
    const info = property.content.informationSummary || {};
    const reviews = property.content.reviews?.cumulative;
    const pricing = property.pricing;
    const id = property.propertyId;
    
    if (!id || SEEN_IDS.has(id)) return null;
    SEEN_IDS.add(id);
    
    const name = info.localeName || info.defaultName || '';
    if (!name) return null;
    
    // Price
    let price = null;
    try {
      const offers = pricing?.offers || [];
      for (const offer of offers) {
        for (const ro of (offer.roomOffers || [])) {
          for (const p of (ro?.room?.pricing || [])) {
            const d = p?.price?.perBook?.inclusive?.display;
            if (d) { price = Math.round(d); break; }
          }
          if (price) break;
        }
        if (price) break;
      }
    } catch(e) {}
    
    // Rating
    let rating = null;
    if (reviews && reviews.score) rating = reviews.score;
    
    // Star rating from hotelCharacter or reviews
    let stars = '';
    const char = info.hotelCharacter;
    if (char) stars = char + '/5星';
    
    // Location
    let location = '';
    const addr = info.address || {};
    if (addr.area && addr.area.name) location = addr.area.name;
    else if (addr.city && addr.city.name) location = addr.city.name;
    
    return { name, stars, rating, price, location, id };
  }
  
  // Function to make a paginated API call
  async function fetchPage(pageNumber, token) {
    const page = {
      pageSize: 11,
      pageNumber: pageNumber
    };
    if (token) page.pageToken = token;
    
    const body = JSON.parse(JSON.stringify(template));
    body.variables.CitySearchRequest.searchRequest.page = page;
    body.variables.CitySearchRequest.searchRequest.searchContext.searchId = 
      'batch-' + Date.now() + '-' + pageNumber;
    
    const resp = await fetch('https://www.agoda.cn/graphql/search', {
      method: 'POST',
      headers: {
        'accept': '*/*',
        'content-type': 'application/json',
        'AG-LANGUAGE-LOCALE': 'zh-cn',
        'AG-CID': '-1',
        'AG-PAGE-TYPE-ID': '103',
        'AG-REQUEST-ATTEMPT': String(pageNumber)
      },
      body: JSON.stringify(body)
    });
    
    const data = await resp.json();
    const props = data?.data?.citySearch?.properties || [];
    const newToken = data?.data?.citySearch?.searchEnrichment?.pageToken;
    
    return { properties: props, nextToken: newToken, data: data };
  }
  
  // Start with the first response's data
  const firstProps = firstResponse.data?.citySearch?.properties || [];
  for (const p of firstProps) {
    const h = extractHotel(p);
    if (h) ALL_HOTELS.push(h);
  }
  
  // Get pageToken from the first response
  pageToken = firstResponse.data?.citySearch?.searchEnrichment?.pageToken;
  
  if (!pageToken) {
    return {error: 'No page token found', total: ALL_HOTELS.length, hotels: ALL_HOTELS};
  }
  
  // Fetch subsequent pages
  pageNum = 2;
  while (pageNum <= MAX_PAGES && pageToken) {
    try {
      const result = await fetchPage(pageNum, pageToken);
      
      if (result.properties.length === 0) {
        consecutiveEmpty++;
        if (consecutiveEmpty >= 3) break;
        pageNum++;
        continue;
      }
      consecutiveEmpty = 0;
      
      for (const p of result.properties) {
        const h = extractHotel(p);
        if (h) ALL_HOTELS.push(h);
      }
      
      pageToken = result.nextToken;
      pageNum++;
      
      if (pageNum % 50 === 0) {
        console.log('Page ' + pageNum + ': ' + ALL_HOTELS.length + ' hotels');
      }
      
      // Small delay to be respectful
      await new Promise(r => setTimeout(r, 200));
      
    } catch(e) {
      console.error('Error on page', pageNum, e);
      consecutiveEmpty++;
      if (consecutiveEmpty >= 3) break;
      pageNum++;
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  
  window.__allHotels = ALL_HOTELS;
  return {
    total: ALL_HOTELS.length,
    pagesFetched: pageNum - 1,
    totalOnSite: totalCount || 'unknown',
    reason: !pageToken ? 'No more page token' : (consecutiveEmpty >= 3 ? 'Empty pages' : 'Max pages'),
    sample: ALL_HOTELS.slice(0, 3)
  };
})();
'''

# Write the script to a file for reference
output = {
    "instructions": "Copy-paste the following into the browser console (F12) on the Agoda search results page",
    "script": script
}

print(json.dumps(output, ensure_ascii=False, indent=2))
