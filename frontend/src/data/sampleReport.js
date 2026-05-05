/**
 * Sample report payload mirroring the FullReport shape from
 * `backend/models.py`. Used by the /report-preview route so the report UI
 * can be exercised without hitting the live pipeline.
 *
 * The pipeline composes two sources:
 *   - product scraping (ScrapingBee) → section_1, section_3.comparison_table
 *   - review scraping  (Apify)        → section_5, with section_2/3/4 derived
 *                                       from the reviews via Groq LLM calls
 *
 * `image_url` is added here even though it isn't in the raw response so the
 * preview shows real thumbnails. Live runs will populate it from the scraper.
 */

export const sampleReport = {
  run_id: '071de0fb-f7e8-4576-9197-48a17e63c0f0',
  your_asin: 'B0FMDL81GS',
  competitor_asins: ['B0BW8TXJJ2'],
  created_at: '2026-05-04T17:28:17.456836',

  // ── Section 1: scraped product metadata ──────────────────────────────
  section_1: {
    products: [
      {
        asin: 'B0FMDL81GS',
        title:
          'OnePlus Nord Buds 3r TWS Earbuds up to 54 Hours Playback, 2-mic Clear Calls, 3D Spatial Audio, AI Translation, 12.4mm Drivers, Dual-Device Connectivity, 47ms Low Latency - Ash Black',
        price: null,
        currency: null,
        star_rating: 4.3,
        total_reviews: 43581,
        bsr: '#3 in Electronics',
        bullet_points: [
          '[Our longest battery ever, up to 54 hrs Music Playback]: A full charge Nord Buds 3r gives upto 54 hours of music playback. 10 minutes of fast charging gives 8 hours of music.',
          '[Titanium-coated Drivers]: The Nord buds 3r comes with 12.4 mm Titanium-coated Drivers to enjoy deeper bass and powerful beats resulting in crystal - clear details in every note. It has fixed spatial audio specifically for OnePlus smartphone users.',
          '[2-mic AI Call Noise Cancellation]: - Powered by AI call noise cancellation algorithm and anti-wind design, our call noise cancellation system excels at preserving human voice clarity while effectively suppressing high-frequency dynamic noise and wind interference in phone calls.',
          '[AI Translation]: Simply tap your earbuds to activate AI Translation via your OnePlus phone and communicate with foreigners smoothly without barriers. [Dual Connection & Google Fast Pair]: The buds can simultaneously connect to two devices such as Android/iOS/Windows smartphone, tablets or computers allowing for quick and seamless device switching. Google Fast Pair simplifies the pairing process, saves time and enhance user convenience.',
          '[Bluetooth & Latency]: New generation of Bluetooth 5.4 enables faster transmission of high-quality audio, providing a better audio experience. It also has 47ms low latency for better gaming.',
          'Charging Cable not inluded in box',
        ],
        specifications: {
          'Brand Name': 'OnePlus',
          'Model Number': 'E517A',
          'Model Name': 'OnePlus Nord Buds 3r',
          'Box Contents': '3N Eartip, Safety & Warranty card, User Manual',
          'Age Range Description': 'Teen, Adult',
          'Country of Origin': 'Vietnam',
          'Warranty Description': '1 year',
          'Number of Items': '1',
          'Series Number': '3',
          'Item Type Name': 'Ear buds',
          'Best Sellers Rank': '#3 in Electronics (See Top 100 in Electronics)#2 inIn-Ear Headphones',
          ASIN: 'B0FMDL81GS',
          'Customer Reviews': '4.34.3 out of 5 stars(43,581)4.3 out of 5 stars',
        },
        product_url: 'https://www.amazon.in/dp/B0FMDL81GS',
        image_url: 'https://picsum.photos/seed/oneplus-nord-buds-3r/320/320',
        scraped_at: '2026-05-04T17:26:44.352159',
      },
      {
        asin: 'B0BW8TXJJ2',
        title:
          'Boat Nirvana Ion, 120HRS Battery, Crystal Bionic Sound w/Dual EQ Modes, 4Mics ENx, App Support, Low Latency, IPX4, v.5.2 Bluetooth Earbuds, TWS Ear Buds Wireless Earphones with mic (Charcoal Black)',
        price: null,
        currency: null,
        star_rating: 4.1,
        total_reviews: 13278,
        bsr: '#50 in Electronics',
        bullet_points: [
          'Playback- boAt Nirvana Ion comes with a massive playback of 120 hours including 24 hours of playback per charge',
          'Crystal Bionic Sound with Dual Modes- These true wireless earbuds have Crystal Bionic Sound powered by Hifi DSP 5 which support dual eq modes: boAt Signature Sound and boAt Balanced Sound',
          'Clear Voice Calls- Nirvana Ion comes with 4 mics ENx Technology which helps block unwanted noise and make sure your voice gets delivered clearly while you are on your calls',
          'Low Latency- These earbuds are equipped with Beast Mode which offer low latency of 60ms removing any kind of lag during your gaming sessions',
          'In Ear Detection- The tws earbuds come with in ear detection, just plug the earbuds in your ears to resume music and pull them out for them to pause',
          'Patented Pocketable Design- The ergonomically compact size of the Nirvana Ion lets you fit them anywhere in your pocket or bag. So carry your music along, everywhere you go',
          'IP Rating- Its IPX4 rating make them an ideal fit for your workouts as it keeps them sweat free.',
          'Bluetooth Version- Live a truly wireless life with the most advanced BT 5.2 technology. Enjoy flawless, uninterrupted and smooth delivery of music.',
        ],
        specifications: {
          'Brand Name': 'boAt',
          'Model Number': 'Nirvana',
          'Model Name': 'Nirvana ION',
          'Box Contents': '1 x Earbuds, 1 x Charging Case, 1 x Extra Ear Tips, 1 x Charging Cable, 1 x User Manual, 1 x Warranty Card',
          'Age Range Description': 'Adult',
          'Country of Origin': 'India',
          'Warranty Description': '1 Year warranty from the date of purchase',
          'Number of Items': '1',
          'Item Type Name': 'True Wireless Earbuds',
          'Best Sellers Rank': '#50 in Electronics (See Top 100 in Electronics)#19 inIn-Ear Headphones',
          ASIN: 'B0BW8TXJJ2',
          'Customer Reviews': '4.14.1 out of 5 stars(13,278)4.1 out of 5 stars',
        },
        product_url: 'https://www.amazon.in/dp/B0BW8TXJJ2',
        image_url: 'https://picsum.photos/seed/boat-nirvana-ion/320/320',
        scraped_at: '2026-05-04T17:26:13.008201',
      },
    ],
  },

  // ── Section 2: per-product LLM summaries ─────────────────────────────
  section_2: {
    summaries: [
      {
        asin: 'B0FMDL81GS',
        product_title:
          'OnePlus Nord Buds 3r TWS Earbuds up to 54 Hours Playback, 2-mic Clear Calls, 3D Spatial Audio, AI Translation, 12.4mm Drivers, Dual-Device Connectivity, 47ms Low Latency - Ash Black',
        strengths: [
          'Good sound quality',
          'Long battery life',
          'Comfortable fit',
          'Durable design',
          'Affordable price',
        ],
        weaknesses: [
          'No Active Noise Cancellation (ANC)',
          'Bass can be too heavy for some users',
          'Limited app features compared to premium buds',
          'Some users experience ear pain due to shape',
          'No premium sound tuning',
        ],
        top_complaints: ['No Active Noise Cancellation (ANC)'],
        top_praises: ['Good sound quality'],
        overall_reaction:
          'Customers are generally satisfied with the OnePlus Nord Buds 3R, praising their sound quality, battery life, and comfortable fit, but some users experience issues with noise cancellation and ear pain.',
      },
      {
        asin: 'B0BW8TXJJ2',
        product_title:
          'Boat Nirvana Ion, 120HRS Battery, Crystal Bionic Sound w/Dual EQ Modes, 4Mics ENx, App Support, Low Latency, IPX4, v.5.2 Bluetooth Earbuds, TWS Ear Buds Wireless Earphones with mic (Charcoal Black)',
        strengths: ['Long battery life', 'Good sound quality', 'Value for money'],
        weaknesses: ['Poor mic functionality', 'Uncomfortable design', 'Build quality issues'],
        top_complaints: ['Poor sound quality'],
        top_praises: ['Long battery life'],
        overall_reaction:
          'Customers have mixed reactions to the product, with some praising its battery life and sound quality, while others criticize its mic functionality, design, and build quality.',
      },
    ],
  },

  // ── Section 3: comparison + structured spec table ────────────────────
  section_3: {
    comparison: {
      your_product_advantages: [
        'Good sound quality with 12.4mm drivers',
        'Long battery life of up to 54 hours',
        'Advanced features like 3D spatial audio and AI translation',
      ],
      competitor_advantages: [
        {
          asin: 'B0BW8TXJJ2',
          product_title:
            'Boat Nirvana Ion, 120HRS Battery, Crystal Bionic Sound w/Dual EQ Modes, 4Mics ENx, App Support, Low Latency, IPX4, v.5.2 Bluetooth Earbuds, TWS Ear Buds Wireless Earphones with mic (Charcoal Black)',
          advantages: ['Long battery life of 120 hours', 'Value for money'],
        },
      ],
      market_gaps: [
        'Active Noise Cancellation (ANC) is not available in either product',
        'Premium sound tuning is lacking in both products',
        'Build quality and durability concerns are present in the competitor product',
      ],
      overall_ranking: [
        'The OnePlus Nord Buds 3r TWS Earbuds is ranked 1 due to its good sound quality, long battery life, and advanced features.',
        'The Boat Nirvana Ion is ranked 2 due to its long battery life and value for money, but is held back by poor mic functionality and build quality issues.',
      ],
    },
    comparison_table: [
      {
        property: 'Brand Name',
        values: { B0FMDL81GS: 'OnePlus', B0BW8TXJJ2: 'boAt' },
      },
      {
        property: 'Model Name',
        values: { B0FMDL81GS: 'OnePlus Nord Buds 3r', B0BW8TXJJ2: 'Nirvana ION' },
      },
      {
        property: 'Battery Life',
        values: { B0FMDL81GS: 'up to 54 hours', B0BW8TXJJ2: '120 hours' },
      },
      {
        property: 'Number of Mics',
        values: { B0FMDL81GS: '2', B0BW8TXJJ2: '4' },
      },
      {
        property: 'Country of Origin',
        values: { B0FMDL81GS: 'Vietnam', B0BW8TXJJ2: 'India' },
      },
      {
        property: 'Rating',
        values: { B0FMDL81GS: '4.3', B0BW8TXJJ2: '4.1' },
      },
      {
        property: 'Review Count',
        values: { B0FMDL81GS: '43581', B0BW8TXJJ2: '13278' },
      },
    ],
  },

  // ── Section 4: prioritized recommendations ───────────────────────────
  section_4: {
    recommendations: {
      recommendations: [
        {
          priority: 'high',
          area: 'product',
          action:
            'Integrate Active Noise Cancellation (ANC) technology into the product to address the market gap and enhance user experience.',
          rationale:
            'The competitive analysis highlights the lack of ANC in both products as a market gap, and adding this feature can be a key differentiator.',
        },
        {
          priority: 'high',
          area: 'product',
          action:
            'Collaborate with audio experts to implement premium sound tuning and improve the overall sound quality of the product.',
          rationale:
            'The competitive analysis identifies the lack of premium sound tuning as a market gap, and addressing this can help the product stand out in terms of sound quality.',
        },
        {
          priority: 'high',
          area: 'product',
          action:
            'Invest in improving the microphone functionality to address customer complaints and enhance the overall user experience.',
          rationale:
            'The competitive analysis mentions poor mic functionality as a drawback of the competitor product, and improving this aspect can be a key differentiator and competitive advantage.',
        },
        {
          priority: 'medium',
          area: 'listing',
          action:
            'Emphasize the advanced features like 3D spatial audio and AI translation in the product listing to better showcase its unique selling points.',
          rationale:
            'The competitive analysis shows that the product has advanced features, but the listing may not be effectively communicating these advantages to potential customers.',
        },
        {
          priority: 'medium',
          area: 'pricing',
          action:
            'Conduct a price analysis to determine if the product is competitively priced, considering the value for money offered by the competitor product.',
          rationale:
            'The competitor product is noted for its value for money, so it\'s essential to assess the pricing strategy to ensure the product remains competitive.',
        },
        {
          priority: 'medium',
          area: 'listing',
          action:
            'Highlight the long battery life of up to 54 hours in the product listing, as this is a key advantage over other products.',
          rationale:
            'The competitive analysis shows that the product has a long battery life, which is a significant selling point that should be prominently featured in the listing.',
        },
        {
          priority: 'low',
          area: 'listing',
          action:
            'Update the product listing to include more detailed information about the build quality and durability of the product to alleviate customer concerns.',
          rationale:
            'While build quality and durability concerns are more prominent with the competitor product, proactively addressing these aspects can help build trust with potential customers.',
        },
      ],
    },
  },

  // ── Section 5: review samples ────────────────────────────────────────
  section_5: {
    samples: [
      {
        asin: 'B0FMDL81GS',
        product_title:
          'OnePlus Nord Buds 3r TWS Earbuds up to 54 Hours Playback, 2-mic Clear Calls, 3D Spatial Audio, AI Translation, 12.4mm Drivers, Dual-Device Connectivity, 47ms Low Latency - Ash Black',
        five_star: [
          {
            rating: 5,
            title: 'Marvellous, awe inspiring, built like steel — GO FOR IT!',
            text: "Alright everyone, please read this review carefully as it's 6 July 2025 today and on the 23rd of August 2025, I will have spent 2 years using these awesome and marvellous earbuds. These have been 2 years of extreme, rigorous and very careless usage and these earphones are still in prime condition. I'm an avid consumer of music — I wear my earbuds almost all day long, in the gym, while running, they've seen a lot of sweat, a lot of earwax. Most days I fall asleep wearing them and wake up with them on the floor. After all of this they're still in prime condition. The mic on these works extremely well, they charge pretty quickly, the box takes a little longer to fully charge but lasts a long time. Call quality, voice quality, everything is awesome. Their response to your touch is also durable. After 2 years their battery life isn't quite as good as new, but the sound quality and durability are still 90% of what they were. Best in class, marvel of engineering — over and out.",
            date: '2025-07-06',
            verified_purchase: true,
          },
          {
            rating: 5,
            title: 'Earbuds nord',
            text: "The audio is clear and the bass quality is perfect. While the noise cancellation is a bit weak, the battery lasts a long time. I only need to charge it every couple of 2 to 3 days. It's not the slimmest device, but the quality is high and it has a very durable, sturdy design. I'll buy again. Thanks Amazon.",
            date: '2026-04-25',
            verified_purchase: true,
          },
          {
            rating: 5,
            title: 'Super earbuds!',
            text: 'The product is so great with clear sound and good bass that I purchased 2 of them. One for me and one for my spouse. Definitely recommend this highly to everyone.',
            date: '2026-04-29',
            verified_purchase: true,
          },
        ],
        one_star: [],
      },
      {
        asin: 'B0BW8TXJJ2',
        product_title:
          'Boat Nirvana Ion, 120HRS Battery, Crystal Bionic Sound w/Dual EQ Modes, 4Mics ENx, App Support, Low Latency, IPX4, v.5.2 Bluetooth Earbuds, TWS Ear Buds Wireless Earphones with mic (Charcoal Black)',
        five_star: [
          {
            rating: 5,
            title: 'Excellent product',
            text: "I don't usually write reviews, but this product has forced me to. I bought this in August 2023 for around Rs. 2300. I don't usually spend more than 1k on earbuds but I was looking for good battery backup at the time. Seriously, this is my best buy till date in earbuds. I use it daily, almost 3 years now. Battery backup is still excellent and sound is also good.",
            date: '2026-04-06',
            verified_purchase: true,
          },
          {
            rating: 5,
            title: 'Bought it for the battery, got more',
            text: 'Let me start with the elephant in the room — 24 hour battery backup from buds alone. I received this TWS at 6:45 in the evening. Paired them with my phone, found 100% charge, started using them. I initiated my testing at 7 p.m. with The Jurassic Park (1993) at about 80% volume. 2 hours later, the buds had ~93% charge left. I watched the sequel — 11:10 p.m., left bud 86%, right 85%. Decided to push it. I rushed to YouTube, searched for a 10 hour heavy metal video, hit play at 100% volume, called it a night. Morning: 7:20 a.m., right bud 41%, left 45%. I gladly accepted my defeat. In-ear detection works very well. Sound: signature mode is too bass-y for me, balance mode does the job. Call quality: THE BEST. Build quality: buds good, case lid has a slight wobble. Noise isolation as good as Dizo Gopods Neo with 25dB ANC on.',
            date: '2023-04-10',
            verified_purchase: true,
          },
          {
            rating: 5,
            title: 'Quality product',
            text: 'This one is working perfectly. Good battery capacity for long time use. Quality sound.',
            date: '2026-04-19',
            verified_purchase: true,
          },
        ],
        one_star: [
          {
            rating: 1,
            title: 'The Ultimate Disappointment: A Scathing Review of the Worst Earbuds I\'ve Ever Used',
            text: "I've tested countless earbuds over the years. Never have I encountered a product as fundamentally flawed as these. Mic functionality is a joke for gaming purposes — picks up every noise except your voice. During a critical raid in my favorite MMO, my teammates kept asking, 'Are you chewing gravel?' Latency in games is so severe that gunshots arrive a full second late. The companion app crashes more than a toddler's toy car. Bass is overblown to distortion, mids are nonexistent, highs are shrill enough to shatter glass. Battery, advertised as 8 hours, barely lasts two at 50% volume. The plastic feels salvaged from a dollar-store toy. The right earbud's mesh grill fell off within a week. Final verdict: 0/10. The only thing these earbuds excel at is making you regret your purchase.",
            date: '2025-02-17',
            verified_purchase: true,
          },
        ],
      },
    ],
  },
}
