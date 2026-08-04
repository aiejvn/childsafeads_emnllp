# Error summary (8 instance(s) with at least one error)

## Per-tier error counts

- st1: 2/8
- st2: 5/8
- st3: 7/8

## st1 gold -> pred confusions

- physical_services -> physical_goods: 1x
- none -> physical_services: 1x

## st2 missing labels (gold had it, prediction missed it)

- creator_community: missing 1x
- education: missing 1x
- fashion: missing 1x
- other: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- hardware_electronics: extra 4x
- creator_community: extra 1x
- apps: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- creator_community -> hardware_electronics: 1x
- education -> hardware_electronics: 1x
- fashion -> hardware_electronics: 1x
- other -> apps: 1x
- other -> hardware_electronics: 1x

## st3 missing labels (gold had it, prediction missed it)

- direct_exhortation: missing 3x
- no_flag: missing 2x

## st3 extra labels (prediction hallucinated, not in gold)

- inadequate_disclosure: extra 3x
- misleading_claim: extra 2x
- direct_exhortation: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- no_flag -> misleading_claim: 1x
- no_flag -> inadequate_disclosure: 1x
- direct_exhortation -> inadequate_disclosure: 1x

## Detailed error instances

### UC4tb_1hfNkyp-zHYCsi_SAw_OPqHDiy1xo4_0b386d28

- gold: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["direct_exhortation", "misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "it can also hide your search engines which I know a lot of y'all need right now"}, {"flag": "direct_exhortation", "quote": "so go check out surf shark right now they offer a 30-day money back guarantee so there's no excuse not to try it and when you do decide to check it out make sure you put in my code one Cloud9 for an extra 3 month free"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps", "hardware_electronics"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["other"], "extra": ["apps", "hardware_electronics"]}, "st3": {"missing": ["direct_exhortation"], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
away and [Music] ALS today's video is sponsored by surf shark VPN in my opinion the best VPN out there see surf shark keeps your online identity safe by encrypting all of the information sent between your device and the internet this keeps all of your personal data protected from big companies or cyber criminal also this VPN can swap the real location of your device with a new one AKA just changing your IP address this way you can virtually travel the world and also watch Netflix in England while still being in America and the crazy part about surf shark is that they have over 3,000 servers in 100 different countries so you can literally watch Netflix in any country you want or if you're trying to run for the cops I mean you can just change your IP address and they never know where you are you can also bypass censorship everywhere surf Shar literally liberates your internet by unblocking blocked websites that otherwise you would not be able to get on to and all of this is through them changing your virtual location Sur shark also secures your online data this VPN encrypts your online data and helps to secure your personal information when you use for public Wi-Fi which can be a gold mod for hackers I'm telling you I've experienced it surf shar's clean web feature blocks ads trackers malware and fishing attempts allowing you to surf the web safely asking your IP address is essential to becoming private online surf shark makes sure that your City Country and download history aren't linked to your identity you can also make a fake identity by using surf shark too but you got to download the app to see that feature surf shark is also equipped with an antivirus that will fight off any and I mean anything that tries to attack your computer and it can also hide your search engines which I know a lot of y'all need right now so go check out surf shark right now they offer a 30-day money back guarantee so there's no excuse not to try it and when you do decide to check it out make sure you put in my code one Cloud9 for an extra 3 month free I appreciate surar vpf for sponsoring this video besides that let's get back to the main video I will say though these type of girls will

VIDEO: 10 Types Of Girls You Shouldn't Date
DESCRIPTION:
Secure your privacy with Surfshark! Enter coupon code 1CLOUD9 for an extra 3 months free at https://surfshark.deals/1cloud9
Merch Link: https://offbrnd.shop/
10 Types Of Girls You Shouldn't Date
1Cloud9

2nd Channel: https://www.youtube.com/channel/UC40NAebPG9L7We6A-LBa7FA
Email For Business Inquiries: kingoftheskys1@gmail.com   

Twitch- https://www.twitch.tv/1cloud9
The Discord- https://discord.gg/Rs34csUW8Q
Instagram- https://www.instagram.com/kingoftheskys/
Twitter- https://twitter.com/kingoftheskyss
OFFICIAL_DISCLOSURE: false

PAGE (1CLOUD9 - Surfshark):
Here's a gift from 1Cloud9
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


### UCfbnTUxUech4P1XgYUwYuKA_a5M_FI_BrH4_d7d3f40b

- gold: {"st1": "physical_goods", "st2": ["fashion"], "st3": ["undisclosed_advertising"], "st3_evidence": [{"flag": "undisclosed_advertising", "quote": "hey gamer sups shut up gamer sup use code cold ones ten percent off"}]}
- pred: {"st1": "physical_goods", "st2": ["fashion", "creator_community"], "st3": ["undisclosed_advertising", "direct_exhortation", "misleading_claim"]}
- errors: {"st2": {"missing": [], "extra": ["creator_community"]}, "st3": {"missing": [], "extra": ["direct_exhortation", "misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
i think you guys just don't like gin to be fair i love gin with gamer sups hey gamer sups shut up gamer sup use code cold ones ten percent off cool shirts shut up bye cool i do both down the hatch

VIDEO: Trying the World's Most Famous Alcohol
DESCRIPTION:
We Tried The Most Famous Drinks in the World!
🌈 Get the Clothes We're Wearing for 10% OFF with code "COLDONES"  👉🏻 https://bit.ly/coolshirtzz
🅿️ Pledge to our patreon for extended videos: https://www.patreon.com/coldones

SEND STUFF TO OUR PO BOX AND IT MIGHT BE FEATURED IN A VID: ✉️📬
PO Box 5091
Glenferrie south
VIC 3122
Australia
_______________________________________________________________
SOCIAL MEDIA LINKS
Twitter⇨ https://twitter.com/ColdOnes
Reddit⇨ https://www.reddit.com/r/ColdOnes/
Instagram ⇨ https://www.instagram.com/coldonestv/
Tik Tok ⇨ https://www.tiktok.com/@coldonestv
_______________________________________________________________
THE BOYS' SOLO CHANNELS
Chad - https://www.youtube.com/anything4views​​
Max - https://www.youtube.com/maxmoefoepokemon
_______________________________________________________________

Edited by  ⇨ https://twitter.com/the_gomii
_______________________________________________________________

#Alcohol #Celebrities #ColdOnes
OFFICIAL_DISCLOSURE: false

PAGE (RECENTLY RESTOCKED):
chemical
€57,95
Crewneck Sweater
AUD
gang shit
€37,95
T-Shirt
AUD
PSY-OP
€31,95
T-Shirt
AUD
PSY-OP
€31,95
T-Shirt
AUD
enderman
€93,95
Hoodie
AUD
enderman
€65,95
Trackpants
AUD
salmon
€38,95
T-Shirt
AUD
SOLD OUT
crafting
€100,95
Pants
AUD
monsters nearby
€62,95
Knit
AUD
axolotl
€42,95
Ushanka
AUD
axolotl
€31,95
T-Shirt
AUD
sheep
€42,95
Ushanka
AUD
sheep
€42,95
Ushanka
AUD
SOLD OUT
wolf
€31,95
T-Shirt
AUD
SOLD OUT
end
€31,95
T-Shirt
AUD
spider
€31,95
T-Shirt
AUD
holding hands
€31,95
T-Shirt
AUD
```
</details>


### UC4CsqctrGOn4NTz09sAhXwQ_15Db2IqCgxw_6a17d684

- gold: {"st1": "physical_services", "st2": ["hardware_electronics"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["misleading_claim"]}
- errors: {"st1": {"gold": "physical_services", "pred": "physical_goods"}, "st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
into the assembly let's take a moment to talk about today's sponsor PCB way if you have an idea for a new mod or want to assemble an open-source project PCB way provides you with the tools to make them a reality from 3D printing services in an array of materials all the way to other services like C CNC Machining injection molding and of course PCB and flex ribbon fabrication so when it comes to taking your retro mods to the next level PCB way is the place to make that happen check out the link in the description for PCB way to get $5 off your first order and again a huge thank you to PCB way for sponsoring this video all right so to start things off

VIDEO: Greatest Emulation Handheld Ever is a SEGA VMU
DESCRIPTION:
Use this link to SAVE $5 on your first order at PCBWay:  https://pcbway.com/g/A311e7

As a kid, I always dreamed of turning the VMU into a fully functional gaming handheld. Thanks to modder KiteRetro, that dream became a reality with his Circuit GEM kit. While the kit is no longer available for purchase, I was lucky enough to snag one back in 2020. In this video, I'll walk you through how it's made. Even though you can’t buy the kits anymore, you can still pick up fully assembled Circuit GEMs from Marky Pi (link below). It's hands down one of the coolest emulation handhelds out there!

// Where to purchase?:
     ► Pick up the Circuit GEM Here: https://markypigaming.com/index.php/product/circuit-gem-preorder/ 
     ► Custom VMU Shells: https://videogamesnewyork.com/vmu-shells/ 

// Follow The Creator:
     ► Kite Retro: https://x.com/kiteretro 
     ► Kite’s GihHub: https://github.com/kiteretro/Circuit-Gem 

// Support Macho Nacho:
     ► PATREON: https://www.patreon.com/MachoNachoProductions 
     ► eBay STORE: https://www.ebay.com/usr/machonachovideogamemods
     ► MERCH: https://www.artisticpixels305.com/machonacho 
     ► WEBSITE: https://macho-nacho.com/
     ► JOIN our DISCORD Community: https://discord.gg/4c3fCnfdaH 
     ► AMAZON Store For Tools/Supplies I Use (Affiliate): http://www.amazon.com/shop/machonachoproductions

// Follow Macho Nacho On Social Media
     ► Twitter:  https://twitter.com/machonachomedia
     ► Instagram:  https://www.instagram.com/machonachoproductions/ 
     ► Facebook:  https://www.facebook.com/MachoNachoProductions 
—--

Timestamps
0:00  Intro
2:22  Parts Overview
4:51  Installation Tutorial
12:44  Features
16:46  Pros and Cons
-----

// SAVE MONEY at these Retro Gaming Stores!  (Affiliate Links Below):

     ► SAVE 10% by using COUPON CODE:  TITO on any purchase from RETRO GAME:  TITO on any purchase from RETRO GAME REPAIR SHOP here: https://retrogamerepairshop.com/?ref=6njgx4sufvs

     ► SAVE 5% by using COUPON CODE: MACHONACHO on any purchase from RETRO MODDING here:  https://bit.ly/39hHnz7

     ► SAVE 10% by using COUPON CODE: TITO on any purchase from CASTLEMANIA Games here:  https://castlemaniagames.com/?ref=tito 

// TOOLS AND GEAR I Use For Video Game Console Modding (Soldering Equipment, Flux, 
     ►All other stuff I use: http://www.amazon.com/shop/machonachoproductions 
-----

// These stores provide fantastic GEAR and MODS for RETRO CONSOLES!  If you use the following links below, I received a small percentage from sales at no cost to you.  This is a great, free way to support the channel (Affiliate)!

○ Stone Age Gamer (Flash Carts and other great Retro Tech)
     ► https://stoneagegamer.com?afmc=MACHONACHO 

○ eBay (Second Hand Retro Gaming Gear and More.  It’s where I buy a lot of the consoles I mod!)
     ► https://ebay.us/NCwNkl 

○ Sendico (Proxy Service to bid on Japanese Auctions.  I use Sendico to get great deals on Retro Consoles directly from Japan!)
     ► https://www.sendico.com/register/2d5a5cf98826c580535586c73fce0a03e4c6f513 
-----

// Intro Music for Retro Renew Series by Matthew McCheskey:
     ► https://matthewmccheskey.bandcamp.com/
-----

Disclaimer:  This video is only for entertainment purposes. Any injury, damage, or loss that may result from improper use of tools, equipment, or from the information in this video is the sole responsibility of the viewer and is to be used at the discretion of the end user/viewer and not Macho Nacho Productions or Tito Perez.  If you are uncertain about any step of the process or feel unsure about your skill level, seek a more authoritative source.

Affiliate Disclosure: I get a small percentage of each sale that uses an affiliate link or coupon code.  It’s a great way to help SUPPORT my channel at no cost to you so I can continue to make these videos for all of you, everyone wins!  And as always, thank you for your continued support of my channel! 

#CircuitGEM #SegaDreamcast #MachoNachoProductions
OFFICIAL_DISCLOSURE: true

PAGE (Affordable Prototype PCB Manufacturer in China):
PCB Prototype the Easy Way
Full feature custom PCB prototype service.
9:00 - 18:00, Mon.- Fri. (GMT+8)
9:00 - 12:00, Sat. (GMT+8)
(Except Chinese public holidays)
Manufacturer Direct Pricing
As fast as 24 hours
Smooth shopping experience
With more than a decade in the field of PCB prototype and ...
Learn MoreLast 30 days
Customers
Paying
Turnkey/Kitted/Hybrid
2 days - 3 weeks
1 - 10000+
SMT & Supply Parts
Machine+Hand
Framework Stencil
1 - 64 Layers
Same Day - 5 weeks
1 - 10000+
High-Temp.FR4, Flex,
Flex-rigid, HDI, Rogers, etc.
0.5 - 13oz
Down to 2/2mil
1 - 10 Layers
As fast as 24 hours
5 - 10000+
FR4,Aluminum
1-3 oz
4/4mil (0.1mm)
Data-based quality PCB Prototyping service.
We will refund if the PCB quality is not as described or has defects
Covers more than 200 countries and regions worldwide
Pay with popular and secure payment methods
Competitive pricing from manufacturer of diverse capabilities
```
</details>


### UC4CsqctrGOn4NTz09sAhXwQ_0OMP8JvGWNY_6aa79e33

- gold: {"st1": "none", "st2": ["other"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "physical_services", "st2": ["other"], "st3": ["inadequate_disclosure"]}
- errors: {"st1": {"gold": "none", "pred": "physical_services"}, "st3": {"missing": ["no_flag"], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
parts. With pretty much all the 3D models complete, the next step was getting them made. For this, I'll be using a company called PCB Way, who also happens to be sponsoring this entire project. And honestly, none of this would have been possible without them. And I'll show you why here in a second. So, to get these built, we need to upload all the files to the PCB website, which is super simple. On the main page here, I'm going to click on the CNC 3D printing option and then click on add file. Next, I'm going to drag and drop

VIDEO: Building Microsoft’s Unreleased Metal XBOX (That Actually Works)
DESCRIPTION:
Purchase the files to 3D print your own XBOX Prototype HERE 👉 https://nachoengineering.com/
And watch this video for the full build tutorial HERE 👉 https://youtu.be/XJHRJEdm89M?si=YxFuGkdybUIH4mn5

Before the XBOX hit store shelves in 2001, Microsoft built one of the most iconic, and dare I say, wild prototypes in video game history. A massive, 40-pound block of machined aluminum, buffed to a mirror shine and shaped into an X, with a glowing green jewel at its core. It was a sight to behold and completely impractical as a home console. But it didn’t need to be. This was a statement piece, built to turn heads and prove that Microsoft could go toe-to-toe with the giants of gaming of the time (Sony, Nintendo and Sega).

So I set out on a journey to build my own, an exact replica, machined from solid aluminum… only better in every way. Join me as I take you through how it was done.
—--

Timestamps
0:00  Intro
5:38  How To Make The Massive Metal Shell?  
7:50   Part 1: Getting The Dimensions
13:51  Part 2: Powering The Beast
16:34   Part 3: The $36,000 Question
19:20  The Glowing Green Core  
22:15  The Arrival
27:19  The First Assembly
33:56  The Final Build  
38:57  What Can It Do? 
41:58  What’s Next?
43:12  Shout Outs!

// XBOX Prototype Dream Team:
     ► Wesk: https://x.com/WeskMods 
           ► Support Wesk’s Preservation Work:  https://ko-fi.com/weskmods 
     ► Redherring32: https://x.com/redherring32
           ► Support Redherring32:  https://ko-fi.com/redherring32 
     ► StuckPixel: https://x.com/pixel_stuck 
           ► Support StuckPixel: https://ko-fi.com/stuckpixel


//Make Your Own Custom Case HERE:
     ► MyCaseBuilder:  https://mycasebuilder.com/ 


// Get Your Limited Edition XBOX Prototype T-Shirts HERE!
     ► Limited Edition: https://www.artisticpixels305.com/product-page/xb-prototype-le-tee 
     ► Standard: https://www.artisticpixels305.com/product-page/xbox-prototype-video-tee 

//Original Music from Early Attic
     ► https://matthewmccheskey.bandcamp.com/album/panoramic
     ► https://www.facebook.com/earlyattic/

//XBOX Mods From The Video:
     ► SSD Mod (Affiliate):  https://www.amazon.com/shop/machonachoproductions/list/3JN287U11S04Y?ref_=cm_sw_r_cp_ud_aipsflist_Z1QE565VMTKJ78H164Y3 
     ► HDMI Kit: https://makemhz.com/products/xboxhd 

// Support Macho Nacho:
     ► PATREON: https://www.patreon.com/MachoNachoProductions 
     ► JOIN our DISCORD Community: https://discord.gg/4c3fCnfdaH 
     ► AMAZON Store For Tools/Supplies I Use (Affiliate): http://www.amazon.com/shop/machonachoproductions

// Follow Macho Nacho On Social Media
     ► Twitter:  https://twitter.com/machonachomedia
     ► Bluesky:  https://bsky.app/profile/machonachomedia.bsky.social 
     ► Instagram:  https://www.instagram.com/machonachoproductions/ 
     ► Facebook:  https://www.facebook.com/MachoNachoProductions 
—--

// SAVE MONEY at these Retro Gaming Stores!  (Affiliate Links Below):

     ► SAVE 10% by using COUPON CODE:  TITO on any purchase from RETRO GAME:  TITO on any purchase from RETRO GAME REPAIR SHOP here: https://retrogamerepairshop.com/?ref=6njgx4sufvs

     ► SAVE 5% by using COUPON CODE: MACHONACHO on any purchase from RETRO MODDING here:  https://bit.ly/39hHnz7

     ► SAVE 10% by using COUPON CODE: TITO on any purchase from CASTLEMANIA Games here:  https://castlemaniagames.com/?ref=tito 

// TOOLS AND GEAR I Use For Video Game Console Modding (Soldering Equipment, Flux, 
     ►All other stuff I use: http://www.amazon.com/shop/machonachoproductions 
-----

// These stores provide fantastic GEAR and MODS for RETRO CONSOLES!  If you use the following links below, I received a small percentage from sales at no cost to you.  This is a great, free way to support the channel (Affiliate)!

○ Stone Age Gamer 
     ► https://stoneagegamer.com?afmc=MACHONACHO 

○ eBay (Second Hand Retro Gaming Gear and More.  It’s where I buy a lot of the consoles I mod!)
     ► https://ebay.us/NCwNkl 

○ Sendico (Proxy Service to bid on Japanese Auctions.  I use Sendico to get great deals on Retro Consoles directly from Japan!)
     ► https://www.sendico.com/register/2d5a5cf98826c580535586c73fce0a03e4c6f513 
-----

Disclaimer:  This video is only for entertainment purposes. Any injury, damage, or loss that may result from improper use of tools, equipment, or from the information in this video is the sole responsibility of the viewer and is to be used at the discretion of the end user/viewer and not Macho Nacho Productions or Tito Perez.  If you are uncertain about any step of the process or feel unsure about your skill level, seek a more authoritative source.

Affiliate Disclosure: I get a small percentage of each sale that uses an affiliate link or coupon code.  It’s a great way to help SUPPORT my channel at no cost to you so I can continue to make these videos for all of you, everyone wins!  And as always, thank you for your continued support of my channel! 

#XBOX #XBOXPrototype #Microsoft
OFFICIAL_DISCLOSURE: true

PAGE (Support Wesk Mods 3D Scans):
This page is currently exclusively used for donations towards 3D scans of videogame consoles and peripherals. How to donate: In the "message" field request what item you'd like to see scanned. If there are enough funds in the pool I'll look at obtaining said item, if not it'll be added to the list and purchased when funds are available. Scans can be found here: https://bitbuilt.net/forums/index.php?forums/3d-scans-repository.183/ Current items next in-line for purchase:
Make money doing what you love.
Start a free page
```
</details>


### UChIZGfcnjHI0DG4nweWEduw_XXCQN5GaH0I_e07e1c20

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["direct_exhortation", "inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "this video is sponsored by VIP your CD key.com"}, {"flag": "misleading_claim", "quote": "they have legit Windows 10 Pro Keys as well as Windows 11 Pro keys for dirt cheap"}, {"flag": "direct_exhortation", "quote": "if you're building yourself a PC or you're looking to upgrade Windows do not pay full price for a key and instead pick them up from here"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps", "hardware_electronics"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": [], "extra": ["hardware_electronics"]}, "st3": {"missing": ["direct_exhortation"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
founders Edition the Rog Astro pallet game Rock MSI gaming Trio and the auras Master this video is sponsored by VIP your CD key.com if you're building yourself a PC or you're looking to upgrade Windows do not pay full price for a key and instead pick them up from here they have legit Windows 10 Pro Keys as well as Windows 11 Pro keys for dirt cheap using the C ts20 you'll get a nice discount and after checking out they will send you instructions on how to retrieve the key within a minute and afterwards all you have to do is go into the activation settings and put it in and you're good to go

VIDEO: Which RTX 5080 should you buy? (If you can 😭)
DESCRIPTION:
Comparing 5 different RTX 5080 models together to see which is the fastest.
🗝VIP-URCDkey Windows 11 Pro Oem Key $21:https://www.vip-urcdkey.com/vu/TS11
🗝VIP-URCDkey Windows 10 Pro Oem Key $15.9:https://www.vip-urcdkey.com/vu/TS10
Use 30% off code: TS20 only for Valentine's Day Sale！
Buy MS Win 11 Pro OEM KEY GLOBAL at : https://www.vip-urcdkey.com/ 

🔥TS Mousepads: https://techsourceshop.com
👽Join our Discord here: https://discord.gg/techsource
Instagram: https://www.instagram.com/ed.techsource/?hl=en

➡️Optional Parts⬅️
Precision Bit Kit: https://www.amazon.com/dp/B0DD9VH4BR
Budget Precision Bit Kit: https://www.amazon.com/dp/B0CQGLFSWP
Electric Screwdriver kit: https://www.amazon.com/dp/B0DN3SH96N
Cable Extensions: https://www.amazon.com/dp/B0CW3SWS37?th=1
Acrylic Wrist Rest: https://www.amazon.com/dp/B0D3JBK3SX?ref=myi_title_dp
OFFICIAL_DISCLOSURE: false

PAGE (Shoping online for PC Games, Software, Video Game Cdkeys, and All kinds of windows and office keys - www.vip-urcdkey.com):
EaseUS Data Recovery Wizard for Mac 1-Year CD Key Global
EaseUS Data Recovery Wizard for Mac 1-Month CD Key Global
EaseUS Data Recovery Wizard Professional Lifetime...
EaseUS Data Recovery Wizard Professional 1-Month CD Key...
EaseUS Video Downloader Monthly Subscription CD Key Global
EaseUS Todo Backup Home Yearly Subscription CD Key Global
EaseUS Todo Backup Workstation Lifetime Upgrades CD Key...
Octopath Traveler 2 Steam CD Key EU
The Last of Us Part I Steam CD Key EU
Age of Empires II: Definitive Edition Dawn of the Dukes...
Age of Empires II: Definitive Edition Lords Of The West...
Octopath Traveler 2 Steam CD Key EU
Boundary Steam CD Key Global
Resident Evil 3 Steam CD Key Global
Monster Hunter Rise: Sunbreak Standard Edition Steam CD...
Age of Empires III: Definitive Edition United States...
Sekiro Shadows Die Twice Steam Key Asia
Age of Empires II: Definitive Edition Lords Of The West...
Age of Empires III: Definitive Edition United States...
```
</details>


### UCXOKEdfOFxsHO_-Su3K8SHg_1WI4Fb6E9co_baa43fb0

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "that's basically digital creeping so what service vpn does is that it encrypts and secures the data information that you're sending through the internet so people that you don't want to have access to your personal information won't"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps", "hardware_electronics"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": [], "extra": ["hardware_electronics"]}, "st3": {"missing": [], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
and while we're waiting for that a big shout out and thank you to surf shark vpn for sponsoring this video and continuing to support this channel you guys heard me talk about surf shark vpn a lot and this is a service i've been using since before they became my sponsor and there are several reasons why i feel like everyone should be using this first of all if you don't know what a vpn is it's a virtual private network basically when you're going on the internet we're accessing all these different wi-fi hotspots around the world the information that you're sending through the internet is not protected that's why when you're searching certain brands or keywords where you're talking to your friends about certain brands or keywords all of a sudden you see whatever you're searching for the advertisement for that start popping up everywhere on your browsers on your facebook on your phone that's basically digital creeping so what service vpn does is that it encrypts and secures the data information that you're sending through the internet so people that you don't want to have access to your personal information won't also surf shark has hack clock id meaning that if anyone's trying to access things like your email you're going to get notified right away and right now i feel like more than ever because we're home all day we're always online we've all got to protect our digital information as much as possible another reason is entertainment if you guys don't know netflix has different shows and movies depending on which country you're in so when you're using surf shark vpn you can have access to other countries netflix catalogs like i always watch stuff from the uk or japan only thing i hate is that their anime is not translated so because you know it's in japan and when i'm traveling abroad i can also have access to my hulu account otherwise even though i'm paying for hulu i can't have access to my own account when i'm traveling overseas so if any of these things matter to you and you want to give it a try and i urge that you do use my link down below in my promo code dumpling and you're gonna get three months for free and you'll have 30 days to decide whether everything i'm telling you is true or not whether you like the servers or not if you don't like the service for whatever reason you'll get your money back guaranteed

VIDEO: TRYING COSTCO Instant Noodles, ASIAN FOOD | COSTCO Food Tour!
DESCRIPTION:
Get Surfshark VPN at https://Surfshark.deals/dumpling and enter promo code DUMPLING for 83% off and 3 extra months for free!

I've been doing a lot of Asian market reviews and haven't checked out Costco's item's yet so I wanted to see Costco's frozen and instant foods. 

★ Check out my Twitch: https://www.twitch.tv/eatwithmikey

***MORE EXCLUSIVE Content on Instagram***
✩ http://instagr.am/Mikexingchen

➔ Get tickets to the best show on earth!!! http://bit.ly/2gu7REI

✸ Strictly Dumpling T-Shirts HERE: http://bit.ly/2IVM2ts

➣ Subscribe for MORE videos about food! http://bit.ly/1hsxh41
➣ Subscribe to my Vlog Channel! https://bit.ly/2FJOGo1
------------------------------------------------------------------------------------------
★↓FOLLOW ME ON SOCIAL MEDIA!↓★
Facebook Show Page: https://www.facebook.com/strictlydumpling
Facebook Mike Fan Page: https://www.facebook.com/mikeychenx
Twitter: http://twitter.com/Mikexingchen

◈ Equipment I use for filming◈ :
Sony RX100 Mark V: https://go.magik.ly/ml/cgc5/
PANASONIC LUMIX G85: https://go.magik.ly/ml/cgcd/
Wide Angle Lens: https://go.magik.ly/ml/cgck/
Camera Mic: https://go.magik.ly/ml/cgcn/
Camera Lights: https://go.magik.ly/ml/cgcq/
Handheld Audio Recorder: https://go.magik.ly/ml/cgcr/
Tripod: https://go.magik.ly/ml/cgcu/
Drone: https://go.magik.ly/ml/cgcx/

My Favorite Cookware！
wok/pan http://amzn.to/2f5G0up
Also this pan http://amzn.to/2f5Qnyi
Pressure pan http://amzn.to/2wJIS7u
Nonstick pot http://amzn.to/2wHRgq1
-------------------------------------
♫ Music from: Epidemic Sound
http://www.epidemicsound.com
OFFICIAL_DISCLOSURE: false

PAGE (Strictly Dumpling - Surfshark):
Here's a gift from Strictly Dumpling
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


### UCdPui8EYr_sX6q1xNXCRPXg_LVaagltOhSs_6d438706

- gold: {"st1": "digital_content_or_services", "st2": ["creator_community"], "st3": ["direct_exhortation", "undisclosed_advertising"], "st3_evidence": [{"flag": "direct_exhortation", "quote": "Join Sora Plus today."}]}
- pred: {"st1": "digital_content_or_services", "st2": ["creator_community"], "st3": ["undisclosed_advertising"]}
- errors: {"st3": {"missing": ["direct_exhortation"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
he could be hiding inside. None of this running around malarkey. Have a little lie down. >> What the is store? Stora Plus is everything YouTube won't let us [music] show you. is how we bring you inside, not just behind the scenes, but into the core of Sto's mission. Get a raw insight into the physical and mental battles. The travel, [music] the rooftops, the runins, the bales and outtakes, and the stuff that shouldn't have been filmed, but passing a civil offense, you [ __ ] >> and loads more unpredictable chaos. >> Where are your shoe? [laughter] We're also bringing you [music] regular live streams, early access, and discounts on store products. Members onlyly events and an [music] exclusive community shaping what comes next. >> I cannot wait. >> This isn't just bonus content. It's your invite into the mission. Join Sora Plus today.

VIDEO: Parkour Hide & Seek In Military Fort
DESCRIPTION:
Join STORROR+ for regular members-only videos and the stuff we can't show on YouTube.
👉🏻 https://storrorplus.com
👕 STORROR Clothing:https://shop.storror.com/all-products 
🎮 STORROR GAME: https://www.youtube.com/@storrorparkourpro 
📸 STORROR Instagram: https://www.instagram.com/storror/
www.instagram.com/storrorsportdesign/ 
https://www.instagram.com/storrorparkourpro/ 

------
MUSIC:

ORBIT - SLWYAROLL
ENIGMA - DJ SEDUCE
AWOL - CRAFT CASE
CHESS - DREAM
BAHIA - EL EQUIPO DEL NORTE
INTERMISSION - HANNAH LINDGREN
ANNIHILATED - BLUE SAGA
MACHIAVELLIAN - WENDEL SCHERER
COALESCE - ELIN PIEL
VOLANT - ELIN PIEL
MEETING OF THE MINDS - SCIENTIFIC

Want us to use your music? 
- Submit your tracks to MUSIC@STORROR.COM
- Attach files to your email or use google drive/dropbox etc. 
- Do not use download links that expire (wetransfer etc).
- Include your credit links.
- Thank you 🙏 

------

THE TEAM:
- Toby Segar https://bit.ly/2ke3BPk
- Drew Taylor  http://bit.ly/2CHG01p
- Sacha Powell  http://bit.ly/2AuFzSd
- Joshua Burnett Blake  http://bit.ly/2CIb4OG
- Callum Powell  http://bit.ly/2lVO2IQ
- Max Cave  http://bit.ly/2CI78g4
- Benj Cave http://bit.ly/2Cu9MCx
------
DISCLAIMER:
This video features Parkour performed either by professionals or under the supervision of professionals. All members of team STORROR have been training since 2005 and insist that no one attempt to re-create or re-enact any ROOFTOP activities or movement AT HEIGHT performed in these videos.
OFFICIAL_DISCLOSURE: false

PAGE (STORROR+):
100+ hours of roof missions, raw moments, and behind-the-scenes stories. No ads. No platform rules. Just more STORROR.
Watch on
"On YouTube you feel like just one of millions. With STORROR+ you feel like you're part of the team — in the inner circle. You see things only people who actually care get to see."
Damitri — STORROR+ MemberEvery Monday, STORROR drops a video on YouTube. On S+ you get the same video with zero ads. No pre-rolls, no mid-rolls, no interruptions. Just watch it.
Demonetisation and platform rules mean a huge amount of what STORROR does never makes the main channel. On S+ none of that applies. Roof missions, raw moments, unfiltered stories. Published without compromise.
Early looks at new products, behind the edit, the planning behind big videos. S+ members see things before anyone else does.
Regular live sessions with the crew. Q&As, challenge videos, whatever's happening that week. You're not watching from the outside.
A members-only space where STORROR and the team post news, project teases, sneak peeks at product development, and things they're not sharing anywhere else.
A private Discord where STORROR actually shows up. Active, real-time conversation with the crew and members worldwide.
See exactly what's dropping and when. Upcoming videos, livestreams and events all in one place so you're the first to know what's coming.
Members get access to exclusive discounts on STORROR apparel. A perk of being part of the community.
Still Not Sure?
"The app gives everyone a much higher sense of community. I'd never been on Discord before. Now I feel like I'm part of something — not just paying for extra content on YouTube."
@Valersushiman"There's a huge back catalogue and you can always cancel if you don't enjoy it. But if you enjoy STORROR anyway, there's more than enough to keep you."
Carly"If you enjoy the main channel, this is a quality upgrade."
John"I consider it an essential expense for my mental health. It is worth the money."
Terry"Just do it, never back out, always do it, never, never back out."
Monty — STORROR+ MemberWatch from anywhere
Watch STORROR+ on mobile, TV apps, or web. At home, on the move, or wherever you’re watching from.
Gift someone full access to STORROR+
Ad-free exclusive access, livestreams, behind-the-scenes, missions, and a global community of STORROR fans.
BUY GIFT CARDS
```
</details>

