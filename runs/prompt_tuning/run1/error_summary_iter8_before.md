# Error summary (8 instance(s) with at least one error)

## Per-tier error counts

- st1: 0/8
- st2: 4/8
- st3: 7/8

## st2 missing labels (gold had it, prediction missed it)

- hardware_electronics: missing 2x
- other: missing 2x

## st2 extra labels (prediction hallucinated, not in gold)

- apps: extra 2x
- financial: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- other -> apps: 2x
- other -> financial: 1x

## st3 missing labels (gold had it, prediction missed it)

- no_flag: missing 4x
- insufficient_context: missing 1x
- hfss_food_marketing: missing 1x

## st3 extra labels (prediction hallucinated, not in gold)

- misleading_claim: extra 5x
- direct_exhortation: extra 3x
- inadequate_disclosure: extra 3x
- undisclosed_advertising: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- no_flag -> misleading_claim: 4x
- no_flag -> direct_exhortation: 2x
- insufficient_context -> undisclosed_advertising: 1x
- no_flag -> inadequate_disclosure: 1x
- hfss_food_marketing -> direct_exhortation: 1x
- hfss_food_marketing -> inadequate_disclosure: 1x
- hfss_food_marketing -> misleading_claim: 1x

## Detailed error instances

### UCB_qr75-ydFVKSF9Dmo6izg_2MXkf8S44Bs_97d2f417

- gold: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["insufficient_context"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["undisclosed_advertising"]}
- errors: {"st2": {"missing": ["other"], "extra": ["apps"]}, "st3": {"missing": ["insufficient_context"], "extra": ["undisclosed_advertising"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
we'll be back with more tech talk and exciting equipment to discuss i'm sure in the next episode

VIDEO: Albert Fabrega's Tech Demo | Crash Safety | F1 TV Tech Talk
DESCRIPTION:
Albert Fabrega and Rosanna Tennant go through the modern safety standards of Formula 1, including crash helmets and seat belts.

This excerpt is taken from Tech Talk - watch the full episode on F1 TV, available globally for all subscribers - https://f1.com/GB22-TechTalk

For more F1® videos, visit http://www.Formula1.com

Follow F1®:
http://www.instagram.com/F1
https://www.facebook.com/Formula1/
http://www.twitter.com/F1
https://www.twitch.tv/formula1
https://www.tiktok.com/@f1

#F1
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


### UCHdos0HAIEhIMqUc9L3vh1w_2stDaPz5vOI_a94840dc

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["inadequate_disclosure", "direct_exhortation", "misleading_claim"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["direct_exhortation", "inadequate_disclosure", "misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
anything else. What the? Come on, man. I suck at 
gaming. You don't suck at gaming. Your monitor just sucks. Yeah, well, I can't get a new monitor. 
I'm broke. You spent $2,500 on food delivery last month. Whatever. Either way, I'd have to drop 
a ton of cash just to get a decent monitor. Not with Pixio. Pixio has a huge assortment of 
high-performance gaming monitors with insane refresh speeds at costs that won't break the 
bank. This is awesome. I'm going to order some food. Ooh yeah, give me some hot wings. Head on 
over to pixogaming.com and level up today. Hey, thanks for watching and supporting Independent 
Animation. If you want to see more from Dorkley,

VIDEO: If Video Games Were 7% More Realistic
DESCRIPTION:
Watch it, Star Fox!
Head over to https://pixiogaming.com today!

Keep Dorkly independent by subscribing to our channels:
https://patreon.com/dorkly
https://www.youtube.com/dorkly
https://www.youtube.com/lowbrowstudios

Check out the new DORKLY store: https://shop.dorkly.com

Subscribe to Dorkly's new podcast - THIS WEEK IN NERD HISTORY!
YouTube - https://www.youtube.com/playlist?list=PLmsMGFIWAJdJcBIRoZxKl34TvomT0oxem
Spotify - https://open.spotify.com/show/0Mfaftkb5WT7j9MJ60kfxi
Apple Podcasts - https://apple.co/4gmIl11

WRITTEN BY
Mike Parker

ANIMATED BY
Mike Parker
Chase Suddarth
Alex Bernstein

VOICES
Stacey Silva
Mike Parker
Chase Suddarth
Alex Bernstein
Sal Crivelli
Danielle Fletcher

SPRITES
Spriters-Resource.com
Zephiel87 
Tonberry 2K  
Sonic Team  
Sega  
Mister Mike 
Dolphman

EXECUTIVE PRODUCERS
Nord Tyrol
Christian Miller  
Ashton Withers   
Mark Glatt   
The Real Kit Nathaniels   
Jeff Meyer  
Henry Cipolla   
Antoine Edoh     
Fatimah    
Matthew Duchock  
Russell Downing   
Fenway Crowley   
Michael Seán Kelley
Ashley Neubauer
LJ Medina
Archer
James Geary
Cavdog26
Crispy Toast
James Dobbs
Business email dorkly@socialsynergize.co
Geek out with us...
INSTAGRAM: http://instagram.com/dorkly
FACEBOOK: http://www.facebook.com/dorkly
TWITTER: http://www.twitter.com/dorkly

Business email dorkly@socialsynergize.co

#RealisticVideoGames
#NinjaTurtles
OFFICIAL_DISCLOSURE: true

PAGE (Official Pixio Store - Best Performance Gaming Monitors):
Add image 3
Column 3
Add your content here
Add image 4
Column 4
Add your content here
Add image 5
Column 5
Add your content here
Add image 6
Column 6
Add your content here
Add image 7
Column 7
Add your content here
Add image 8
Column 8
Add your content here
Built for competitive eSports
30-Day Returns
Try it risk-free.
Free Shipping.
Always included.
U.S. Based Support
Real help when you need it.
3-Year Limited Warranty
Reliable coverage, built in.
```
</details>


### UCXOKEdfOFxsHO_-Su3K8SHg_yuYSt4i9_Z8_8c963bc9

- gold: {"st1": "physical_goods", "st2": ["food"], "st3": ["hfss_food_marketing"], "st3_evidence": [{"flag": "hfss_food_marketing", "quote": "Japanese subscription snack boxes"}, {"flag": "hfss_food_marketing", "quote": "Peach KitKat"}, {"flag": "hfss_food_marketing", "quote": "a strawberry King cider made with the king of strawberries is like a ultra high quality strawberry soda"}]}
- pred: {"st1": "physical_goods", "st2": ["food"], "st3": ["inadequate_disclosure", "direct_exhortation", "misleading_claim"]}
- errors: {"st3": {"missing": ["hfss_food_marketing"], "extra": ["direct_exhortation", "inadequate_disclosure", "misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
hey guys Mike Chen before getting into this video a little Japanese snacks review first with a sponsor of this video Tokyo tree and Sakura call let's do Sakura call First this month's theme is a rival of Sakura shiso sembe basically Sakura color rice crackers try this oh it tastes like pickled plums that's good wow this is so pretty look at this a little Sakura flower inside this jelly so every single bite it's like you're walking through a Sakura pedal storm this is one of my favorite snacks for one of these boxes ever and if you don't know sakurako and Tokyo treat are Japanese subscription snack boxes all these snacks are curated in Japan and shipped to you anywhere in the world and when you get a Sakura box you're getting 20 authentic traditional artisanal Japanese snacks a lot of these snack makers has been operating for over a hundred years also in the boss you can get traditional teas and a tableware item and this month's is a beautiful Sakura plate moving on to Tokyo treat Sakura picnic party Peach KitKat I've had this before peach KitKat this is my favorite KitKat if you see this anywhere you must try a peach kick out a strawberry King cider made with the king of strawberries is like a ultra high quality strawberry soda and when you get a Tokyo tree box you're getting 20 of the latest most exclusive limited edition and seasonal flavored Japanese snacks that are only available in Japan so two different snack boxes both equally delicious and if you want this one's snack box April snack box you have until the 15th of April to place your water and I love the mission of this company which is to share the amazingness of Japanese culture through the medium of snacking that's just such a great way to do it so if you want to give this track out of my link down below use my promo code dumpling to get five dollars off your first sakuroco box or five dollars off your first Tokyo treat box also use my special promo called Hanami and you will be able to get extra items in your Sakura coat box every single month for life and usually when I open my two boxes this is pretty much my food for the day so I'm gonna go eat and enjoy the video

VIDEO: 24 Hours Eating ONLY Japanese Department Store Food & Pokémon Café
DESCRIPTION:
🌸 Get your Sakuraco https://team.sakura.co/strictlydumpling-SC2303 and TokyoTreat https://team.tokyotreat.com/strictlydumpling-TT2303 boxes now and celebrate Japan's Sakura season! Use code "DUMPLING" for $5 off either box, or use Special Code "HANAMI" and get EXTRA bonus items in your Sakuraco box every month for life!
Experience Japan for yourself! 🌸

Spent the day eating at giant department stores in Tokyo Japan and came across a Pokémon café as well. I highly recommend eating at Japanese department stores to try out some of the best produce in the world.

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

PAGE (Choose Your Plan | Sakuraco):
Total Price
$0.00
Experience a new, authentic part of Japan every month through carefully curated snacks, teas, and home goods made with love
24-Page Culture Guide that accompanies you on an in-depth journey to explore monthly makers, themed articles, and snack info
Each box includes authentic home goods, including ceramics, chopsticks & furoshiki sourced from traditional Japanese makers
Hand-packed and shipped directly from Japan
Auto-renew with the option to pause or cancel anytime.
Discover Okinawa’s sunlit islands, savor authentic local flavors, and experience cultural moments that capture the spirit of the region.
Discover Okinawa’s sunlit islands, savor authentic local flavors, and experience cultural moments that capture the spirit of the region.
Sakuraco brings the authentic taste of Japanese snacks, candies, and teas right to your doorstep. Our products are sourced directly from family makers with centuries-old traditions, ensuring a traditional, uniquely Japanese experience.
From flavor pairings and prefectures, to festivals and holidays, we carefully curate the most authentic Japanese snacks, candy, and teas to get a true feel of Japan.
```
</details>


### UC-yfMLscSY3vP_PKC1Z5B0w_vyVxKh_VU0c_6cffe7f8

- gold: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "One of the safest things you can download out there."}, {"flag": "misleading_claim", "quote": "Regardless of the machine, Salad makes you money."}, {"flag": "misleading_claim", "quote": "use code Isaac why to make double the money."}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps", "financial"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["other"], "extra": ["apps", "financial"]}, "st3": {"missing": [], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
Moonji has huge traps. Holy crap. I literally have never worked out my traps ever. Before we continue, I'd like to give a big kiss on the face to the sponsor of today's video, Salad. Salad and I, we go we go way back. We went to high school together. Hell, I was his best man at his wedding. Jokes, of course, but I have previously mentioned Salad numerous times on this channel quite some time ago. If you're not familiar with Salad, let me give you the most basic rundown. Salad is a program that you can download on your PC that utilizes time spent away from your computer. Whether it be sleeping, work, or school, you can leave Salad to take care of racking in some sweet bucks while you're gone. Salad, in short, is a cryptocurrency miner. I know, when I say that, it sounds scary, malicious, terrible, horrible idea. But I myself am an avid user of Salad and if my word is not enough, check out their online ratings. They're through the roof positive. One of the safest things you can download out there. Now, Salad works on all sorts of PCs, whether it be your NASA computer with four GPUs or your grandma's old Intel 500. Regardless of the machine, Salad makes you money. All you have to do to start earning is press this little start button and go for a walk or something. I don't know. While you're away, Salad earns you the dollar bills that you can use to purchase anything from Discord Nitro to literal Turtle Beaches, Robux, Minecraft capes, Minecraft itself, charities, even straight-up visas. Salad has it all. If you'd like to download Salad, head to the link in the description and use code Isaac why to make double the money. That's like two times more money. Thank you, Salad, for sponsoring this video. Now, let's continue. All right, the VC is locked. I already got [screaming] it.

VIDEO: Last to leave VC wins $10,000
DESCRIPTION:
This night was truly a disaster.

Check out salad: 
https://bit.ly/Isaac-Salad
https://linktr.ee/saladchefs

🧉 Use code 'GROUP' for 10% off 🧉
https://bit.ly/GAMERSUPPS

LIMITED MERCHANDISE!!:
https://www.isaacwhy.com

intro song: https://bit.ly/3qtrOPM
intro artist: https://bit.ly/3FraLnA
elimination song: https://bit.ly/3nL2H89

JOIN THE OFFICIAL DISCORD (275,000+ MEMBERS):
https://discord.gg/bufa6aH

----------------------------------------------------------------------
SUPPORT MY FRIENDS IN THE VIDEO

@Softwilly
Larry: https://bit.ly/3z7esvw
Grunk: https://bit.ly/3jJRQvP
Tanner: https://bit.ly/3rhCPU5
Bear: https://bit.ly/3JcZd9R
Jubby: https://bit.ly/32wE7SM
@MoonzyCat 
@Yumi 

----------------------------------------------------------------------

my beautiful subtitler: https://bit.ly/3EnUtus

Socials:
TWITCH: isaac_why
INSTAGRAM: isaacwhy
TWITTER: isaac_why


In this video, I gave $10,000 away to the winner of my competition. The last to leave VC wins the challenge. I felt alot like Mr Beast, and how he gives away Millions of dollars to those in need. Hosting this competition was super fun! We spent a total of 26 hours in a voice chat. People were eliminated, while doing risky dares such as cracking an egg on their head and tweeting our odd things. Who do you think the Last to Leave VC will be?
#Discord
OFFICIAL_DISCLOSURE: false

PAGE (Salad - Distributed GPU Cloud | 60,000+ daily active GPUs from $0.02/hour):
Text-to-Image
Get superfast image generation with pre-built containers on RTX 5090. Save on costs while keeping top-tier output.
Deploy AI/ML production models at scale securely on the world's largest distributed cloud network. Save up to 90% on compute costs compared to data center GPUs & hyperscalers.
Save even more for high-volume GPU use.
“By switching to SaladCloud, we are serving inference on over 600 consumer GPUs to deliver 10 Million images per day and training more than 15,000 LoRAs per month. SaladCloud not only had the lowest GPU prices in the market but also offered us incredible scalability.”
Justin Maier
Founder & CEO, Civitai
"On SaladCloud's consumer GPUs, we are running 3X more scale at half the cost of A100s on our local provider and almost 85% less cost than the two major hyperscalers we were using before.I’m not losing sleep over scaling issues anymore."
Jamsheed Kamardeen
CTO, Blend
"If you want access to 1000s of GPUs, you can get them on SaladCloud for better cost-efficiency. Salad is also really customer friendly, something you cannot get from a larger cloud provider as a startup."
Zachary Lawrence
CEO, Klyne.ai
Read case study >Benchmarks, tutorials, product updates and more.
Big Tech controls the compute, sets the prices and rations supply. Not anymore.
SaladCloud unlocks the world's largest AI compute hidden in plain sight, offering low-cost AI-enabled GPUs to businesses while rewarding individual GPU owners.
All GPUs on SaladCloud belong to the RTX/GTX class of GPUs from Nvidia. Our GPU selection policy is strict and we only onboard AI-enabled, high performance compute capable GPUs to the network.
We have several layers of security to keep your containers safe, encrypting them in transit, and at rest. Containers run in an isolated environment on our nodes - keeping your data isolated and also ensuring you have the same compute environment regardless of the machine you’re running on.
Since SaladCloud is a compute-share network, our GPUs have longer cold start times than usual, and are subject to interruption. The highest vRAM on the network is 24 GB. Workloads requiring extremely low latency times are not a fit for our network.
Workloads are deployed to SaladCloud via docker containers. SCE is a massively scalable orchestration engine, purpose-built to simplify this container development.Containerize your model and inference server, choose the hardware and we take care of the rest.
GPUs on SaladCloud are similar to spot instances. Some providers share GPUs for 20-22 hours a day. Others share GPUs for 1-2 hours per day. Users running workloads select the GPU types and quantity. SaladCloud handles all the orchestration in the backend and ensures you will have uninterrupted GPU time as per requirements.
Owners earn rewards (in the form of Salad balance) for sharing their compute. Many compute providers earn
$30−$200 per month on SaladCloud as a reward that they exchange for games, gift cards and more.
Our constant host intrusion detection tests look for operations like folder access, opening a shell, etc. If a host machine tries to access the linux environment, we automatically implode the environment and blacklist the machine. We’re also bringing Falco into our runtime for a more robust set of checks.
We use a proprietary trust rating system to index node performance, forecast availability, and select the optimal hardware configuration for deployment. We also run proprietary tests on every GPU to determine their fit for our network. Salad Container Engine automatically reallocates your workload to another GPU (same type and class) when a resource goes offline.
Scale quickly to thousands of GPU instances worldwide without the need to manage VMs or individual instances, all with a simple usage-based price structure.
Save up to 90% on orchestration services from big box providers, plus discounts on recurring plans.
Distribute data batch jobs, HPC workloads, and rendering queues to thousands of 3D accelerated GPUS.
Bring workloads to the brink on low-latency edge nodes located in nearly every corner of the planet.
Deploy Salad Container Engine workloads alongside your existing hybrid or multi-cloud configurations.
Scale your workloads effortlessly with dynamic resource allocation, meeting fluctuating demands in real time without over-provisioning.
Experience flexible pricing tailored to your usage, ensuring cost-effective scaling without compromising performance.
AI-enabled consumer GPUs offer better cost-performance than datacenter GPUs for many use cases.
Get superfast image generation with pre-built containers on RTX 5090. Save on costs while keeping top-tier output.
You are overpaying for managed services and APIs. Serve TTS inference on SaladCloud's consumer GPUs and get 10X-2000X more inferences per dollar.
If you serve AI transcription, translation, captioning & insights at scale, you are overpaying by thousands of dollars today. Save up to 90% with the Salad Transcription API, the lowest priced API in the market today.
Simplify and automate the deployment of computer vision models like YOLOv8 on 10,000+ consumer GPUs on the edge. Save 50% or more on your cloud cost compared to managed services/APIs.
Running Large Language Models (LLM) on SaladCloud is a convenient, cost-effective solution to deploy various applications without managing infrastructure or sharing compute.
We can’t print our way out of the chip shortage. Run your workloads on the edge with already available resources. Democratization of cloud computing is the key to a sustainable future, after all.
The high total cost of ownership (TCO) on popular clouds is a well-known secret. With SaladCloud, you containerize your application, choose your resources, and we manage the rest, lowering your TCO and getting to market quickly.
Over 1 million individual nodes and 100s of customers trust SaladCloud with their resources and applications.
Over 1 million individual nodes and 100s of customers trust SaladCloud with their resources and applications.
You don’t have to manage any Virtual Machines (VMs).
No ingress/egress costs on SaladCloud. No surprises.
Save time & resources with minimal DevOps work.
Scale without worrying about access to GPUs.
```
</details>


### UC9lNNtAARC-n0WC7tm-884Q_lrFTX-0vrDU_8296c5d0

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics", "health"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "physical_goods", "st2": ["health"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": ["hardware_electronics"], "extra": []}, "st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
but who am I kidding? People are going to anyway. But before we get too far into things, I want
to give a big thank you to our sponsor for today’s video, Manscaped, and yeah, I can
probably go into detail about The Lawn Mower 2.0 or The Plow or their other amazing products. However, I really want to say that the Crop
Preserver ball deodorant is amazing because at the time of this recording, it is summer
in Texas and this has saved my nether regions on more than one occasion. I think that it maybe might not be much of
a coincidence that last time I promoted these guys, I had a girlfriend and now I have a
fiancée. So if you want to get in on this for yourself
go ahead and go to Manscaped.com and make sure you use the code COMICD20 at checkout
for 20% off. The Perfect Package 2.0 includes everything
that you saw here and it is definitely worth the investment. I am a big fan of these products and you’re
going to be hearing about them a lot more in the future on this channel, but anyway. Back to the video. Peter’s first girlfriend was Betty Brant,
a secretary at the Daily Bugle.

VIDEO: ALL of Spider-Man's Girlfriends!
DESCRIPTION:
Thanks to Manscaped for sponsoring today’s video! Get 20% OFF + Free Shipping with my link https://manscaped.com/comicd
   • Subscribe for more: http://bit.ly/1vfuUS2
   • Support us on Patreon: https://Patreon.com/TrailerDrake

Arizona Rose as Mary Jane - https://www.instagram.com/arizona.rose/
Ant Dude as Peter Parker - https://www.youtube.com/user/AntDude92
That C Monster as Gwenpool - https://www.twitch.tv/thatcmonster

0:00 Intro
1:20 Sponsor
2:13 Betty Brant
3:14 Gwen Stacy
5:29 Mary Jane Watson
6:03 Cissy and Debbie
8:31 Felicia Hardy
9:15 MJ... again.
9:36 Jill Stacy
10:55 Carlie and Sara
13:08 Anna-Maria Marconi
13:57 Cindy Moon
14:36 Lian, Bobbi, and Rebecca

Special thanks to our Patrons for helping make this possible!
Basel, Bonnie Davies, Yosh Flores, Lord of Realms, Senita Mahoney, Jonathan & Megan Pierson, David Adler, Dylan Blass-Svedvik, Ralph Braganzan, Ethan Dannen, Oliver Kingston, Sam Kirkham,, LookWhosFhtagn, Ben Payne, Cole Roberts, The Side Quest Gamer, Andrew Shaffer, Vydal

#SpiderMan #Marvel #Comics
OFFICIAL_DISCLOSURE: true

PAGE (MANSCAPED® | The Leader in Men’s Grooming Tools & Essentials | MANSCAPED US):
Money-Back Guarantee
Free Shipping Over $49
2-Year Warranty
Not just balls
Make your face look as good as your groin.
Made for you
Game-changing tech.
The Lawn Mower® 5.0 UltraGroin & Body Hair Trimmer
Waterproof Design
Take it in the shower. Trim wet or dry.
**IPX7 rated to protect against immersion in up to one meter of fresh water for up to 30 minutes.
The Chairman® ProElectric Foil Face Shaver
SkinSafe® Blade Technology
Designed to give you a skin-close shave while reducing the risks of nicks and snags. So you can shave with confidence.
*SkinSafe® technology does not guarantee cut protection.
Weed Whacker® 3.0 ProElectric Nose, Ear & Eyebrow Hair Trimmer
Powerful, Industry-Leading Motors
Constant RPMs prevent the blade from slowing down, so your devices are strong until the last stroke.
Our Recos
Top-tier essentials.
Shop. Earn. Shave.
Want the total package for your package and more? You're hereby invited to the brotherhood of body care.
Earn $10 Rewards Cash for every 1,000 points.
Guest List
Earn 5 points per $1 spent
A-List
Earn 8 points per $1 spent
VIP
Earn 10 points per $1 spent
```
</details>


### UC6Mjg5R5QOJYjrio1JmP8Fg_pyZ5ID7RIE0_d6d949f3

- gold: {"st1": "physical_services", "st2": ["health"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "physical_services", "st2": ["health"], "st3": ["misleading_claim", "direct_exhortation"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["direct_exhortation", "misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
burglary at Microsoft headquarters to steal an Xbox prototype this is the Xbox underground thank you to Zach do for sponsoring this video being a big kid has its works you can eat ice cream for dinner and you want to Bim watch your P show you can't nobody can stop you guys if you want to watch a TV show all day but what happens if a meal-sized portion of ice cream gives you boo boo belly and 20 straight hours in front of a screen rots your eyes you'll need a doctor that's where Zach do comes in Zach do is a free app and website that makes finding the right doctor easy you can search and compare highquality in network doctors for any medical need mental skincare you name it Dental that's what I use it for you can instantly book an appointment most appointments happen within 24 to 72 hours sometimes it is the same day instantly with over 100,000 Healthcare Providers across every specialty you have plenty of options with Zach do plus you can filter doctors by which insurance you have who's located nearby and who has the best rating by verified patients not only that you can see their available appointment times before you book if and when I need doctors I'm going to use Zach do and and you should too go to zocdoc.com oompaville and book a top rated doctor today that's zoc do.com or click the link in the description and thank you to Zach do for supporting this video hackers have been

VIDEO: The Kids Who Outplayed The FBI...
DESCRIPTION:
Go to https://zocdoc.com/OOMPAVILLE find and instantly book a top-rated doctor today

https://www.youtube.com/watch?v=yStl8VdK3fc

BUY CANDY 👉 http://link.sour.gg/sourboys
Wishlist My Game 👉https://store.steampowered.com/app/3266110/Black_Pine_Incident_Response/
EXCLUSIVE CONTENT 👉 https://link.sour.gg/psyop
Official Oompaville Merch (funny shirts) 👉  http://oompa.shop
Podcast 👉 @oomppod
DAILY POSTING CHANNEL  👉  @oompayt
MY LINKS 👉 https://wlo.link/@oompa
Business Inquiries 👉 brands@sour.gg

Special thanks to the team: 
Tara 
Squeaky:    / @thatsqueaky  
Coop: https://linktr.ee/tcoop1800
Rosie: https://linktr.ee/badhiveillustration
OFFICIAL_DISCLOSURE: true

PAGE (SourBoys):
Let customers speak for us
FAQ
-
Depends on what you buy! Every flavor we use a different blend of sour/sugar to keep certain flavors elevated and more.
Currently we have 5 levels.- Level 1 - Barely sour. Mostly sweet!
- Level 2 - Pretty standard sour, like a Sour Patch Kid.
- Level 3 - Getting pretty sour! about 30% more sour than a Sour Patch Kid.
- Level 4 - A little bit more sour than a Sour Skittle
- Level 5 - Very sour. Enjoyable only to the most extreme lovers of sour candy!
Some flavors don't pair well with EXTREME SOUR! In the future, we will offer a clean indicator for sour levels!
-
We use VERY high-quality (and expensive) dyes from fruits and veggies. Things like turmeric for yellow, blueberries for blue, spirulina for green and beets for red! Some with blends of all those!
-
Yes! SourBoys belts contain gluten. One of our main ingredients is locally sourced wheat flour. It's very high-quality stuff! Lil Guys sour gummies DO NOT CONTAIN GLUTEN.
-
Yes! One of the sources of our glucose syrup is from corn starch.
-
YES. Cane sugar mostly! We really respect candy companies charging forth with low-sugar options, but for us, we don't find them fulfilling our cravings for candy. Sometimes they suck! We set out to create the most delicious and bold candy possible, and to achieve that in unison with using significantly less sugar than our competitors and exclusively using natural dyes and flavors, and so on.
-
For sure, but not recommended. Take a break. Eat some protein! This is just candy. It's meant to be enjoyed with friends and family. You should also brush your teeth!
-
Visa, Denarius, MasterCard, Doubloons, American Express, Peppercorns, Discover, Amazon Pay, Drachma, Google Pay, Cash App, PayPal, and more!
-
Just depends on where you live! Add something to the cart and take a peek. As we have grown, we have passed our savings (from scaling) onto the consumers!
Most orders are processed within 1-3 business days. Shipping times vary depending on which option you choose!
-
YURP. Available worldwide except North Korea, Russia, Belarus, Ukraine, and Haiti. Customers are responsible for customs duties and taxes. Please check local import requirements before ordering.
-
NOPE. SourBoys and LilGuys are the best plant-based candies on earth!
```
</details>


### UC_0CVCfC_3iuHqmyClu59Uw_7JPgXvd8Ck8_ff58b00e

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
help of Micro Center they were kind enough to send this over for review so this video is sponsored by Micro Center if you're not familiar with Micro Center and you're a tech Enthusiast then you really should be this is an awesome store that you can actually head in and put your hands on the product before you buy them whether you need a monitor some Ram a CPU a GPU Raspberry Pi printer basically anything Tech related you can pick up in Micro Center stores they've got 25 stores nationwide with a new one opening in Indianapolis by the end of the summer and two more by the end of 2025 and by the way if you sign up for microcenter's email list and visit the Indianapolis store when it's open you can get a 128 gigabyte flash drive for free and right now in all of their stores they have a promotion going on known as monitor Madness so you can head over to Micro Center and check out the monitors on display to see which one you like the best they've got really awesome discounts on a ton of them like for instance if you wanted to go with something a bit cheaper coming in at 80 you could go with this Acer 23.8 inch it's full HD so 1080p LED display at 75 Hertz or if you wanted to go all out with it you could go with something like this LG 26.8 inch 4K UHD display also supports Nvidia g-sync so basically whatever your Technique needs are Micro Center's got you covered okay so jumping right into the specs

VIDEO: GE78 HX First Look! The Most Powerful & Expensive Laptop We've Ever Tested!
DESCRIPTION:
In this video we take a look at the most powerful laptop we’ve ever tested And the most expensive! Powered by the all new Intel i9 13950HX CPU and backed by an Nvidia RTX 4080 Laptop GPU this this can run anything to throw at it! Known as the MSI Raider GE78HX. This video is sponsored by Micro center

New Customer Exclusive - Free 256 GB SSD: https://micro.center/27m
Shop MSI Raider GE78HX 17" Gaming Laptop - Dark Grey: https://micro.center/r4x
Receive a FREE 128gig flash drive at Micro Center’s Indianapolis Grand Opening: https://micro.center/qqz
Submit your build to Micro Center's Build Showcase: https://micro.center/b35

Follow Me On Twitter: https://twitter.com/theetaprime
Follow Me On Instagram: https://www.instagram.com/etaprime/

25% Code for software: ETA
Windows 10 Pro OEM Key($15): https://biitt.ly/KpEmf
Windows10 Home Key($14): https://biitt.ly/2tPi1
Windows 11 Pro Key($22): https://biitt.ly/RUZiX
Office 2019 pro key($49): https://biitt.ly/o0OQT

Equipment I Use:
Monitor: Pixio 277 Pro On Amazon: https://amzn.to/3PGUBwe
Elgato HD60 X Screen Capture Device: https://amzn.to/3GkP2AL
Tool Kit: https://amzn.to/3Wo8bpX
Camera: https://amzn.to/3XJfFoI

DISCLAIMER: This video and description contains affiliate links, which means that if you click on one of the product links, I’ll receive a small commission at no extra cost to you!
Under section 107 of the Copyright Act 1976, allowance is made for “fair use” for purposes such as criticism, comment, news reporting, teaching, scholarship, education, and research.
No Games Are Included Or Added

This video and Channel and Video are for viewers 14 years older and up. This video is not made for viewers under the age of 14. 

00:00 Introduction
00:28 Overview
00:58 IO Overview
01:55 Video Sponsor Ad Spot
03:09 Raider GE78HX 13VH Specs
04:30 Per Key Backlit RGB Steek Series Keyboard
05:06 Cyberpunk 2077
05:43 Benchmarks
06:38 Spiderman Remastered
07:04 Elden Ring
07:28 Dirt 5
07:53 Mortal Kombat 11
08:13 Horizon Zero Dawn
08:37 Cod Modern Warfare 2
09:01 God Of War 4K Ultra
09:29 Final Thoughts

Want to send me something?
ETAPRIME 
12520 Capital Blvd Ste 401 Number 108
Wake Forest, NC 27587 US

THIS VIDEO IS FOR EDUCATIONAL PURPOSES ONLY!

#gaming #nvidia #intel #etaprime
OFFICIAL_DISCLOSURE: true

PAGE (Sign In):
Sign In
Shopped with us before?
Use the information you provided in store.
By continuing, you agree to our account Terms and Conditions, Privacy Policy, and Cookie tracking, including our best email deals and max 5 text msgs/mo (incl. cart reminder, informational alerts) from 64276. Unless previously opted out. Msg & data rates may apply. Text STOP to end. Opt out at any time.
```
</details>


### UCzOfLNkiScJp3U_h_QlvHHg_61PHU5OdJAA_949fed47

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics", "health"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "giving you that ultra smooth bare skin finish."}]}
- pred: {"st1": "physical_goods", "st2": ["health"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": ["hardware_electronics"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
which meant once again I was now alone, lost, diving into a wild jungle, which is uh something my girlfriend could relate to before I started using Manscaped, today's sponsor. I'm so sorry. But today we got something brand new, the Manscape Lawn Mower 5.0 White Hot Ultra. And this thing is beautiful. Now, if you've been looking a little bit like Sassy the Sasquatch down there, this trimmer might just be the thing for you. Equipped with two interchangeable nextG skin safe blade heads, a long hair trimmer blade and a foil blade, giving you that ultra smooth bare skin finish. And swapping between the two couldn't be simpler. Cordless, waterproof, and also equipped with the dual temperature LED lights. No matter the conditions, you won't be missing any more spots. And with a travel lock, easy recharging, and a comprehensive three-level battery life indicator, the 5.0 Ultra is your perfect companion. So, don't miss out and head over to Manscape today and use code Wilgum 15 at checkout for 15% off. And you'll even get 2 years free warranty. And thank you to Manscaped for sponsoring the video. Okay, now Frost

VIDEO: Official Rust Survival, but I'm Stranded in the jungle...
DESCRIPTION:
#rust #solorust #chilledvibes 
When Two Solo Roleplayers take on the vanilla Rust Jungle...

Thanks to MANSCAPED for sponsoring today's video! Get 15% OFF on the special edition of The Lawn Mower® 5.0 Ultra in “White Hot” with code "WILLJUM15" at https://manscaped.com/willjum

WILLJUM'S SERVERS  - FOR INFO - DISCORD.GG/WILLJUM

[EU] Willjum's Casual Solo/Duo Monthly 
connect 156.236.84.230:28014
[EU] Willjum's solo only server 
Connect willjum.eu
[NA] Willjum's solo only server
Connect willjum.US

MY SECOND CHANNEL : https://www.youtube.com/channel/UCgYBxwW1sqqKMb4KjfvDZgQ/videos


Massive thank you to my current Patrons, Thanks to your help i was able to afford my new PC! so thank you! if you want to support me further: 

https://www.patreon.com/Willjum
MY TWITCH :
https://www.twitch.tv/willjum






Give me a follow on twitter! https://twitter.com/willjum1

Business email (for non business stuff just message me on discord) willjum@afkcreators.com

Much love to the wonderful  @Sinhunsan1 on Twitter for the Thumbnail!!

Fantastic Music From 

Epidemic Sounds
Musicbed
OFFICIAL_DISCLOSURE: true

PAGE (MANSCAPED® | The Leader in Men’s Grooming Tools & Essentials | MANSCAPED US):
Money-Back Guarantee
Free Shipping Over $49
2-Year Warranty
Not just balls
Make your face look as good as your groin.
Made for you
Game-changing tech.
The Lawn Mower® 5.0 UltraGroin & Body Hair Trimmer
Waterproof Design
Take it in the shower. Trim wet or dry.
**IPX7 rated to protect against immersion in up to one meter of fresh water for up to 30 minutes.
The Chairman® ProElectric Foil Face Shaver
SkinSafe® Blade Technology
Designed to give you a skin-close shave while reducing the risks of nicks and snags. So you can shave with confidence.
*SkinSafe® technology does not guarantee cut protection.
Weed Whacker® 3.0 ProElectric Nose, Ear & Eyebrow Hair Trimmer
Powerful, Industry-Leading Motors
Constant RPMs prevent the blade from slowing down, so your devices are strong until the last stroke.
Our Recos
Top-tier essentials.
Shop. Earn. Shave.
Want the total package for your package and more? You're hereby invited to the brotherhood of body care.
Earn $10 Rewards Cash for every 1,000 points.
Guest List
Earn 5 points per $1 spent
A-List
Earn 8 points per $1 spent
VIP
Earn 10 points per $1 spent
```
</details>

