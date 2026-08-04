# Error summary (7 instance(s) with at least one error)

## Per-tier error counts

- st1: 0/7
- st2: 6/7
- st3: 5/7

## st2 missing labels (gold had it, prediction missed it)

- other: missing 3x
- creator_community: missing 2x
- education: missing 1x
- fashion: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- creator_community: extra 2x
- fashion: extra 1x
- food: extra 1x
- financial: extra 1x
- gambling_adjacent: extra 1x
- hardware_electronics: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- other -> creator_community: 1x
- creator_community -> financial: 1x
- other -> financial: 1x
- creator_community -> hardware_electronics: 1x
- education -> hardware_electronics: 1x
- fashion -> hardware_electronics: 1x

## st3 missing labels (gold had it, prediction missed it)

- no_flag: missing 1x
- inadequate_disclosure: missing 1x
- misleading_claim: missing 1x

## st3 extra labels (prediction hallucinated, not in gold)

- misleading_claim: extra 2x
- undisclosed_advertising: extra 1x
- inadequate_disclosure: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- no_flag -> misleading_claim: 1x
- inadequate_disclosure -> undisclosed_advertising: 1x

## Detailed error instances

### UCkxctb0jr8vwa4Do6c6su0Q_VyAYTFgzwzU_d7af87bb

- gold: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["inadequate_disclosure"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "Check out 30 Morbid Minutes on Spotify, Apple Podcasts, or wherever you listen to podcasts."}]}
- pred: {"st1": "digital_content_or_services", "st2": ["creator_community"], "st3": ["undisclosed_advertising"]}
- errors: {"st2": {"missing": ["other"], "extra": ["creator_community"]}, "st3": {"missing": ["inadequate_disclosure"], "extra": ["undisclosed_advertising"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
hear that noise again. I did not like that sound. Are you interested in the creepy history behind Victorian nursery rhymes? How do you feel about tales of sleep paralysis demons? Ever played around with seances and spirit boards or Googled necrocannibalism? Then 30 morbid minutes is a new podcast for you. Hosted by Elise Williams and Jessica Vasami, each episode investigates a new topic ranging from the macabre to the morbid to the downright creepy. Sourced straight from history and the headlines of today, 30 morbid minutes is sure to scratch that creepy crawly itch you may have. Subscribe now on Spotify, Apple Podcasts, or wherever you listen to podcasts. New episodes are available every Tuesday or they're available a day earlier for RT First members.

VIDEO: The Quarry Full Playthrough Part 4: An Eye For an Eye
DESCRIPTION:
Check out 30 Morbid Minutes on Spotify, Apple Podcasts, or wherever you listen to podcasts.
Get Your RTX Badges Here! ►
https://www.rtxevent.com/
We're back with Chapters 7 and 8 of The Quarry! Every day this week, we'll be releasing another part until we finish this game, one way or another. Today, the gang will need to keep their EYE on the prize if they want to solve the mystery and escape in one piece.

Head to our site for early, uncensored content: http://bit.ly/AHSite

» Get your Let's Play merch: http://bit.ly/AHmerch
» Subscribe: http://bit.ly/SubToLP

About Let's Play:
Hello fellow Gamer. This you should watch me. I play game. Good. Thank you, thank you. If you watch me, I'm hot. Videos, they'll be better... The Let's Play view is the right thing to do YouTube, so do.

More from Let's Play:
» Achievement Hunter: http://bit.ly/AHYTChannel

https://www.youtube.com/user/letsplay

#TheQuarry #FullPlaythrough
OFFICIAL_DISCLOSURE: true

PAGE (Rooster Teeth):
The funniest goddamn channel on the Internet, making you laugh since 2003. For more information, we’ve put together a handy guide...
There’s really no reason to visit any other website, given that we have everything you need here. But if you insist on going elsewhere you might as well follow us.
```
</details>


### UCkxctb0jr8vwa4Do6c6su0Q_BBzja8PGBZE_d7af87bb

- gold: {"st1": "physical_goods", "st2": ["other"], "st3": ["inadequate_disclosure"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "Go to http://uncommongoods.com/regulation to get 15% off."}]}
- pred: {"st1": "physical_goods", "st2": ["fashion", "food", "creator_community", "other"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": [], "extra": ["creator_community", "fashion", "food"]}, "st3": {"missing": [], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
it's not that's not in the video anymore I'm not stupid definitely keep that uh if you want to hear where do you get that this holiday season Uncommon Goods is your secret weapon and we all love a secret weapon Uncommon Goods is here to make your holiday shopping stressfree by scouring the globe for the most remarkable and truly unique gifts for everyone on your list whether you're shopping for your Secret Santa or your entire family UNC commmon Goods knows exactly what they want for me personally it's the Advent calendars I absolutely love an advent calendar I think there's so much fun I think they're a great talking point I've just had so many moments throughout the years of uh sharing that experience with people I care about whether it's family or friends that uh I can never get enough of them so I highly recommend you check out their Advent calendars when you shop on Uncommon Goods you're supporting artists and small independent businesses These Fine products are often made in small batches so shop now before they sell out this holiday season Uncommon Goods looks for the products that are the highest quality as well as being handmade or made in the US they have the most meaningful out of the ordinary gifts anywhere from art and jewelry to kitchen and home and bar Uncommon Goods as something for everyone not the same lackluster gifts you could find just anywhere and with every purchase you make in Uncommon Goods they give you back $1 to a nonprofit partner of your choice they've donated more than $2.5 million today to get 15% off your next gift go to uncommongoods.com regulation that's uncommongoods.com regulation for 15% off don't miss out on this limited time offer Uncommon Goods we're all out of the ordinary oh oh what slow motion dick

VIDEO: Regulation Gameplay // RoboCop: Rogue City
DESCRIPTION:
Go to http://uncommongoods.com/regulation to get 15% off.
Andrew is joined by Geoff and Gavin to shoot as many punk dicks as possible.
Thanks to Nacon for sending over a code!  In this special episode of Let's Play in RoboCop: Rogue City, 

» Support us directly » http://fuckfacepod.com/first
» Subscribe to LetsPlay » https://www.youtube.com/channel/UCkxctb0jr8vwa4Do6c6su0Q
» Subscribe to F**kFACE » https://www.youtube.com/channel/UCPP6JksBPYY3MeFQn5yanIw
» Get your F**kFACE Merch » https://store.roosterteeth.com/collections/f-kface

Follow F**kFACE here:
» Instagram » https://www.instagram.com/fuckfacepod/
» Twitter/X » https://twitter.com/FuckFacePod

Head to the Rooster Teeth site for more content: http://roosterteeth.com
#LetsPlay #RegulationGameplay
#Letsplay #RoboCop #FFpod
OFFICIAL_DISCLOSURE: true

PAGE (Rooster Teeth):
The funniest goddamn channel on the Internet, making you laugh since 2003. For more information, we’ve put together a handy guide...
There’s really no reason to visit any other website, given that we have everything you need here. But if you insist on going elsewhere you might as well follow us.
```
</details>


### UC2O6HDtMOZf9FkUAepz9Atg__FVVIVsEQ6s_a0c2ad91

- gold: {"st1": "digital_content_or_services", "st2": ["creator_community", "other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "It's a membership program with VIP treatment and insider pricing, usually with better deals than credit card programs or third-party sites."}, {"flag": "misleading_claim", "quote": "You can try the perks yourself with a free 1-year trial and also have the option to upgrade to their elite program for 70% off in your first week."}]}
- pred: {"st1": "digital_content_or_services", "st2": ["financial"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["creator_community", "other"], "extra": ["financial"]}, "st3": {"missing": [], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
the 10-hour flight down to Sydneys, Australia, mate. I'm coming back. Now, while we wait for the Panda Express to start boarding, can I tell you how I actually pull off some of the trips that I do like this one, flying with Airlines all over the world. I've been a Founders Card member for over 3 years now. It's a membership program with VIP treatment and insider pricing, usually with better deals than credit card programs or third-party sites. [music] Think of it like getting the perks of a premium credit card without having to have the premium credit card. For me, the big ones are lounge access like the one I'm sitting in in China and the premium travel partners. I've used it on Aero for a semi-private [music] flight, on JSX, on Blade, and Clear membership, too, which gets me through airport security at airports all around America without the fuss. Plus, top-tier status with Hertz, automatic status at top hotel chains with no spend requirements, and up to 70% off at luxury hotel brands. I've paid for it for 3 years now and renewed it twice, which should tell you everything you need to know about what I think of it. But, if you want to try it, the link's in the description, and use my code NoelVIP. You can try the perks yourself with a free 1-year trial and also have the option to upgrade to their elite program for 70% off in your first week. Click the link down below or use my promo code to unlock the offer. All right then, time to head down to the

VIDEO: I Flew China's Most Bizarre Airline - and instantly Regretted It
DESCRIPTION:
Get 12 months of FoundersCard for free with my link https://founderscard.com/NOELVIP
and use code NOELVIP

I took a flight on China's weirdest Airline - and instantly regretted it.

🛍️ OFFICIAL NOEL MERCH → https://www.noelphilips.com
🛩️ FLY WITH ME on my second channel → @FlyWithNoelPhilips
💬 Join my exclusive WhatsApp group + get bonus content & behind-the-scenes access → https://www.patreon.com/inflightvideo
OFFICIAL_DISCLOSURE: true

PAGE (VIP Travel Privileges):
Enjoy 12 Months of Trial Access
to FoundersCard Membership
Members receive preferred pricing and elite status with leading airlines, rental car programs, loyalty programs, and innovative travel brands. Benefits include:
Some benefits are not available on the trial and require an upgrade to a paid plan.
"I travel often so I was very happy I was able to get such a large discount using this benefit. The savings alone on one rental would easily pay for the membership to FoundersCard for a year. Amazing!"
Robbie M., Owner @ Glam-R-Ize
Based on a single 5–10 night stay, FoundersCard Members save an average of $2,500 – $5,000 annually, and benefit from added amenities and flexible cancellation at top hotels and resorts globally.
FoundersCard helps businesses of all sizes succeed with a customized program of exclusive benefits and savings. Benefits include:
Some benefits are not available on the trial and require an upgrade to a paid plan.
"Stripe benefit paid for my FoundersCard membership for the next year. It works seamlessly with my e-commerce platform and integrates into QuickBooks. Simply excellent."
Jason G, Chairman of the Board @ Pfenex, Inc.
FoundersCard offers Members-only pricing, privileges, and access with a wide network of leading fashion, fitness, and entertainment brands.
Activate NowSome benefits are not available on the trial and require an upgrade to a paid plan.
A selection of our lifestyle benefit partners
Curated by FoundersCard, these exclusive gatherings combine world-class dining with powerful connection. Held in hand-selected, iconic venues across the globe’s most sought-after cities, each event offers an unforgettable blend of sophistication, access, and meaningful conversation.
Join the 300,000+ FoundersCard community
Join us at Trapezi on May 14th
Created By
VP of Partnerships & Experiences, FoundersCard
FC Member since 2025
Join us at Central Park Tower on June 4th
Created By
Founder & CEO, FoundersCard
FC Member since 2009
Join us at The Ned London on September 24th
Created By
VP of Partnerships & Experiences, FoundersCard
FC Member since 2025
FoundersCard is more than just a membership — it’s your gateway to a vibrant community of like-minded entrepreneurs and innovators, brought together through curated experiences and exclusive opportunities.
Nelson G.
CEO - For The Earth Corp
Lorna P.
CEO - Stewart Forbes
David H.
Founder & Chief Scientist,
Hanson Robotics
FoundersCard isn't a credit card itself; rather, it's a membership program that unlocks VIP benefits and privileges, designed to complement and enhance your existing credit card strategy.
The full list of our VIP member benefits is available after you've submitted your invitation request or joined FoundersCard. This is to maintain the exclusivity our partners provide.
FoundersCard Membership is available globally. While we do our best to select benefits that all Members can enjoy, there may be some restrictions based on your location.
You will have access to redeem the benefits available on your Membership tier upon the approval of your Membership application.
Some benefits require a paid membership and may vary by tier, membership start date, and yearly fee.
Each benefit has a dedicated landing page on the FoundersCard site, with instructions on how to redeem. Benefits are not automatically redeemed for you.
```
</details>


### UCHu2KNu6TtJ0p4hpSW7Yv7Q_819Ovq5FPxY_ea312c4e

- gold: {"st1": "physical_goods", "st2": ["creator_community", "education", "fashion"], "st3": ["inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "let's just share a few words from our sponsor any cubic"}, {"flag": "misleading_claim", "quote": "a brand new top of the line and super affordable extreme high resolution resin printer the photon monox 6k will be available from november 15th it will be available from the anycubic store with an early bird offer of 5.99 before they ultimately retail for 659 us dollars"}]}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["creator_community", "education", "fashion"], "extra": ["hardware_electronics"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
claws while the final two claws are printing let's just share a few words from our sponsor any cubic makers of awesome 3d printers any cubic makers of the viper that have done the filament printing on have just released a brand new top of the line and super affordable extreme high resolution resin printer the photon monox 6k will be available from november 15th it will be available from the anycubic store with an early bird offer of 5.99 before they ultimately retail for 659 us dollars with a much improved 5760 by 3600 pixels with print resolution up to 34 microns offering a higher level of detail for 3d models and additionally it features an industry-leading 350 to 1 black and white contrast screen with a 9.25 6k led screen the photon 1x6k has a significant print volume 247 larger than the 6.08 inch 3d printers making it not only higher quality than a lot of its competitors but enabling you to print more it has a super fast print speed where you only need one and a half hours to print a 12 millimeter garage kit saving four and a half hours compared to the any cubic photon on one and a half hours over the run of the mill 6.8 inch 3d printers so go check out the any cubic monox 6k and if you're early you could get that awesome discount huge thank you to nqb for sponsoring the video and making this project possible this looks astounding by the way the level of detail at this tiny size is super impressive i wonder how impressive it is well it's this [Applause] [Music]

VIDEO: IS THIS my most DANGEROUS creation?...
DESCRIPTION:
Check out the ANYCUBIC PHOTON MONO X 6K 3D printer from the official store (spon) http://bit.ly/3C58Keh - Limited units only $599 available on Nov 15, 2021
- Get the Space Bear Claw: https://www.myminifactory.com/users/TabletopTime
- Get the Space Bear Bust and Bits: https://puppetswar.eu/space-bears.html
- Watch More Space Bear VIDEOS! https://www.youtube.com/watch?v=ockcxkz7GEs&list=PLxfMCMdaVAV0McByqNrViuhSv0wlbUmVk&index=2
--------------------------------
✨support me on Patreon: https://www.patreon.com/jazzastudios
🖌️ GET MY APP, BRUSHES, MERCH and MORE!
➨ https://www.jazzastudios.com
--------------------------------
JAZZA'S OFFICIAL SOCIALS! - Follow/Sub ↴
▶ TikTok: https://www.tiktok.com/@jazzastudios
▶ Instagram: https://www.instagram.com/jazzastudios/
▶ Bluesky: https://bsky.app/profile/jazzastudios.com
▶ Facebook: https://www.facebook.com/JazzaOfficial/
▶ Twitter: https://twitter.com/jazzastudios
--------------------------------
OFFICIAL_DISCLOSURE: false

PAGE (Jazza Studios):
Skip to content
Menu
Search
Log in
Create account
0
Cart
Item added to your cart
View my cart (0)
Check out
Continue shopping
Shop
Contact
Log in
Create account
Close
JAZZA
STUDIOS
Shop
Contact
Featured Digital Products
See More
Jazza's Ultimate COLORING BUNDLE!
Jazza's Ultimate COLORING BUNDLE!
€31,95
€31,95
Unit price
/
per
Jazza's Alcohol Marker Masterclass
Jazza's Alcohol Marker Masterclass
€26,95
€26,95
Unit price
/
per
Color Quest: Digital Coloring Pages
Color Quest: Digital Coloring Pages
€13,95
€13,95
Unit price
/
per
Jazza's Ultimate DIGITAL PAINTING BUNDLE!
Jazza's Ultimate DIGITAL PAINTING BUNDLE!
€31,95
€31,95
Unit price
/
per
THE CLASSICS ARE BACK!
See more
I'm An Adult - Unisex Tee
I'm An Adult - Unisex Tee
From €17,95
From €17,95
Unit price
/
per
OBNOXIOUS - Unisex Tee
OBNOXIOUS - Unisex Tee
From €17,95
From €17,95
Unit price
/
per
Kinaesthetic Learner - Unisex Tee
Kinaesthetic Learner - Unisex Tee
From €17,95
From €17,95
Unit price
/
per
Choosing a selection results in a full page refresh.
```
</details>


### UC6Oihk5E2X9kuvI4q4rWxtQ_QPTVS_H_w1Q_79513155

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
it's been like 2 weeks since my last one so you know we're due but before we get started this video is sponsored by Disney speed storm inspired by Disney and Pixar worlds Disney speed storm is the ultimate hero-based combat racing game with highspeed circuits and competitive yet fine and accessible gameplay and Disney speed storm just released season 5 on November 30th which features brand new Racers inspired by Frozen plus this Let It Go season brings brand new customization items and a brand new RAC trck environment inspired by Arendell and this game has already been launched as freeo playay in September so with the freeo play title anyone can download the game for free on PC or console Frozen holds a special place in my heart and my favorite is Olaf so I was obviously thrilled when I found out you could play with him as a racer in the game but of course Elsa Anna Kristoff and Hans are there too there are also four different racer classes including Speedster trickster brawler and Defender so you can switch it up depending on your play style Disney speed storm is suitable for both single and multiplayers so you can play with your friends and you can download the game for free using PC or console to start racing with some of your favorite Disney and Pixar characters the link to download will be down in the description below and thank you so much to Disney sweed storm for sponsoring this video let's get back into it this is what I

VIDEO: Building a POP-UP BOOK Townhouse in The Sims 4
DESCRIPTION:
Thank you to Disney Speedstorm for sponsoring this video! Download Disney Speedstorm's new season "Let it Go" here: https://gmlft.co/Syd-DS-YT #sponsored

Let's build in the sims 4! Today we're building a townhouse inside a storybook.

❥❥❥VLOGS: https://www.youtube.com/c/SydMacVlogs  

♡follow me♡
twitch: https://www.twitch.tv/sydmac
discord: https://discord.gg/xUykUMm
twitter: https://twitter.com/sydneymacoretta
instagram: http://instagram.com/smacoretta 
tiktok: http://tiktok.com/@sydneymacoretta
sims 4 gallery ID: sydneymacoretta 

♡more sims 4 content♡
builds: https://youtube.com/playlist?list=PLBqWb--FlIRcRQdnkpoOKvAPz37GRgFjo
gameplay: https://youtube.com/playlist?list=PLBqWb--FlIRdYN8jp12xzX4eFQ9yLs4HJ
create a Sim: https://youtube.com/playlist?list=PLBqWb--FlIRd8LL824vUX010M0yMX_sdU
build Hacks: https://youtube.com/playlist?list=PLBqWb--FlIRdNrK3AxNGyvMsR0DmSSOd3
tutorials: https://youtube.com/playlist?list=PLBqWb--FlIRfWw8J0B--yNzXe-fCtYVAY

The Sims 4 is rated T for Teen and this video is intended for an audience aged 13 and up.

00:00-01:27 Intro
01:28-10:44 Exterior
10:45-19:00 Traditional Christmas Interior
19:01- All Beige Christmas Interior
OFFICIAL_DISCLOSURE: true

PAGE (Disney Speedstorm | Available now):
TAKE THE TRACKS BY STORM
An incredible lineup of Disney and Pixar Racers are suited up and revved up for racing combat.
Each Racer has a Unique Skill at their disposal. Whether you use Mulan's "Firework Barrage" to blow the competition away or Sulley's "Fearsome Roar" to scare them off the track, there's a wide range of Unique Skills to master.
FEARSOME ROAR
NORMAL: Sulley's roar pushes all the opponents in the area around him, instantly replenishes the boost bar, and gets more boost fuel for each affected Racer.
CHARGED: Sulley roars three times, each time Stunning all the opponents in an even bigger area.
From the docks of the Pirates' Island track from Pirates of the Caribbean to the wilds of the Jungle Ruins map from The Jungle Book, experience these worlds from a fresh perspective geared specifically for racing!
```
</details>


### UCHJ-qzwjtcO2bNY7UfZxd-g_BW42nM2M3Ww_56aadca8

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["age_restricted_or_prohibited_product", "inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "https://bandit.camp/r/rustmoments for a FREE $0.15  (18+)"}, {"flag": "misleading_claim", "quote": "https://bandit.camp/r/rustmoments for a FREE $0.15  (18+)"}, {"flag": "age_restricted_or_prohibited_product", "quote": "https://bandit.camp/r/rustmoments for a FREE $0.15  (18+)"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps", "gambling_adjacent"], "st3": ["inadequate_disclosure", "age_restricted_or_prohibited_product"]}
- errors: {"st2": {"missing": [], "extra": ["gambling_adjacent"]}, "st3": {"missing": ["misleading_claim"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:


VIDEO: BEST RUST TWITCH HIGHLIGHTS AND FUNNY MOMENTS 255
DESCRIPTION:
https://bandit.camp/r/rustmoments for a FREE $0.15  (18+)

Welcome back to another episode of Best Rust twitch highlights and funny moments!
(Videos where viewers submit their clips to my form and I edit them into one Rust moments video)

If You liked the video, please hit the thumbs up button and subscribe for more videos.

Submit your clips: https://forms.gle/1eiAbc1XQRxFz9mG7
Also join my discord: https://discord.gg/w77b3KTSPd

00:00 Sponsor
00:24 Rust Moments

Featuring:

https://www.twitch.tv/toonyx
https://www.twitch.tv/qaixx
https://www.twitch.tv/xkevv
https://www.twitch.tv/a1dan8992
https://www.twitch.tv/posty
https://www.twitch.tv/winnie
https://www.twitch.tv/jukebox288
https://www.twitch.tv/albin
https://www.twitch.tv/ferhatucarr
https://www.twitch.tv/snowmers
https://medal.tv/u/ThaChad
https://www.twitch.tv/bchillz
https://www.twitch.tv/maximz

#rust​​​​​​ #rusthighlights​​​​ #rustmoments​​​

VIDEO CONTEXT DISCLAIMER:
We obtain clips from our viewers with full permission and rights to use them and compile clips to fit under the guise of a compelling narrative via the use of interesting and exciting video concepts and themes for each individual video. We also add significant editing to make the work transformative from the original creations and fair use.
OFFICIAL_DISCLOSURE: true

PAGE (ThaChad's Latest Clips & Gameplay Videos | Medal.tv):
Record, Edit and Share Gaming Moments.
Medal is the easiest way to record, save, and share your best gaming moments. Whether you’re pulling off
chaotic stunts in Fortnite or catching hilarious fails in Roblox, use Medal to make sure those moments don’t
get missed. Clip instantly and connect with friends over highlights that matter.
Page not displaying correctly? You need to enable JavaScript to run this page!
```
</details>


### UC2O6HDtMOZf9FkUAepz9Atg_8WZGH0Tlmms_97011208

- gold: {"st1": "digital_content_or_services", "st2": ["apps", "other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "You see, thanks to Surfshark, surfing the web is a lot more pleasurable and safer, too."}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": ["other"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
chicken with biscuits and gravy. You can't beat them. That's so good. [Music] This video is brought to you by Surfshark. Now, as you guys know, there is nothing I enjoy more in the world than surfing. I'd even go so far as to say I'm actually pretty GOOD AT IT. WELL, NOT THIS SORT OF SURFING. OBVIOUSLY, I'm not very good at this. It's far too cold and wet for my liking. I much prefer a different sort of surfing. Surfing the web. I'm really good at that and I can spend hours at it. You see, thanks to Surfshark, surfing the web is a lot more pleasurable and safer, too. Surfshark's a VPN that encrypts all of your data. Even when I'm traveling on public airport hotspots and Wi-Fi on planes, in hotels, you name it. Whenever I'm on public Wi-Fi, my data is safe because I'm encrypted through the Surfshark VPN. You see, a VPN encrypts your data, which means that you're not leaving anything on display for the rest of the world to see. Even when I'm not traveling, though, Surfshark comes in handy because I can sit and watch TV as if I'm anywhere else in the world, which is really handy because I live here in the States. Thanks to Surfshark, I can still watch my favorite TV programs with Susie, like Gogglebox. Super easy to install. You go on the website, you download it and install it, you sign into your account, and then you can choose whichever country you'd like to connect through. Right now, Surfshark are offering you four extra months completely free of charge at surfshark.com/noel phillips. [Music] So, I'd flown in, explored Beckley

VIDEO: I Took America's Most POINTLESS Flight
DESCRIPTION:
Go to https://surfshark.com/noelphilips or use code NOELPHILIPS at checkout to get 4 extra months of Surfshark VPN!
I took the twice daily jet flight between two tiny towns that nobody takes, to find out... why?!

🛍️ OFFICIAL NOEL MERCH → https://www.noelphilips.com
🛩️ FLY WITH ME on my second channel → @FlyWithNoelPhilips
💬 Join my exclusive WhatsApp group + get bonus content & behind-the-scenes access → https://www.patreon.com/inflightvideo
OFFICIAL_DISCLOSURE: true

PAGE (Noel Philips - Surfshark):
Here's a gift from Noel Philips
- Browse the web safely and ad-free
- Stream content securely and privately
- Connect an unlimited number of devices
Widely trusted with 40M+ global app downloads, rewarded with 30+ recognition awards
Data as of 06/22/2026
Data as of 06/22/2026
Surfshark is not only a great VPN that allows me to access whatever content I want but they also let me say whatever I want! Eat bricks, kids!
I have been using Surfshark since I got it and I love it.
I haven’t turned it off since I downloaded it, because everything is blocked in Australia for some reason.
I love using Surfshark, it’s a really simple straightforward way of watching movies from any location!
We absolutely LOVE using Surfshark! We’re huge fans of the brand and this VPN has literally changed our lives!
I love using Surfshark because I get to watch all the content that's available but couldn't because of my location!
Surfshark is not only a great VPN that allows me to access whatever content I want but they also let me say whatever I want! Eat bricks, kids!
I have been using Surfshark since I got it and I love it.
I haven’t turned it off since I downloaded it, because everything is blocked in Australia for some reason.
I love using Surfshark, it’s a really simple straightforward way of watching movies from any location!
We absolutely LOVE using Surfshark! We’re huge fans of the brand and this VPN has literally changed our lives!
I love using Surfshark because I get to watch all the content that's available but couldn't because of my location!
Surfshark is not only a great VPN that allows me to access whatever content I want but they also let me say whatever I want! Eat bricks, kids!
I have been using Surfshark since I got it and I love it.
I haven’t turned it off since I downloaded it, because everything is blocked in Australia for some reason.
I love using Surfshark, it’s a really simple straightforward way of watching movies from any location!
We absolutely LOVE using Surfshark! We’re huge fans of the brand and this VPN has literally changed our lives!
I love using Surfshark because I get to watch all the content that's available but couldn't because of my location!
Surfshark One
Surfshark One is a cybersecurity bundle for all-over protection. Surf the web without tracking, secure your devices from threats, guard your personal data, & get immediate data breach alerts.
Secure your connection
Enjoy your online adventures with 24/7 privacy protection by the award-winning Surfshark VPN
Keep your personal data private
Create a brand new online identity and a proxy email with Alternative ID. Use it to shield your info, avoid data leaks and a spam-filled inbox.
Protect your devices
Surfshark Antivirus — powerful device protection that secures everything, from your webcam to your files. Experience 24/7 security that you can set and forget.
Get data leak alerts
Alert notifies you the moment your email addresses, IDs, credit cards, or other personal data gets leaked online.
Browse ad-free without digital footprints with the Surfshark Search engine.
```
</details>

