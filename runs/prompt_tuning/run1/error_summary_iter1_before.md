# Error summary (9 instance(s) with at least one error)

## Per-tier error counts

- st1: 2/9
- st2: 5/9
- st3: 7/9

## st1 gold -> pred confusions

- physical_services -> digital_content_or_services: 1x
- digital_content_or_services -> physical_goods: 1x

## st2 missing labels (gold had it, prediction missed it)

- creator_community: missing 2x
- other: missing 2x
- apps: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- other: extra 1x
- health: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- apps -> other: 1x

## st3 missing labels (gold had it, prediction missed it)

- misleading_claim: missing 5x
- inadequate_disclosure: missing 2x

## st3 extra labels (prediction hallucinated, not in gold)

- undisclosed_advertising: extra 4x
- no_flag: extra 2x
- direct_exhortation: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- inadequate_disclosure -> undisclosed_advertising: 2x
- misleading_claim -> undisclosed_advertising: 2x
- misleading_claim -> no_flag: 2x
- misleading_claim -> direct_exhortation: 1x

## Detailed error instances

### UCd21m0AHf4Vx88Znty7v4Cw_a7NgJJnSmFI_4fc96499

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "that's why we have a great hero and the sponsor of this video expressvpn"}, {"flag": "misleading_claim", "quote": "it does all of this without slowing your internet speeds down whatsoever"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["undisclosed_advertising"]}
- errors: {"st2": {"missing": ["apps"], "extra": ["other"]}, "st3": {"missing": ["inadequate_disclosure", "misleading_claim"], "extra": ["undisclosed_advertising"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
most hyped i've been for an upcoming episode well while we're on the topic of villains you know who anime fans consider the true villains region locks of course that's why we have a great hero and the sponsor of this video expressvpn it's the premier vpn service that will allow you to bypass those pesky region locks and enjoy shows you wouldn't normally be able to access legally i started using expressvpn and i never looked back i recently used it to watch some killer kill fights just open expressvpn and select the united states server and boom now you can use it to watch hundreds of different anime which aren't available in your region and it does all of this without slowing your internet speeds down whatsoever i can stream animate with blazing fast speeds in hd quality and never experience any buffering with expressvpn you can also browse the internet with the maximum security that a vpn can provide that includes hiding your location and protecting you against the scourge of attacks on privacy that are becoming more and more prevalent as the days go by and all you have to do is head on to my description box and follow the instructions to download expressvpn or just go to expressvpn.com vinnie tube with expressvpn see a brand new internet without limits start your trial on the number one vpn service now

VIDEO: Top 10 Most Epic Villain Transformations in Anime
DESCRIPTION:
Go to https://www.ExpressVPN.com/viniitube and find out how you can get 3 months of Express VPN free!
In this video we'll be going through some of the most epic and impactful Villain Transformations in Anime. If you like the video please like and share. This list is just my opinion, so feel free to comment your list below. For more Top 10's and anime related videos subscribe!

Patreon: https://www.patreon.com/ViniiTube
Join this channel to get access to perks:
https://www.youtube.com/channel/UCd21m0AHf4Vx88Znty7v4Cw/join
2nd/Non-Top 10 Channel: https://www.youtube.com/c/ViniiTubeKai
Twitter:  https://twitter.com/ViniiTube
Instagram: https://www.instagram.com/viniitube/
#ViniiTube #Anime #AnimeTops
_

Credits to:
Thumbnail by https://bit.ly/2SsjAKD
Edited by Jivaanu
Voiceover by Jas Rao: http://jasrao.co.uk



Copyright Disclaimer Under Section 107 of the Copyright Act 1976, allowance is made for "fair use" for purposes such as criticism, comment, news reporting, teaching, scholarship, and research. Fair use is a use permitted by copyright statute that might otherwise be infringing.
OFFICIAL_DISCLOSURE: false

PAGE (Get the ViniiTube VPN deal: 4 extra months and new apps):
Get the ViniiTube VPN deal: 4 extra months and new apps
Enjoy 4 extra months on our special offer for ViniiTube viewers!
30-day money back guarantee for new users
One subscription brings together all layers of privacy
Your internet connection is where most online exposure begins, especially on shared or public networks.
ExpressVPN helps keep your browsing private by encrypting your traffic before it leaves your device.
It’s designed to fit naturally into how you already use the internet, whether you’re at home, travelling, or connected to public WiFi.
Most account issues start with reused or weak passwords.
ExpressKeys helps generate and store strong, unique passwords so one mistake doesn’t spread further than it should.
By removing the need to remember or reuse credentials, it supports safer routine account access across the services you already use.
Even careful people are affected by data breaches they didn’t cause.
Identity Defender helps monitor for signs that personal information may be misused, so issues can be addressed earlier rather than later.
It provides visibility into potential identity-related risks without requiring constant attention. Currently available for U.S. users only.
Your email address is one of the most persistent identifiers you have online.
MailGuard lets you create aliases when signing up for services, newsletters, coupons, or trials, so your real address stays private.
If an alias is ever compromised or starts receiving spam, you can simply turn it off without affecting your main inbox.
From install to everyday coverage — Set up in 90 seconds
-
Download & Install
Works across the devices you already use
-
One-Tap Connect
Connect easily wherever you are
-
Start Browsing
A safer more private way to be online
24/7 customer support via live chat & email
Get ExpressVPNDefense fit for those who shape the internet
Engineered for privacy, security, and reliability
Lightway protocol
Designed to connect instantly, encrypt data quickly & hide your connections from online threats
AES-256 Encryption
Industry-standard encryption used to keep your internet traffic secure and private so you can stay safe online
TrustedServer Technology
Audited & verified RAM-based servers wipe your digital trail & leave zero breadcrumbs for advertisers
Private DNS
Your DNS requests stay private, away from prying eyes & third-party trackers
Parental controls
Keep your kids safe online with content filtering, website blocking, and real-time monitoring—all built into ExpressVPN
Identity Defender (U.S. only)
Monitors the dark web for data leaks, alerts you to identity breaches & helps safeguard your personal information
Consistently fast speeds, built for everyday use
Designed to stay fast and stable, even during long online sessions
- Powered by Lightway: an in-house protocol engineered for speed, stability and efficiency
- Optimized servers designed to handle data-intensive activity without unnecessary slowdown
- Unlimited bandwidth, with no artificial data caps or usage limits
A distributed server network, designed for reliability
Supports your internet access across different locations and networks
- A global network of servers in 170+ locations to support stable connections worldwide
- Specialized servers designed to work on networks with access restrictions
- Access to IP locations that support all your apps, website and platforms
Built for households with multiple devices
Easy to set up apps and simple to manage across a shared household
- Native apps for phones, computers, tablets, and smart TVs
- Use on upto 14 devices at the same time under one subscription
- Optional browser extensions for Chrome, Firefox and Edge that extend privacy into day-to-day browsing
Why ViniiTube recommends ExpressVPN
There’s a reason people love ExpressVPN—see how it leads
| Included in all plans | ||||
|---|---|---|---|---|
| 4K Streaming Support | ||||
| AES 256-bit Encryption | ||||
| Kill Switch | ||||
| DNS & IP Leak Protection | ||||
| WireGuard Post-Quantum Protection | ||||
| In-App Server Speed Test | ||||
| Servers in All 50 U.S States | ||||
| TrustedServer Technology | ||||
| Ultra-Fast Full Rust Protocol | ||||
| Included with highest tiers | ||||
| Password Manager | ||||
| Inbox protection service | ||||
| Private AI workspace | ||||
| ID defender | (U.S. Only) |
|||
| Dedicated IP | ||||
| Free eSIM Data | ||||
| Parental Controls | ||||
| Router with built-in VPN* |
What our most satisfied customers say
-
Rated 4.4 out of 5
-
Rated 4.7 out of 5
ExpressVPN for ViniiTube: Try it risk free
- Preventative, layered approach to online security
- Works across shared devices and households
- 30-day money-back guarantee
```
</details>


### UCB_qr75-ydFVKSF9Dmo6izg_1Uc68hBXOrs_67f0ddda

- gold: {"st1": "physical_goods", "st2": ["creator_community", "fashion", "other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "All Ridge products come with a lifetime warranty. So, this is literally the last wallet you'll ever have to buy."}]}
- pred: {"st1": "physical_goods", "st2": ["fashion"], "st3": ["undisclosed_advertising"]}
- errors: {"st2": {"missing": ["creator_community", "other"], "extra": []}, "st3": {"missing": ["misleading_claim"], "extra": ["undisclosed_advertising"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
Silverstone is like it's it is staggering. It is breathtaking. This episode is sponsored by Ridge. I think a lot of you might relate to this. You know, when you're all suited and booted up for an event, maybe a wedding or just a sharp outfit for a night out, the last thing you want is a bulky wallet making your jacket bulge like you've got a sandwich stuffed in your pocket. It totally ruins the look, doesn't it? That's one of the first things I noticed with my Ridge wallet. It's so slim. I can slide in a couple of cards, my driving license, even a hotel key card, and it all sits flat, neat, and it's incredibly durable. I've been using my Ridge wallet and key case for a couple of weeks now, and honestly, I love them. The build is solid. Mine's in slate gray, and it looks like something lifted straight off an F1 chassis. When I'm filming episodes for the podcast or doing interviews on camera, I'm often sitting down, and the last thing I want is my keys and my wallet sticking out. But with Ridge, I barely noticed them. The key case is just as clever. It's roughly the size of a USB stick, and your keys fold neatly inside. No jingling, nothing poking you in the leg, and way more comfortable in your pocket. We always talk in racing about marginal gains, little tweaks that make a big difference. That's exactly what Ridge delivers. Once you start using it, you'll wonder why you didn't switch sooner. All Ridge products come with a lifetime warranty. So, this is literally the last wallet you'll ever have to buy. And with over 50 colors and styles to choose from, you might as well get something you really love. For a limited time, our listeners get 10% off at Ridge by using the code grid at checkout. Just head to ridge.com and use the code grid and you're all set. After you purchase, they will ask you where you heard about them. Please support our show and tell them that our show sent you. Now, Brad, you guys were embedded in

VIDEO: Brad Pitt: Becoming Sonny Hayes For F1 The Movie | F1 Beyond The Grid Podcast
DESCRIPTION:
For F1 The Movie, Brad Pitt lived the high-speed life of a Formula 1 driver. He drove with seven-time World Champion Lewis Hamilton. He learned to race. He spent years shooting scenes at racetracks around the world.

The result is what he calls ‘the most visceral feeling you will get in a race car of anything put on film’ - F1 The Movie, in cinemas on June 25th and June 27th in North America.

Brad Pitt tells Tom Clarkson about making the movie, the ‘adrenaline’ he felt driving on spectacular Formula 1 circuits, what he learned from his time with Lewis Hamilton and how getting close to F1 cars and drivers took his breath away.

Plus, he reveals the true F1 stories which inspired the character of Sonny Hayes, describes the feeling of driving a real F1 car, and hints at his hopes for a sequel.

For more F1® videos, visit https://www.Formula1.com

Follow F1®:
https://www.instagram.com/F1
https://www.facebook.com/Formula1/
https://www.twitter.com/F1
https://www.twitch.tv/formula1
https://www.tiktok.com/@f1

#F1 #F1TheMovie
OFFICIAL_DISCLOSURE: false

PAGE (F1 - The Official Home of Formula 1® Racing):
F1 Homepage
FEATURED VIDEO
11:03
Haas take on the Grid Games Challenge | F1 Grid Games
2:25
The Cooldown Room - Did Luke Browning keep his Cooldown Laps leadership?
13:10
Jolyon Palmer's Analysis: Hamilton's first win for Ferrari
1:58
2026 Barcelona-Catalunya Grand Prix: The key VSC pit stop that helped seal Hamilton’s win
0:54
2026 Barcelona-Catalunya Grand Prix: Every overtake as Hadjar goes on a charge up to P6
2026 Season
2026 HIGHLIGHTS
7:57
Race Highlights: 2026 Barcelona-Catalunya Grand Prix
8:30
Formula 2 Highlights: 2026 Barcelona-Catalunya Feature Race
7:54
Formula 3 Highlights: 2026 Barcelona-Catalunya Feature Race
7:51
Qualifying Highlights: 2026 Barcelona-Catalunya Grand Prix
8:42
Formula 2 Highlights: 2026 Barcelona-Catalunya Sprint Race
```
</details>


### UCfbnTUxUech4P1XgYUwYuKA_Ib_lBfhO-qE_68043743

- gold: {"st1": "physical_goods", "st2": ["creator_community", "fashion"], "st3": ["inadequate_disclosure"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "today sponsors ah yeah miss upset over gamma subs GG and he's cocoa buns for 10% off your order"}]}
- pred: {"st1": "physical_goods", "st2": ["fashion"], "st3": ["undisclosed_advertising"]}
- errors: {"st2": {"missing": ["creator_community"], "extra": []}, "st3": {"missing": ["inadequate_disclosure"], "extra": ["undisclosed_advertising"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
out for three when we really slow we are fat I am today sponsors ah yeah miss upset over gamma subs GG and he's cocoa buns for 10% off your order also if you're among the first 200 people to claim the sample packs it's a link down below but only us customers only our second sponsor tonight once again thank you break on and also as always cool shirts and over two shirts with the Z cool and use code cold ones for temps enough today's guest is a big fat man

VIDEO: Twomad Goes to Bed | Cold Ones
DESCRIPTION:
🌈 Buy any of the clothes we're wearing for 10% off with the code 'COLDONES' at https://tinyurl.com/COLDONES
🥤 USE CODE COLDONES FOR 10% off GAMER SUPPS https://gamersupps.gg/?afmc=coldones
🎧Go to https://buyraycon.com/coldones FOR BLACK THEIR FRIDAY DEALS!!!

PLEDGE ON PATREON FOR THE EXTENDED VERSION: https://patreon.com/coldones

Check out @threemad 
_______________________________________________________________

SEND STUFF TO OUR PO BOX:

Cool Shirtz
Parcel Locker 10168 81071 
208 Riversdale Road
HAWTHORN VIC 3122


Audio!

Soundcloud⇨ https://tinyurl.com/twomadSC
Spotify⇨ https://tinyurl.com/twomadSF
iTunes⇨ https://tinyurl.com/twomadIT
_______________________________________________________________

♫“Eternity” Instrumental by Homage♫
https://tinyurl.com/y6lfdr7o










♫ Homage - Cold Ones Mix ♫

Featuring songs from his following albums:

90s Kids: http://bit.ly/2CC0zcX
Twenty-Five: http://bit.ly/2KbG4Iv
Aqua: http://bit.ly/2NHtxi9
OFFICIAL_DISCLOSURE: false

PAGE (Cool and epic):
Cool Shirtz
EUR
Select Currency
AUD
ALL L
AUD $
BAM КМ
BND $
CAD $
CHF CHF
CNY ¥
CZK Kč
DKK kr.
EUR €
GBP £
HKD $
HUF Ft
IDR Rp
ISK kr
JPY ¥
KHR ៛
KRW ₩
MDL L
MKD ден
MOP P
MYR RM
NOK kr
NZD $
PHP ₱
PLN zł
RON Lei
RSD РСД
SEK kr
SGD $
THB ฿
TWD $
UAH ₴
USD $
VND ₫
EUR €
0
Very Cool x Minecraft
Back In Stock
Tops
Bottoms
Accessories
Decor
Tops
Tees
Shirts
Longsleeves
Jumpers
Crop Tops
Outerwear
Bottoms
Accessories
Hats
Jewellery
Socks
Bags
Water Bottles
AirPod Cases
Masks
Pins
Decor
Desk Mats
Keycaps
Water Bottles
Art Toys
Sale
Close Menu
Very Cool x Minecraft
Back In Stock
Tops
Bottoms
Accessories
Decor
Tops
Tees
Shirts
Longsleeves
Jumpers
Crop Tops
Outerwear
Bottoms
Accessories
Hats
Jewellery
Socks
Bags
Water Bottles
AirPod Cases
Masks
Pins
Decor
Desk Mats
Keycaps
Water Bottles
Art Toys
Sale
LOGIN
Register Now
LOWEST PRICE
BEST SELLERS
NEW IN
TRENDING
50 reviews
XS
S
M
L
XL
2XL
3XL
diequik
€31,95
T-Shirt
AUD
Error
What are you looking for?
Submit
```
</details>


### UCN-JYa0sNXJ0osjqO--Dzcw_LhE7Pos43y8_931e1366

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics", "health"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "perfect match AI uses advanced technology that analyzes your face and perfectly matches you with the style of frames that fit your look"}]}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics", "health"], "st3": ["direct_exhortation"]}
- errors: {"st3": {"missing": ["misleading_claim"], "extra": ["direct_exhortation"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
talk about I guess yeah awkwardness out of the way let's get into today's video all right first things first yes what was that oh oh These oh yes I am so sorry sorry how silly of me yes ah yes these are these are glasses brought to you by today's sponsor glassesusa.com glasses USA is one of the largest prescription eyewear retailers in the United States they offer thousands and guys I mean thousands of top brands such as Oakley Gucci or these slick Ray bands what is going on I look like I should be riding a motorcycle somewhere on the east coast glassesusa.com is changing the game with their really cool new app perfect match a I it's like having a professional style you for glasses but even better perfect match AI uses advanced technology that analyzes your face and perfectly matches you with the style of frames that fit your look just like this ah see look at that and simple all you do use your phone to scan your face step two answer a couple of quick questions and perfect match does the rest the best part is it's completely free and you can do it from anywhere these are three frames that I was matched with comment down below how good these look mhm pretty neat huh I feel like I could freaking conquer the world in these things as someone who does content creation online I often am looking at screens and so finding the perfect pair of glasses to help me with the blue light problem in my life but also that helps me feel stylish was a great experience it beats going to the store if you're ready to find your perfect match today click on the link in the description and go to glassesusa.com glassesusa is giving my viewers only $10 off on top of any coupon or existing sale don't wait seize your deal and find your new favorite pair today thank you once again to glassesusa.com for sponsoring this video back to the wrapup all right July it's it's hard for me to

VIDEO: I Read Another 21 Books For This Video...
DESCRIPTION:
Find your perfect pair for free with GlassesUSA.com’s AI: https://glassesusa.me/IanGubeli_PairfectMatch (mobile only). Plus enjoy an extra $10 off with code IAN10, for order $100 or more, but act fast because this offer won’t last! 


Want to check out the frames featured?! Click below and enjoy even more crazy discounts👇🏽

The Geometric in Shiny Black: https://glassesusa.me/IanGubeli_Geometric 

Revel Sidestep in Black: https://glassesusa.me/IanGubeli_RevelSidestep 

Rayb-Ban Aviator Metal II in Gunmetal: https://glassesusa.me/IanGubeli_RayBan

In today's video, I read another 21 books for this video...Yes, that sounds repetitive, but it's just me talking about the 21 book I've read between the months of July and September. Stick around to see what books I talk about. Thanks for stopping by!

______________________

For business inquiries: treavor@smallscreenmarketing.com

______________________

Music:

"Gatefold" - https://www.epidemicsound.com/track/eYDxUfSQFn/
"Coniferous" - https://www.epidemicsound.com/track/SAs07G75qh/

______________________

Tags:

book haul, young adult, leigh bardugo, I Read Another 21 Books For This Video..., i read another 21 books for this video..., ian gubeli, ian gubeli stephen king, ian gubeli red rising, ian gubeli wife, ian gubeli reading vlogs, ian gubeli reading challenges, booktube, booktok, three month reading wrap up, monthly reading wrap up, reading wrap up, july reading wrap up, august reading wrap up, september reading wrap up, haley pham, ashlynn calee, haley pham vlogs, stephen king
OFFICIAL_DISCLOSURE: true

PAGE (Dusty Decks - Gatefold | Epidemic Sound):
0:002:12
- 3:5878 BPM
- 2:1188 BPM
- 2:2581 BPM
- 2:1483 BPM
- 2:0976 BPM
- 2:1765 BPM
- 3:2584 BPM
- 2:1386 BPM
- 2:0974 BPM
- 2:0475 BPM
Want more music?
Explore our full catalog with 55,000 tracks and over 250,000 sound effects
Create free accountExplore our full catalog with 55,000 tracks and over 250,000 sound effects
Create free account
```
</details>


### UCFPElAbES8GHfBZrDrGbSLQ_7pcwHjS_iqM_63e0eb35

- gold: {"st1": "physical_services", "st2": ["health"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "meeting with a therapist to work on your mental health is just as helpful as hiring a personal trainer to work on your physical health and the positive impact can be just as life changing"}, {"flag": "misleading_claim", "quote": "whether you struggle with anxiety depression self-doubt or anything else talkspace gives you the access to the help you need to move forward"}, {"flag": "misleading_claim", "quote": "your privacy and security are the number one priority"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["health"], "st3": ["undisclosed_advertising", "misleading_claim"]}
- errors: {"st1": {"gold": "physical_services", "pred": "digital_content_or_services"}, "st3": {"missing": [], "extra": ["undisclosed_advertising"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
topic yeah go for it i'm still gonna look but you're not gonna find it bro this podcast is sponsored by talkspace meeting with a therapist to work on your mental health is just as helpful as hiring a personal trainer to work on your physical health and the positive impact can be just as life changing meeting with a therapist should be as ordinary and judgment-free as going to the dentist or getting a personal trainer i love that talkspace makes it easy to connect with a therapist privately and that's your message whenever you need to it's all the benefits of therapy without the hassle of settling assessing appointments and waiting a week or more between conversations if you've wondered about therapy but aren't sure where to start you need to check out talkspace at talkspace your privacy and security are the number one priority the app puts you in a private room with just you and your therapist you can send messages 24 7 and get replies throughout the day so no need to wait for a weekly appointment and talk space encryption and added security features uh keep your conversation fully protected so whether you struggle with anxiety depression self-doubt or anything else talkspace gives you the access to the help you need to move forward facing those obstacles isn't easy and you don't win a prize for doing it alone getting professional help isn't weird all week it's smart because sure your friend might know a thing or two about electricity but you wouldn't let him rewire your house so don't leave your mental health to chance or the amateur advice of well-meaning friends and family talk to someone who's trained to help you make lasting progress join top space today and start moving toward with a single uh sorry moving forward with a single message just visit talkspace.com and get a hundred dollars off your first month when you use the promo code what's good at sign up that's 100 off at talkspace.com promo code what's good yes i go to talkspace.com and use code what's good to get a hundred dollars off your first month now back to the christmas set okay so

VIDEO: What’s Good Christmas Special!! (Ep134)
DESCRIPTION:
Go to http://talkspace.com and use code WHATSGOOD to get $100 off your first month!

Our insta: https://www.instagram.com/whatsgoodcast/

Listen to the full podcast here: http://fanlink.to/WhatsGood

Miniminter: http://youtube.com/miniminter
Randolph: http://youtube.com/officialrandolph
OFFICIAL_DISCLOSURE: false

PAGE (Talkspace - #1 Rated Online Therapy, 1 Million+ Users):
Space to figure things out
- Convenient access anytime, anywhere
- Professional support from licensed therapists
- Flexible options tailored to your needs and budget
Therapy covered by insurance
- Most insured members have a $0 copay
- Licensed therapists available as soon as today
- Therapy sessions over video, voice or chat (your choice)
Research-backed therapy, covered by insurance
- Backed by 30+ peer-reviewed studies
- 80% say it's as or more effective as in-person therapy
- Covered by most major insurance plans
Virtual therapy that works
- Match with a licensed therapist as soon as today
- 98% of members find it more convenient than in-person therapy
- Most pay $0 with insurance
Trusted by over 1 million members
- 5,600+ licensed therapists and providers
- over 60,000 5-star reviews
- Covered by most major insurance plans
Most insured members have a $0 copay
Choose your insurer to learn more:
What’s included with Talkspace
*May vary by insurance coverage
More than 60,000
5-star reviews
Read why people love using Talkspace.
See all reviews
How Talkspace works
Hormonal shifts, evolving identities, and societal expectations that accompany certain life stages can powerfully impact women’s mental health. We created Chapters to quickly connect women with mental health care providers with expertise in their needs, providing fast access to specialized therapy and psychiatry.
Learn moreExperts in virtual mental health care
Comprehensive treatment with therapy and psychiatry
Combining therapy and medication has been proven to bring the best results for most mental health conditions.
Talkspace vs. In-person
In-person
A therapist licensed in your state
No parking fees or lost travel time
Meet the Talkspace licensed providers
Our network of therapists and psychiatric providers have specialization in 150+ conditions, treatment approaches, and mental health needs.
High-quality care backed by evidence
Talkspace partners with major research institutions to validate the quality of our treatment methods.
70%
saw improvement of anxiety or depression symptoms within 3 months.
80%
reported Talkspace was as or more effective than face-to-face therapy.
98%
found Talkspace to be more convenient than face-to-face therapy.
Any questions?
Find trust-worthy answers on all things mental health at Talkspace.
How much is Talkspace online therapy?
Talkspace makes online therapy convenient, accessible, and, also importantly, affordable. Cost depends on how you pay: through US health insurance, Medicare, EAP, employer, organization, or out-of-pocket. Many employers cover Talkspace for free, either directly with an employer code or through an Employee Assistance Plan (EAP). Most major health insurance plans cover Talkspace therapy, and if your plan does you’ll likely only pay a copay (typically $15). If you pay out-of-pocket Talkspace therapy plans begin at $69/week.
Does insurance cover online therapy?
Typically, yes. Talkspace is in-network with many major insurance plans, and most insured members have a $0 copay. Our extensive network ensures you can get the treatment you need without worrying about cost. So Talkspace therapy may be covered by your employer’s healthcare plan. Or you may receive it for free as a direct benefit from your employer. Coverage will depend on your insurance company and health plan. Some of the mental health services most often covered include: talk therapy, co-occurring behavioral health and medical conditions, psychiatric emergency care, and medication management. Learn more about insurance coverage for online therapy.
Is online therapy effective?
Online therapy is proven to be as effective, if not more effective than face-to-face therapy. A study conducted by Talkspace & the Journal of Telemedicine and e-Health showed that text-based therapy through Talkspace was highly effective and comparable to traditional therapy. Talkspace also generated greater satisfaction in terms of its delivery, accessibility, and affordability. With online therapy, you’re able to access a wider range of mental health professionals and receive high-quality, evidence-based care from wherever you are. Learn more with Talkspace research.
What is the difference between therapy and psychiatry?
Therapy and psychiatry can both play an important role in your mental health treatment plan. In therapy, licensed therapists work with you to discuss personal challenges and devise a personalized plan, but they aren't able to prescribe medication. A therapist will help to understand your feelings, provide support, and help create a plan for the future.
Psychiatry is a medical specialty that prescribes and monitors medication to treat mental health symptoms. Psychiatrists and psychiatric providers are licensed medical providers who specialize in mental health treatment and can provide psychiatric care services and personalized medication management. Talkspace connects you with an online psychiatric provider within a week, for an evaluation, prescription, and ongoing care.
How do I get matched with a therapist?
After you answer a few online questions about your symptoms and preferences you’ll be matched with a therapist who is licensed in your state and who is likely to be a good fit for your needs. Talkspace therapists are a diverse group with a wide range of specializations. After receiving your personalized match, you’ll be able to communicate with your licensed therapist through text, audio, or video. If you don’t click with your therapist, it’s easy to switch. Learn how to change providers
```
</details>


### UCrEUTzd1W__Y5Sb5vSbuZ5g_6QyJmhuQZKw_a82ee5e2

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "they without a doubt make the world's greatest phone mount"}]}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["no_flag"]}
- errors: {"st3": {"missing": ["misleading_claim"], "extra": ["no_flag"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
make driving this thing daily just so much better it was so bad and you know what that's a perfect time to think this video sponsor proclip USA they without a doubt make the world's greatest phone mount let me show you this thing it's not going to look like any other phone mount because it's not like any other phone [Music] mount let me talk to you about it you can tell that I'm genuinely excited about this project because let's be honest you can go to your local Walmart and pick up a mediocre suction cup or vent mounted phone holder and it will work it will maybe charge your phone might open automatically but it's going to be flimsy and it's going to last like a year especially in our daily drivers bone mounts are so important it's something you don't think about but after getting a nice one it is lifechanging why not spend just a little bit extra to get a really high quality piece and that's where Pro clip USA comes into play pro clip USA specializes in high quality two-part phone mounts now the way the two-part system works is that for one you have a base and that base is vehicle specific it's not suction cut mounted it's not vent mounted it's not cup holder mounted it's designed to clip somewhere on your interior whether that be the a pillar like this one is some are designed to clip into your dash but it's made for your specific vehicle so it fits perfectly and it's super sturdy but it's easy to install and it's mounted just with double-sided tape and clips no screws so you don't have to mess up your factory interior and then to attach to the base you have a phone specific Mount now they have a ton of different options to fit every single phone and every single phone case they also have wireless charging and believe it or not my actual favorite thing is wired charger it essentially just has a wire mounted onto the phone charger and as you slide your phone in it plugs it in now the reason why I like that more than wireless charging is because wireless charging Heats your phone up a lot but with the wired charging I've never had that issue and so together those two parts make a complete Pro clip USA mounting solution and it's freaking awesome so if you guys are tired of your cheap and flimsy phone holder check out Pro clip USA and build your new Mount to death I'll have a link in the description and up there in the cards check it out if you're interested huge thank you to Pro clip for sponsoring this video and now well one week later thanks FedEx our motor mounts

VIDEO: This Modification Will RUIN Your Daily Driver... (Don't Do It Unless You HAVE TO!)
DESCRIPTION:
Upgrade your phone mount today! Get 15% off ProClip USA custom car phone mounts with code: GINGIUM https://bit.ly/3xK0cwM. Today we install upgraded motor mounts on the Turbo Honda Fit. Upgraded motor mounts greatly improve shifting & other driving characteristics, but, also greatly increase vibrations leading to an uncomfortable ride. In my opinion, they should only be installed on your daily driver if its ABSOLUTELY necessary...

SUPPORT ME HERE! ► https://www.patreon.com/Gingium

OTHER VIDS!!
Quick Builds► https://youtube.com/playlist?list=PLmg4g_Vt8FJVS7igJ0Hoa13QBBjsOB1-w
Drift Truck ► https://youtube.com/playlist?list=PLmg4g_Vt8FJWx9lk6SN2Xf_LI7Lq9iM0r
Rally Miata ► https://youtube.com/playlist?list=PLmg4g_Vt8FJW649AYWxYawDUtX92Tg-JG
Eclipse ► https://youtube.com/playlist?list=PLmg4g_Vt8FJWoxr7cAo60Lp5pGHv-4QfC
LS Volvo ► https://youtube.com/playlist?list=PLmg4g_Vt8FJW-U7vgcFq0ecgRZErTOcyX

BE MY FRIEND!!!! 
Follow me on Twitter ► https://twitter.com/_Gingium_
Follow me on Instagram ► https://www.instagram.com/gingium/

MY RECORDING EQUIPMENT!!
Camera ► https://amzn.to/3lVq7J9
Lens ► https://amzn.to/3yhf168
Microphone ► https://amzn.to/3q4pv5x
Tripod ► https://amzn.to/3pOGiZR
Carry Bag ► https://amzn.to/3rV50uz
SD Card  ► https://amzn.to/3lQdv68

MY FABRICATION/MECHANIC EQUIPMENT!!
Welders & Supplies ► https://www.usaweld.com/?Click=67190 (code: GINGIUM)
CNC Plasma Table ► https://store.langmuirsystems.com?aff=23 (code: GINGIUM)
Tube Bender ► https://www.roguefab.com/ (code: gingium25)
OFFICIAL_DISCLOSURE: true

PAGE (Custom Car Phone Mounts & Holders):
Black Edition
Magnetic Golf Cart Phone Mount
- MagSafe & Qi2 Compatible
- Fits Any Golf Cart Frame
- Tool-Free 3-Second Install
30-Day Returns
1-Year Warranty
Free US Shipping
Mounting Expertise
Proven Durability
Unmatched Lead Times
Your Car. Your Phone. A Perfect Fit.
ProClip custom-fit mounts and holders built for your car's exact trim. No suction cups, no vent clips, no wobble. Just a trusted hold.
Shop by Category
Every ProClip mount is engineered for your exact vehicle trim and phone model — no guessing, no adapters, no wobble.
For Business & Fleet
Equip Your
Entire Fleet
Built for the demands of fleet vehicles, ProClip delivers secure, consistent phone and tablet mounting trusted for over 20 years by independent contractors, growing businesses, and enterprise fleets.
Pick your fleet vehicle. Build your mount.
Golf Cart Phone Mounts
Four styles, one precision magnetic hold. Choose the edition that matches your game.
Magnetic Golf Cart Phone Mount
Magnetic Golf Cart Phone Mount
Magnetic Golf Cart Phone Mount
Magnetic Golf Cart Phone Mount
Tired of phone mounts that wobble in your vents, block your view, or fall off mid-drive? ProClip snaps directly into your car dashboard and stays put — every road, every ride.
ProClip is made specifically for your year, make, and model — not a universal phone mount with foam pads and crossed fingers. It snaps into your dashboard like it was always supposed to be there.
No suction cups hanging from your windshield. No flimsy vent clip blocking your AC. ProClip blends right into your dash — clean, solid, and exactly where you want your phone.
Install takes about five minutes. After that, your cell phone mount just works — no rattles, no readjusting, no picking it up off the floor at a red light. Solid hold, every single drive.
Got a new phone? Just swap the holder — your dashboard base stays put. New car? Keep your holder and grab a new base. You never have to start from scratch.
Swipe to explore
ProClip is made specifically for your year, make, and model — not a universal phone mount with foam pads and crossed fingers. It snaps into your dashboard like it was always supposed to be there.
No suction cups hanging from your windshield. No flimsy vent clip blocking your AC. ProClip blends right into your dash — clean, solid, and exactly where you want your phone.
Install takes about five minutes. After that, your cell phone mount just works — no rattles, no readjusting, no picking it up off the floor at a red light. Solid hold, every single drive.
Got a new phone? Just swap the holder — your dashboard base stays put. New car? Keep your holder and grab a new base. You never have to start from scratch.
Got Questions? We've Got Answers.
Everything you need to know about your custom dashboard phone mount — compatibility, installation, returns, and warranty.
```
</details>


### UC4G10tk3AHFuyMIuD3rHOBA_AXU40tVIxT4_9eab2229

- gold: {"st1": "digital_content_or_services", "st2": ["creator_community", "other"], "st3": ["undisclosed_advertising"], "st3_evidence": [{"flag": "undisclosed_advertising", "quote": "MERCH\n\nhttps://rdcworld1.com/collections/all"}]}
- pred: {"st1": "physical_goods", "st2": ["creator_community"], "st3": ["undisclosed_advertising"]}
- errors: {"st1": {"gold": "digital_content_or_services", "pred": "physical_goods"}, "st2": {"missing": ["other"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:


VIDEO: VIDEO GAME HOUSE 2
DESCRIPTION:
Music Video Akillez, Tory Lanez:
https://www.youtube.com/watch?v=fF87Cq2Uh58

Video Game House 2 Is the second installment of Video Game House 1 where video game characters living together all under one roof! Mario, Luigi, Sora, Link, And Chief Try to Make A Living!

~RDC Social Media ~

@RDCWorld1
Mark Phillips - @SupremeDreams_1
Affiong Harris - @CleanUniform
Desmond Johnson - @l0v3andpeac3
Leland Manigo - @23_Is_Leland
Dylan Patel - @dylanpatel4_
Benjamin Skinner - @Ive_Ben_Jammin
Johnathan Newton - @playthatjohn

MERCH

https://rdcworld1.com/collections/all

GAMING CHANNEL

https://www.youtube.com/channel/rdcworldgaming

TWITCH CHANNEL

https://www.twitch.tv/rdcgaming

DREAM CON INFO!

https://www.dreamconvention.com

DISCORD

https://discord.gg/dVT5jSu

SOUNDCLOUD

https://soundcloud.com/user-713063081
OFFICIAL_DISCLOSURE: false

PAGE (Products):
Skip to content
Log in
Home
Shop
About
Contact
Facebook
Instagram
YouTube
TikTok
Twitter
Need help? call us
members@rdcworld1.com
Home
Shop
About
Contact
Log in
€0,00
Total €0,00 in cart
Home
Collections
Products
Products
Filter and Sort
1 product
Gift Card
Regular price
From €8,95 EUR
+ 3
and 3 more
Filter and Sort
Availability
Availability
In stock (1)
In stock (1 product)
Out of stock (0)
Out of stock (0 products)
Read more
Read less
Sort by
Featured
Most relevant
Best selling
Alphabetically, A-Z
Alphabetically, Z-A
Price, low to high
Price, high to low
Date, old to new
Date, new to old
Didn't find the product you were looking for?
Search
Featured Categories
Collection title
Collection title
Collection title
Collection title
Collection title
TOP
Clear
Search
Popular searches
rdcworld1
rdcworld
dream con
dreamcon
dream con 2026
You may like
View cart
Your cart is empty
Continue shopping
Have an account?
Log in
to check out faster.
You may like
Clear
Country/region
Netherlands | EUR €
Afghanistan
(AFN ؋)
Åland Islands
(EUR €)
Albania
(ALL L)
Algeria
(DZD د.ج)
Andorra
(EUR €)
Angola
(USD $)
Anguilla
(XCD $)
Antigua & Barbuda
(XCD $)
Argentina
(USD $)
Armenia
(AMD դր.)
Aruba
(AWG ƒ)
Ascension Island
(SHP £)
Australia
(AUD $)
Austria
(EUR €)
Azerbaijan
(AZN ₼)
Bahamas
(BSD $)
Bahrain
(USD $)
Bangladesh
(BDT ৳)
Barbados
(BBD $)
Belarus
(USD $)
Belgium
(EUR €)
Belize
(BZD $)
Benin
(XOF Fr)
Bermuda
(USD $)
Bhutan
(USD $)
Bolivia
(BOB Bs.)
Bosnia & Herzegovina
(BAM КМ)
Botswana
(BWP P)
Brazil
(USD $)
British Indian Ocean Territory
(USD $)
British Virgin Islands
(USD $)
Brunei
(BND $)
Bulgaria
(EUR €)
Burkina Faso
(XOF Fr)
Burundi
(BIF Fr)
Cambodia
(KHR ៛)
Cameroon
(XAF CFA)
Canada
(CAD $)
Cape Verde
(CVE $)
Caribbean Netherlands
(USD $)
Cayman Islands
(KYD $)
Central African Republic
(XAF CFA)
Chad
(XAF CFA)
Chile
(USD $)
China
(CNY ¥)
Christmas Island
(AUD $)
Cocos (Keeling) Islands
(AUD $)
Colombia
(USD $)
Comoros
(KMF Fr)
Congo - Brazzaville
(XAF CFA)
Congo - Kinshasa
(CDF Fr)
Cook Islands
(NZD $)
Costa Rica
(CRC ₡)
Côte d’Ivoire
(XOF Fr)
Croatia
(EUR €)
Curaçao
(ANG ƒ)
Cyprus
(EUR €)
Czechia
(CZK Kč)
Denmark
(DKK kr.)
Djibouti
(DJF Fdj)
Dominica
(XCD $)
Dominican Republic
(DOP $)
Ecuador
(USD $)
Egypt
(EGP ج.م)
El Salvador
(USD $)
Equatorial Guinea
(XAF CFA)
Eritrea
(USD $)
Estonia
(EUR €)
Eswatini
(USD $)
Ethiopia
(ETB Br)
Falkland Islands
(FKP £)
Faroe Islands
(DKK kr.)
Fiji
(FJD $)
Finland
(EUR €)
France
(EUR €)
French Guiana
(EUR €)
French Polynesia
(XPF Fr)
French Southern Territories
(EUR €)
Gabon
(XOF Fr)
Gambia
(GMD D)
Georgia
(USD $)
Germany
(EUR €)
Ghana
(USD $)
Gibraltar
(GBP £)
Greece
(EUR €)
Greenland
(DKK kr.)
Grenada
(XCD $)
Guadeloupe
(EUR €)
Guatemala
(GTQ Q)
Guernsey
(GBP £)
Guinea
(GNF Fr)
Guinea-Bissau
(XOF Fr)
Guyana
(GYD $)
Haiti
(USD $)
Honduras
(HNL L)
Hong Kong SAR
(HKD $)
Hungary
(HUF Ft)
Iceland
(ISK kr)
India
(INR ₹)
Indonesia
(IDR Rp)
Iraq
(USD $)
Ireland
(EUR €)
Isle of Man
(GBP £)
Israel
(ILS ₪)
Italy
(EUR €)
Jamaica
(JMD $)
Japan
(JPY ¥)
Jersey
(USD $)
Jordan
(USD $)
Kazakhstan
(KZT ₸)
Kenya
(KES KSh)
Kiribati
(USD $)
Kosovo
(EUR €)
Kuwait
(USD $)
Kyrgyzstan
(KGS som)
Laos
(LAK ₭)
Latvia
(EUR €)
Lebanon
(LBP ل.ل)
Lesotho
(USD $)
Liberia
(USD $)
Libya
(USD $)
Liechtenstein
(CHF CHF)
Lithuania
(EUR €)
Luxembourg
(EUR €)
Macao SAR
(MOP P)
Madagascar
(USD $)
Malawi
(MWK MK)
Malaysia
(MYR RM)
Maldives
(MVR MVR)
Mali
(XOF Fr)
Malta
(EUR €)
Martinique
(EUR €)
Mauritania
(USD $)
Mauritius
(MUR ₨)
Mayotte
(EUR €)
Mexico
(USD $)
Moldova
(MDL L)
Monaco
(EUR €)
Mongolia
(MNT ₮)
Montenegro
(EUR €)
Montserrat
(XCD $)
Morocco
(MAD د.م.)
Mozambique
(USD $)
Myanmar (Burma)
(MMK K)
Namibia
(USD $)
Nauru
(AUD $)
Nepal
(NPR Rs.)
Netherlands
(EUR €)
New Caledonia
(XPF Fr)
New Zealand
(NZD $)
Nicaragua
(NIO C$)
Niger
(XOF Fr)
Nigeria
(NGN ₦)
Niue
(NZD $)
Norfolk Island
(AUD $)
North Macedonia
(MKD ден)
Norway
(USD $)
Oman
(USD $)
Pakistan
(PKR ₨)
Palestinian Territories
(ILS ₪)
Panama
(USD $)
Papua New Guinea
(PGK K)
Paraguay
(PYG ₲)
Peru
(PEN S/)
Philippines
(PHP ₱)
Pitcairn Islands
(NZD $)
Poland
(PLN zł)
Portugal
(EUR €)
Qatar
(QAR ر.ق)
Réunion
(EUR €)
Romania
(RON Lei)
Russia
(USD $)
Rwanda
(RWF FRw)
Samoa
(WST T)
San Marino
(EUR €)
São Tomé & Príncipe
(STD Db)
Saudi Arabia
(SAR ر.س)
Senegal
(XOF Fr)
Serbia
(RSD РСД)
Seychelles
(USD $)
Sierra Leone
(SLL Le)
Singapore
(SGD $)
Sint Maarten
(ANG ƒ)
Slovakia
(EUR €)
Slovenia
(EUR €)
Solomon Islands
(SBD $)
Somalia
(USD $)
South Africa
(USD $)
South Georgia & South Sandwich Islands
(GBP £)
South Korea
(KRW ₩)
South Sudan
(USD $)
Spain
(EUR €)
Sri Lanka
(LKR ₨)
St. Barthélemy
(EUR €)
St. Helena
(SHP £)
St. Kitts & Nevis
(XCD $)
St. Lucia
(XCD $)
St. Martin
(EUR €)
St. Pierre & Miquelon
(EUR €)
St. Vincent & Grenadines
(XCD $)
Sudan
(USD $)
Suriname
(USD $)
Svalbard & Jan Mayen
(USD $)
Sweden
(SEK kr)
Switzerland
(CHF CHF)
Taiwan
(TWD $)
Tajikistan
(TJS ЅМ)
Tanzania
(TZS Sh)
Thailand
(THB ฿)
Timor-Leste
(USD $)
Togo
(XOF Fr)
Tokelau
(NZD $)
Tonga
(TOP T$)
Trinidad & Tobago
(TTD $)
Tristan da Cunha
(GBP £)
Tunisia
(USD $)
Türkiye
(USD $)
Turkmenistan
(USD $)
Turks & Caicos Islands
(USD $)
Tuvalu
(AUD $)
U.S. Outlying Islands
(USD $)
Uganda
(UGX USh)
Ukraine
(UAH ₴)
United Arab Emirates
(AED د.إ)
United Kingdom
(GBP £)
United States
(USD $)
Uruguay
(UYU $U)
Uzbekistan
(UZS so'm)
Vanuatu
(VUV Vt)
Vatican City
(EUR €)
Venezuela
(USD $)
Vietnam
(VND ₫)
Wallis & Futuna
(XPF Fr)
Western Sahara
(MAD د.م.)
Yemen
(YER ﷼)
Zambia
(USD $)
Zimbabwe
(USD $)
View details
Join the Dream Gang
Subscribe now and get 15% off your first purchase!
00
d
:
00
h
:
00
m
Enter your email
Subscribe
Facebook
Instagram
YouTube
TikTok
Twitter
Are you sure?
Yes
No
Choosing a selection results in a full page refresh.
Opens in a new window.
```
</details>


### UCtuLEGI-JkI6VFCW-5ZYtbw_xxZhHxBNn5Y_6912414b

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics", "other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "The NextG upgraded hybrid mesh addressed seat provides 30% more breathability and reduces hip pressure by 20%."}]}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics", "other"], "st3": ["no_flag"]}
- errors: {"st3": {"missing": ["misleading_claim"], "extra": ["no_flag"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
just need to talk to somebody about it. So, without further ado, let's just get into it. But before we get into today's video, I want to thank today's video sponsor, Flexispot. Now, Flexispot has been a longtime friend of the channel and has always been my go-to for my office furniture, like standing desks. But today, I'm here to talk to you about their C7 Morpher office chair. One thing about me is I value a good office chair because I have my booty in one more often than not. Between working my full-time job and then doing YouTube stuff and then playing video games, I need something that will keep me feeling supported and comfortable for a long, long time during the day. I'm currently in the C7 Morpher chair and I plan to be in it for the foreseeable future because it is very comfortable. C7 Morpher offers Flexi Spots flex lean technology in the back rest which is precision engineered to gently wrap around your upper back. It can adjust up to 10° forward to adjust to your sitting style, keeping your shoulders and your upper back supported all day. It also features the air lumbar support technology in the lower back and it can be inflated to adjust to your needs and the angle can also be adjusted to your preferences. The lumbar support also like moves with you as you as you recline. Unlike other chairs with this function, your back will still be perfectly supported when reclining. The NextG upgraded hybrid mesh addressed seat provides 30% more breathability and reduces hip pressure by 20%. And I can tell you as someone who like the pain begins in her hips with a bad chair, I can tell you that this chair is extremely comfortable and very very nice on my hips. It also has 5D armrests which I have talked about Flexis Spot office chairs before and this is one of my favorite features of their chairs. These move literally like all the way around and I could adjust them as much as I need to so that my elbows feel supported the whole time and I don't experience any pain. And it also has a foot rest which I love because I love sitting criss-cross applesauce at my desk and this makes it very easy because I am 5'8 so my legs are a little bit long and so uh I can't typically sit like that in like just the chair. So it's really nice to have the additional uh foot rest to do that with. Spot also offers a 10-year warranty uh with direct replacement for damaged parts and a 30-day free return policy. So, there's really nothing to lose with trying a Flexis Spot product. So, if you want to upgrade your workspace with Flexis Spot like I did, be sure to not miss their huge Labor Day sale and use the link down below in my description as well as my code C750 to save $50 off the Flexis Spot C7 Max chair. Thank you so much to Flexispot for being a continued sponsor of this channel. And as always, thank you to you guys for continuing to interact with my content so that brands like Flexispot want to keep working with me. Okay, now let's get back into the video. So, like I said, I'm going to be

VIDEO: The Rise of Being a Bad Mom for Views
DESCRIPTION:
Upgrade Your Workspace with flexispot! Don’t miss FlexiSpot’s huge Labor Day sale! Enter my exclusive code 'C750' and save $50 on the C7Max chair! Shop through
Flexispot C7Max Chair：https://bit.ly/4oHwyhL -us
https://bit.ly/41NlXbg -ca

My Nail Girlie: https://www.instagram.com/aspirenailcarestudio

Business Inquiries: megananne@makrwatch.com

S O C I A L S:
Instagram: https://www.instagram.com/heylookitsmegan/
TikTok: heylookitsmegan1
Twitter (for some ~more~ spicy takes): @heylookitsmegan
Twitch (coming soon!): https://www.twitch.tv/heylookitsmegan

S U P P O R T (if ya want) 
Amazon Storefront: https://www.amazon.com/shop/megananne?ref_=cm_sw_r_cp_ud_aipsfshop_aipsfmegananne_SGPQ6P0XA4T8ZTNVS4ZF
Merch Store: https://megananne.creator-spring.com/
My Etsy Store: https://www.etsy.com/shop/MadeStation
Etsy Store Instagram: https://www.instagram.com/madestation/

H A N G O U T:
Discord: https://discord.gg/jzF92M5
OFFICIAL_DISCLOSURE: true

PAGE (Professional Ergonomic Office Chair | Comfortable Chair C7M | Flexispot):
Best for Long Time Sitting: Why the C7 Max is Effective
Two Seats, One Goal: Unmatched Comfort for Extended Work
Eco-Friendly 0.2" Latex Seat Cushion
The latex cushion offers firm, breathable comfort and lasting support. SGS and CA Prop 65 certified
for a safe, non-toxic seating experience.
DuPont Mesh for Pro-Level Comfort
Crafted with premium DuPont mesh for lasting elasticity and superior breathability. Provides firm,
adaptive support that keeps you cool and comfortable all day.
```
</details>


### UCCqEeDAUf4Mg0GgEN658tkA_rrKVM7gI7zY_17ada26e

- gold: {"st1": "physical_goods", "st2": ["food"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "factor makes meeting your nutrition goals easier than ever"}, {"flag": "misleading_claim", "quote": "their team of gourmet chefs create each meal using only ingredients with Integrity to help you feel your best all day long"}, {"flag": "misleading_claim", "quote": "if you're ready to feel your best while making the most out of your summer Adventures you can stick to your Wellness goals with premium Ready-to-Eat meals"}]}
- pred: {"st1": "physical_goods", "st2": ["food", "health"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": [], "extra": ["health"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
games except in very rare cases like when I play a game that's essentially perfect but before we go any further I do want to give a special thank you to the sponsor for this video factor factor makes meeting your nutrition goals easier than ever by delivering fresh never frozen dietitian-approved meals right to your doorstep their team of gourmet chefs create each meal using only ingredients with Integrity to help you feel your best all day long if you're ready to feel your best while making the most out of your summer Adventures you can stick to your Wellness goals with premium Ready-to-Eat meals featuring high quality ingredients such as broccolini leeks and asparagus you can treat yourself to 34 plus weekly restaurant quality options like bruschetta shrimp risotto Green Goddess chicken and Grill grilled Steakhouse filet mignon ready in just two minutes and if you're too busy with summer plans to cook and you want to make sure you're eating well with Factor you can skip the extra trip to the grocery store and The Chopping prepping and cleaning up too while still getting the flavor and nutritional quality you need factors fresh never frozen meals already in just two minutes so all you have to do is heat and enjoy then get back outside and soak up the warm weather and for us Factor has helped cut down on grocery shopping significantly which really saves us a lot of time and energy plus the food is really good so head to factor75.com or click the link below and use the code stuckman 50 to get 50 off your first Factor box that's factor75.com and the code is stuckman 50 to get 50 off your first Factor box that link is in the description below thank you so much to factor for sponsoring this video first off I have to

VIDEO: The Legend of Zelda: Tears of the Kingdom - Game Review
DESCRIPTION:
Thanks to Factor for sponsoring. Use code STUCKMANN50 to get 50% off your first Factor box at https://bit.ly/3oi7QtG

Chris Stuckmann reviews The Legend of Zelda: Tears of the Kingdom.
OFFICIAL_DISCLOSURE: true

PAGE (Factor):
A flexible menu every week
with something for everyone
Simply select meals after checkout or
Calorie Smart
~550kcal or less per serving
Chef’s Choice
Widest variety of clean, chef-crafted meals
Keto
Low carb high fat meals
High Protein
30 grams of protein or more per serving
Carb Conscious
35 grams of total carbs or less per serving
GLP-1 Balance
Protein-forward, calorie-friendly meals
Fiber Filled
6 grams of fiber or more per serving
Flexitarian
Balanced meals with veggies & purposeful proteins
Breakfast
Energizing breakfasts to start your day right
Smoothies & Juices
Dozens of options to sip, savor, & thrive
Snacks
Nutritious treats to help you fuel up on the go
Special discount for heroes!Get the offer
```
</details>

