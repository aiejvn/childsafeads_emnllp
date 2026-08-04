# Error summary (7 instance(s) with at least one error)

## Per-tier error counts

- st1: 0/7
- st2: 3/7
- st3: 7/7

## st2 missing labels (gold had it, prediction missed it)

- other: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- gambling_adjacent: extra 1x
- other: extra 1x
- apps: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- other -> apps: 1x

## st3 missing labels (gold had it, prediction missed it)

- inadequate_disclosure: missing 3x
- insufficient_context: missing 1x
- age_restricted_or_prohibited_product: missing 1x
- no_flag: missing 1x
- misleading_claim: missing 1x

## st3 extra labels (prediction hallucinated, not in gold)

- misleading_claim: extra 3x
- undisclosed_advertising: extra 1x
- inadequate_disclosure: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- insufficient_context -> undisclosed_advertising: 1x
- age_restricted_or_prohibited_product -> misleading_claim: 1x
- no_flag -> misleading_claim: 1x
- inadequate_disclosure -> misleading_claim: 1x
- misleading_claim -> inadequate_disclosure: 1x

## Detailed error instances

### UCshoKvlZGZ20rVgazZp5vnQ_MzDh8Gndkw4_79a5a43b

- gold: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": ["other"], "extra": ["apps"]}, "st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
alright ladies and gentlemen welcome back to another episode of RL crafts as always brought to you by our sponsors MC pro hosting providing the server on which we are playing they can also provide you with a server if you wish to do so check out the link in the description of the video you'll be able to snag a server with a discount off your first month like going through that link you can do a one-click install of RL crafts if that's something you're interested in play with your friends or do vanilla stuff or do it's very dark out and apparently there could be a

VIDEO: If Only Minecraft Had Giant Ants (RLCraft Modpack #12)
DESCRIPTION:
1.15 update should give us every kind of giant insect.
Thanks to MCProHosting for sponsoring the video! Use code "CaptainSparklez" to get 25% off your own server's first month: https://mcph.info/CaptainSparklez
Previous Episode ► https://www.youtube.com/watch?v=B03MHiCHCFU&list=PLSUHnOQiYNg0h4QNFGAxEnktRwgpwq1Tr&index=11&t=0s
RLCraft playlist ► https://www.youtube.com/playlist?list=PLSUHnOQiYNg0h4QNFGAxEnktRwgpwq1Tr

Modpack Link: https://www.curseforge.com/minecraft/modpacks/rlcraft/files/2780296
X33N: https://www.youtube.com/user/X33N

My Links

● Twitter: http://twitter.com/CaptainSparklez
● Instagram: http://instagram.com/jordanmaron
● Live stream: https://www.twitch.tv/captainsparklez
● Amazon: https://www.amazon.com/shop/captainsparklez

Outro Song:
Jalmaan & Voldex - Far Away (feat. Sebastian Hansson)
Video link: https://www.youtube.com/watch?v=OsK5XeoreW4
Link: https://link.divr.moe/FarAway

Thanks for watching, dudes! Ratings, favorites, and general feedback is always appreciated :)
OFFICIAL_DISCLOSURE: false

PAGE (CaptainSparklez's Amazon Page):
Sorry, we’re having trouble displaying some posts. Try refreshing the page.
Sorry, we couldn’t find what you’re looking for.
Sorry, we’re having trouble displaying some posts. Try refreshing the page.
No posts yet
When CaptainSparklez posts, you’ll see their posts here.
Sorry, we’re having trouble displaying some posts. Try refreshing the page.
Sorry, we’re having trouble displaying some posts. Try refreshing the page.
No posts yet
When CaptainSparklez posts, you’ll see their posts here.
Sorry, we’re having trouble displaying some posts. Try refreshing the page.
No posts yet
When CaptainSparklez posts, you’ll see their posts here.
Sorry, we’re having trouble displaying some posts. Try refreshing the page.
```
</details>


### UC9fPdns4wpC6hJ4qLkrORMA_kZCfjWrNmEA_a60d11fd

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["age_restricted_or_prohibited_product"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps", "gambling_adjacent"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": [], "extra": ["gambling_adjacent"]}, "st3": {"missing": ["age_restricted_or_prohibited_product"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
so before we begin I wanted to give a huge shout out to Ubisoft for sponsoring this video and I was going to start with opening one alpha pack I kind of messed it up and opened it before I started recording and look what I got that's content creator luck right there so year eight season one is finally here in Rainbow Six Siege it is coming out March 7th which should already be out by the time this video goes live and with it comes one of the most influential operators we've ever seen which is Brava now Brava can hack any Defender Gadget or any electronic Defender Gadget with the clutch drum and it's pretty straightforward you look at a defending Gadget and you just hack it and another significant change this season is the new reloading system you can no longer reload cancel and Siege when you go to reload you only have one bullet in the chamber during that process so if somebody pushes you you're basically dead now the biggest change this season and not just this season but in the history of Siege is mousetrap so if you don't know they're now going to detect mnk users on console and add input lag to their devices making it almost impossible to play this is a huge change for all the controller players I just want to compete fairly in their ranked games another change they're adding this season is the voice chat restriction so if somebody's saying a bunch of crazy stuff in game chat there's now a system in place to report them to get that type of behavior out of the game it's also that time of year where rainbow is offering their year pass you can get it for 10 off up until March 20th so don't miss out on that offer if you want to learn more you can click the link in the description below thanks again to Ubisoft for sponsoring and enjoy the rest of the video

VIDEO: New Season New Me in Rainbow Six Siege (Operation Commanding Force)
DESCRIPTION:
Check out all the new changes here https://ubi.li/FOAXd
Thanks to Ubisoft for sponsoring this video!











#rainbowsixsiege 
#ad
OFFICIAL_DISCLOSURE: true

PAGE (Operation Commanding Force | Seasons | Tom Clancy's Rainbow Six Siege | Ubisoft (EU / UK)):
Bolster through the first season of Rainbow Six Siege Year 8 with Operation Commanding Force! From the beautiful melting pot that is Brazil comes the sly and headstrong new Operator Brava. Equipped with her Kludge Drone, an electromagnetic gadget that can disrupt hostile surveillance, Brava joins the ranks of Viperstrike ready to push the limits of convention and good measure to carry out justice. Read the Patch Notes below for full details.
In Operation [REDACTED], Brava faced every specialist’s nightmare when she had to choose between saving a fellow operator or the mission objective, rescuing a group of hostages. She chose the latter. Soldiers who can make the right decision in the worst of circumstances belong in Viperstrike.
PARA-308
ASSAULT RIFLE
CAMRS
Marksman Rifle
USP40
HANDGUN
Super Shorty
SHOTGUN
Smoke Grenade
Claymore
“The Kludge Drone’s capacity to turn a hostile device wouldn’t be as effective without Brava’s ability to survey a situation…”
Brava's Kludge Drone is a sabotage tool capable of taking over opponents' devices. If the device can't be controlled, it's destroyed instead.
Coming in the middle of Operation Commanding Force, players who use mouse and keyboard on consoles will activate a penalty that adds lag to their inputs. The goal of this penalty is to encourage fair gameplay by removing the unfair advantage that mouse and keyboard players have on consoles.
While active, continued use of mouse and keyboard gradually increases the lag over several matches, making it harder to aim and shoot. Completing matches with a controller will gradually reduce the lag back to normal.
NEW REPUTATION PENALTY: ABUSIVE VOICE CHAT
This season introduces a new Reputation Penalty for abusive voice chat. While active, this penalty mutes repeat offenders by default to prevent hateful and disruptive content in voice chat. Muted players can still use voice chat but will only be heard by players who unmute them.
At launch:
RELOAD REWORK
Reloading has been reworked so that interrupting the animation will leave the player without a magazine, but closed bolt weapons will have a single round for the player to use at any point during the reload.
ZERO UPDATE
Zero's Argus camera has some new behaviors. Zero can command his cameras to pierce through surfaces while controlling the Observation Tool. Once the camera has pierced a surface, teammates and Zero can swap to surveil either side at will unless they're eliminated.
OPERATOR SPECIALTIES
Operator Specialties identify an Operator's playstyle in-game. All Operators have one to two specialties which can be checked during the Planning Phase, in the Operators section, and in Operator Guides.
SPECIALTY CHALLENGES
Specialty Challenges aim to help beginner players learn the various Operator specialties and what they contribute to a match.
By completing challenges, players can earn a variety of rewards, including an Operator after finishing all challenges for a single specialty. If the Operator is already owned, players will earn their value in renown instead. All players can be complete the challenges and earn all rewards, not just beginners.
PLAY SECTION UI CHANGES
Playlists are now divided into 3 separate categories: Competitive, Quick Play, and Training, alongside the already-existing Custom Game section.
BOOT THE TEST SERVER FROM LIVE GAME
For convenience, the live game now notifies players when the Test Server is live and has a shortcut that lets players quickly boot it.
BRAVO PACK TICKET
This season introduces the Bravo Pack Ticket, a rare item that lets you pick an exclusive reward from the latest Bravo Collection. This ticket will be awarded to Premium players who reach level 100 in this season’s Battle Pass as a reward for their dedication.
It’s a new Year and as per usual Operation Commanding Force brings its own batch of Operator price decrease. Dropping to 10,000 Renown or 240 R6 Credits are Operators Oryx and Iana. Flores’ price is decreasing to 15,000 Renown or 360 R6 Credits, and finally, Azami is now priced at 20,000 Renown or 480 R6 Credits.
Travel to the luscious and vibrant landscapes of Brazil with the seasonal skin collection included in the Lush Foliage Bundle. It comes with the Tropical Underbush weapon and attachment skins, the Flowery Relaxation charm, as well as the Thunderous Nature operator card background! The seasonal weapon skin will be released at season launch and available for purchase throughout the season. Once unlocked, it remains in your inventory indefinitely and can be applied to all available weapons.
BRAVA
TWITCH
Muzzle Brake
Compensator
To learn more about the mischievous bugs we've fixed for this season, follow the link below.
BUG FIXES LIST
```
</details>


### UCDogdKl7t7NHzQ95aEwkdMw_3xR1uRU1O8Q_70f5c1f4

- gold: {"st1": "physical_goods", "st2": ["creator_community", "fashion"], "st3": ["insufficient_context"], "st3_evidence": [{"flag": "insufficient_context", "quote": "[music] [music] Ladies and gentlemen, welcome to"}]}
- pred: {"st1": "physical_goods", "st2": ["fashion", "creator_community"], "st3": ["undisclosed_advertising"]}
- errors: {"st3": {"missing": ["insufficient_context"], "extra": ["undisclosed_advertising"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
[music] [music] Ladies and gentlemen, welcome to

VIDEO: SIDEMEN HIDE AND SEEK IN THE MOST EXPENSIVE HOUSE IN LONDON
DESCRIPTION:
👉🏻: Subscribe to our Reacts Channel: https://www.youtube.com/SidemenReacts 👈🏻
👕: Sidemen Clothing: http://www.sidemenclothing.com
👉🏻 Subscribe to our 2nd Channel: https://www.youtube.com/MoreSidemen 👈🏻
📸: Sidemen Instagram: http://www.instagram.com/Sidemen
🐤: Sidemen Twitter: http://www.twitter.com/Sidemen

✏️: SUBMIT A #SidemenSunday IDEA HERE
https://forms.gle/JDuGrSzM4F6mdo6D9

-----------------------------------------------------------------------------------------------------------------------

▶️ SIDEMEN ◀️

🔵 JOSH (Zerkaa)
● http://www.youtube.com/Zerkaa
● http://www.youtube.com/ZerkaaPlays
● http://www.instagram.com/Zerkaa
● http://www.twitter.com/ZerkaaHD

🔴 HARRY (W2S)
● http://www.youtube.com/W2S
● http://www.youtube.com/W2SPlays
● http://www.instagram.com/Wroetoshaw
● http://www.twitter.com/Wroetoshaw

🔵 VIK (Vikkstar123)
● http://www.youtube.com/Vikkstar123
● http://www.youtube.com/Vikkstar123HD
● http://www.youtube.com/VikkstarPlays
● http://www.instagram.com/Vikkstagram
● http://www.twitter.com/Vikkstar123

🔴 JJ (KSI)
● http://www.youtube.com/KSI
● http://www.youtube.com/KSIOlajidebtHD
● http://www.instagram.com/KSI
● http://www.twitter.com/KSIOlajidebt

🔵 TOBI (Tobjizzle)
● http://www.youtube.com/TBJZL
● http://www.youtube.com/Editingaming
● http://www.instagram.com/Tobjizzle
● http://www.twitter.com/Tobjizzle

🔴 ETHAN (Behzinga)
● http://www.youtube.com/Behzinga
● http://www.youtube.com/Beh2inga
● http://www.instagram.com/Behzingagram
● http://www.twitter.com/Behzinga

🔵 SIMON (Miniminter)
● http://www.youtube.com/Miniminter
● http://www.youtube.com/MM7Games
● http://www.instagram.com/Miniminter
● http://www.twitter.com/Miniminter
OFFICIAL_DISCLOSURE: false

PAGE (SDMN Clothing):
ARCHIVE SAVE 60%
ARCHIVE SOLD OUT
ARCHIVE SAVE 60%
FIRST LOOK
Sundaes Hoodie
Pink
ARCHIVESOLD OUT
ARCHIVESOLD OUT
ARCHIVE SOLD OUT
ARCHIVE SAVE 50%
ARCHIVE SAVE 60%
ARCHIVESOLD OUT
ARCHIVESOLD OUT
FIRST LOOK
2013 Long-Sleeve T-Shirt
Off White/Navy
FIRST LOOK
Sundaes Hoodie
Pink
FIRST LOOK
2013 Waffle Long-Sleeve
Black/Gray
FIRST LOOK
Studios ® Waffle Long-Sleeve
Light Blue/Gray Marl
FIRST LOOK
FIRST LOOK
Studios ® Lightweight Windbreaker
Textured Cacao
FIRST LOOK
Every Sunday T-Shirt
Off White
FIRST LOOK
```
</details>


### UCdkpbFQAQFLK_DeO10PpVNg_N_8t-fsKJcc_70db7008

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "\u2014 Shopping Links (Using Affiliate Links Supports Us!) \u2014"}, {"flag": "misleading_claim", "quote": "the best source for gaming chairs and desk for those long gaming sessions"}]}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics", "other"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": [], "extra": ["other"]}, "st3": {"missing": ["inadequate_disclosure"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
today's video is brought to you by ewin racing the best source for gaming chairs and desk for those long gaming sessions we have a playlist of our ewin chair and desk videos Linked In the video description below save 30% off of everything using the discount code Tech deals more details at the end of the video and then Blaze uh has come in are

VIDEO: Have SSDs Finally Made All Hard Drives Obsolete? — Byte Size Tech
DESCRIPTION:
Welcome to Byte Size Tech - This Channel is devoted to highlights from Tech Deals.  These are segments cut straight from the live streams, in easy to digest portions! So, if you're looking for Byte Sized Tech answers, you've come to the right place! 
— Expand the Video Description for more Details —

— Gaming Chairs & Desks / Wide Selection of Sizes & Colors —
Save 30% off Everything using Promo Code TECHDEALS
EWin Racing - http://pcdeal.tv/EWinRacing
EWin Video Playlist - http://pcdeal.tv/EWinRacing-Videos
Watch Rogue’s Video on how to buy a gaming chair https://youtu.be/4GiXy7EEI14

— Live Stream —
AMD Giving up on Radeon GPUs? — Intel Arc 2 — AM5 APUs — Gamescom 2023 — RTS 08-06-23
https://www.youtube.com/watch?v=CXvgCdoD_ko

Have SSDs Finally Made All Hard Drives Obsolete? — Byte Size Tech
RTS   08 06 2023   Are Hard Drives Still Worth It   Ewin

#bytesizetech #pcbuild  #upgrade 
————

— Our YouTube Channels —
https://youtube.com/techdeals
https://youtube.com/roguetechgaming
https://youtube.com/technewsnetwork
https://youtube.com/techfamilyreacts

— Shopping Links (Using Affiliate Links Supports Us!) —
Amazon https://amzn.to/3g594St
EwinRacing https://pcdeal.tv/EWin
Newegg https://pcdeal.tv/31ZiN3M
Walmart https://pcdeal.tv/2RyKrBH
EBay https://pcdeal.tv/3bE2mAa
BackBlaze https://pcdeal.tv/2HZU5Hs

— Game Store Links —
Humble Bundle https://pcdeal.tv/2HAIu2q
Fanatical https://pcdeal.tv/3uZviuh
GreenManGaming https://pcdeal.tv/GMG

— Direct Support —
Patreon https://pcdeal.tv/2HZTJR8
TD Merch https://pcdeal.tv/3pD6xlH

— Follow Us —
Twitch - https://pcdeal.tv/2lQQXGg
OFFICIAL_DISCLOSURE: true

PAGE (E-WIN Gaming Chairs & Desks - Best Heavy-Duty Brand for Gamers):
BUILT TOUGH FOR EVERY CHALLENGE
Perfect For Hardcore Gamers and Plus-sized Users Seeking Long-Lasting Chair.
Our E-WIN chairs are engineered for durability.supporting up to 550Ibs with ease.They're perfect for individuals seeking a sturdy.long-lasting chair that meets their unique comfort needs.Experience seamless support through every task-whether you're deep in gameplay or handling heavy-duty work.
Durability Approved by Pioneers Across Industries
Perfect For Hardcore Gamers and Plus-sized Users Seeking Long-Lasting Chair.
Our E-WIN chairs are engineered for durability.supporting up to 550Ibs with ease.They're perfect for individuals seeking a sturdy.long-lasting chair that meets their unique comfort needs.Experience seamless support through every task-whether you're deep in gameplay or handling heavy-duty work.
```
</details>


### UCd21m0AHf4Vx88Znty7v4Cw_1ZemHYCcHkA_af5ff07e

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "Before we continue, I'd like to give a shout out to the sponsors of this video. Honkai Star Rail"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["inadequate_disclosure"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
Before we continue, I'd like to give a shout out to the sponsors of this video. Honkai Star Rail, a cinematic turnbased RPG where you ride the Astral Express across galaxies, battling ancient gods, rogue AIs, and cosmic horrors. It's a blend of strategy, story, and stunning visuals that make every battle feel like an anime episode. And now, version 3.7 takes things up a notch. We're heading back to Amphorius with the long-awaited arrival of Sirene, the ice remembrance support whose abilities revolve around love, hope, and devastating true damage combos. Pair her with Casteries, Hyene, or the Trailblazer for some freeze and shatter chaos. First half reruns bring Casteries, Trippy, and Hyene from November the 5th to the 26th, followed by Fon, Cipher, and My Day from November the 26th to December the 16th. New players get 10 free special passes just for logging in, plus a golden companion spirit token to claim a five-star topaz. There's also the currency wars event, new areas, enemies, and more lore drops. Download Hawkeye Star Rail using my link and start your journey aboard the Astral Express today because the galaxy's calling and this ride's only getting

VIDEO: Top 10 Most Anticipated Winter 2026 Anime
DESCRIPTION:
Check out Honkai Star Rail here: https://track.echolinkslive.com/tk/sl/efmyrm

Winter 2026 is shaping up to be one of the strongest anime seasons in years, and this list breaks down the top upcoming shows every fan should have on their radar. From long-awaited adaptations to hyped new originals, Winter 2026 is loaded with action, mystery, fantasy, and the kind of world-building that takes over the internet the moment episode one drops.

In this video, we highlight the series generating the biggest buzz across trailers, announcements, and early previews. Whether you’re hunting for your next comfort binge or the next anime that’s going to dominate social media, this list has you covered.

If you enjoy breakdowns like this, make sure to like, share, and subscribe. More seasonal lists, reviews, and anime guides are on the way!

Patreon: https://www.patreon.com/ViniiTube
Join this channel to get access to perks:
https://www.youtube.com/channel/UCd21m0AHf4Vx88Znty7v4Cw/join
2nd Channel: https://www.youtube.com/c/ViniiTubeKai
Twitter:  https://twitter.com/ViniiTube
Instagram: https://www.instagram.com/viniitube/
Discord: https://discord.gg/98N5ugVwvx
#ViniiTube #Anime #AnimeTops
_

Credits to:
Voiceover by Jas Rao: http://jasrao.co.uk


Copyright Disclaimer Under Section 107 of the Copyright Act 1976, allowance is made for "fair use" for purposes such as criticism, comment, news reporting, teaching, scholarship, and research. Fair use is a use permitted by copyright statute that might otherwise be infringing.
OFFICIAL_DISCLOSURE: false

PAGE (Jas Rao - Voiceover artist):
My voice
If you want a British voice to tell your story in a clear, engaging way with a neutral accent and soft London tone, then I'm your man.
For over ten years, brands like Amazon Prime, Asda, Lidl, CIPD, the BBC have trusted me to get their messages across to audiences, whether it's in an explainer, animation, e-learning, TV/radio commercial or documentaries.
Amazon Prime
CIPD
NHS
ViniiTube
TV Regent
Tate
"Jas is a lovely, professional, genuine guy who delivers authentic, natural and conversational reads that are really engaging and relatable for the listener. I'd absolutely recommend Jas if you're looking for a VO for a project."
Amy Doyle, Maple Street Creative
"I've worked with Jas on a number of projects over many years. He's always been highly professional and a real pleasure to worth with."
Andrew Lees, Damn Fine Media
"Jas continues to be our first choice for our projects as he always impresses with his versatility, patience and efficiency."
Amar Sraan, Make It Reel
"Jas is incredibly professional and friendly and took direction well, delivering an engaging and authentic VO for our project."
Nicole Davis, Little Dot Studios
"Jas is the best in the business. If you ever need any type of VO work, he's your man. He's always on time and delivers quality work. I'd highly recommend."
Nathan Singleton, Hoop Nation
My reasons I'm your guy
Fancy trying my voice out on your project?
Email voiceover@jasrao.co.uk or fill out your details below, and I'll voice up to 30 seconds of your project, for free.
The small print:
```
</details>


### UC_hK9fOxyy_TM8FJGXIyG8Q_Cbq_9ad7u64_ed9273da

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "get a free starter pack with 15,000 food 30,000 gold and 10 gems plus play with the super Dar man Dragon"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure"]}
- errors: {"st3": {"missing": ["misleading_claim"], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
hey Dar man fam download Dragon City by clicking the link in the description or scan the QR code to get a free starter pack with 15,000 food 30,000 gold and 10 gems plus play with the super Dar man Dragon thanks for watching and I'll see you in the next [Music]

VIDEO: Mom Finds Out Her TEENAGER Is INSIDE GANG, What Happens Next Is Shocking | Dhar Mann Studios
DESCRIPTION:
▶️ Watch my favorite videos: https://www.youtube.com/playlist?list=PLnBCOhf_VBTVGGC7OryYH7wO87PCostB3



REMEMBER - We're not just telling stories, we're changing lives! So please help my videos change more lives by SHARING!




⚑  SHOP EXCLUSIVE MERCH! ⚑  
Shop Merch ➜ https://shop.dharmann.com/




📲 FREE APP! Get daily inspirational texts and see all your favorite videos on the Dhar Mann App: https://www.dharmann.com/app-update/  




⚑ CONNECT WITH ME ⚑ 
Instagram ➜ https://www.instagram.com/dhar.mann/
Facebook ➜ https://www.facebook.com/dharmannofficial
Snapchat ➜ https://www.snapchat.com/add/dhar-mann
Twitter ➜ https://twitter.com/dharmann
Pinterest ➜ https://pinterest.com/dharmannofficial
TikTok ➜ https://bit.ly/34P7DQR
Newsletter Sign-Up ➜ http://bit.ly/2uNssig




► INTERNATIONAL CHANNELS:
➜ Spanish: https://www.youtube.com/channel/UCL_AAt7DuXaF-eMtjygGWLQ?sub_confirmation=1
➜ Portuguese: https://www.youtube.com/channel/UClv8l2Oix3LF4TbPO_qq4HA?sub_confirmation=1
➜ Arabic: https://www.youtube.com/channel/UCLAZmh_ZIqeBPSZ3nkm5oZA?sub_confirmation=1
➜ Hindi: https://www.youtube.com/channel/UCks4m6NPNDwWMb6B5B5QaXA?sub_confirmation=1
➜ French: https://www.youtube.com/c/DharMannFran%C3%A7ais?sub_confirmation=1
➜ German: https://www.youtube.com/channel/UCsz0xVHocxsIs0Ya9bYLC2g?sub_confirmation=1
➜ Bahasa Indonesia: https://www.youtube.com/channel/UCHSz47qI_LRbQbsOWDsJ6rg?sub_confirmation=1
➜ Türkçe: https://www.youtube.com/channel/UCLmofNdlx4xN8BX70fW1zCA?sub_confirmation=1





★ OTHER CHANNELS ★ 
🔴 Bonus Videos ➜ https://www.youtube.com/channel/UC_J_2HxLExDed9fITZTUDXQ?sub_confirmation=1
🟡 Top Videos Channel ➜ https://www.youtube.com/channel/UCFJLO3HoTMzXYoeb2ocXe8w?sub_confirmation=1
🟠 Reactions Channel ➜ https://bit.ly/3ftiiYk
🟢 Extended Cuts ➜ https://bit.ly/3iBiNBS
Dhar and Laura Vlog ➜ http://bit.ly/DharAndLauraYouTube






★ RECOMMENDED VIDEO FOR YOU ★
- Gamer Gets Cyberbullied At School: https://youtu.be/kmG9maCcut4

★ RECOMMENDED PLAYLIST FOR YOU ★
- My Best Videos: https://www.youtube.com/playlist?list=PLnBCOhf_VBTVGGC7OryYH7wO87PCostB3






⚑ LEAVE A REVIEW ON IMDB ⚑ 
Share Your Review ➜ https://imdb.to/3zDwUgv








💥 NEW VIDEOS MONDAY - FRIDAY at 5pm (PST) 💥









CHAPTERS:
00:00   Mom Finds Out Her TEENAGER Is INSIDE GANG
25:52   Dhar's Outro
26:08   RECOMMENDED VIDEO TO WATCH





CREDITS:
Idea: Dhar Mann and Kayla Skipper  
Writer: Dhar Mann and Kayla Skipper
Director / Cinematographer: Carlos Orellana
Senior Managers: Ruben Ortiz, Tony Corsini, Christopher M. Brown
Assistant Director: Justin Doyle
Editor: Paulo Pohl
Assistant Editor: Javier Martinez
Composer: Rahul Dhakad
Colorist: Tania Alvarado
Sound Editor: Lucca Mendes
VFX Editor: Ian Kursakov
Trailer Editor: Brian Burkhardt
Casting and Locations Manager: Alisha Watson
Casting Associate: Kevin Svec
Pre Production Managers: Hope Mueller, Luz Ortiz
Post Production Manager: Brian Nelson, Allan Dave Castro
Bookings Manager: Kevin Acciani 
Bookings Associates: Nix Villarubin, Sherri Salazar, Khai Almendrala, Lea Leysis
Gaffer: Vaibhav Arora
Key Production Assistant: Colter Angel
Makeup/Hair: Brittany Fontaine
Sound Mixer / Boom Operator: Travis Hatcher 
Production Designer: Marco Chiong
Set Dresser: Cory Maracle
Props and Inventory Manager: Manuel Alcaraz
Props Associate: Armand Bashar
Inventory Associate: Joshua Bogert
Stunt Coordinator: Lorenzo Carreon 


Actors 

Kent - Devon Weetly
Gang Member 1 - Alexis Silvestre 
Gang Member 2 - Kevin Tates
Gang Member 3 - Danny Huen
Building Owner - David Alan Graf
Mom - Elektra Cohen
Customer - Jessica Basista
Boss - Koji Fueta
Woman - Rita Sehmi
Therapist - Paul Jerome
Dad - Brian Lewis
Tucker - Aydne Mekus 
Rich Mom - Tatiana Turan
Druggie - Atsuyuki Kono
Cop 1 - Vincent Sawyer
Cop 2 - Mike Carolina
Judge - Douglas Thaddeus Jeffrey
Bailiff - Gary Manrique
Uber Driver - Kais Boukthir
Younger Woman - Sera Lay
















  
#DharMannFam #Inspirational #Motivational
OFFICIAL_DISCLOSURE: true

PAGE (Dhar Mann Official Merch):
Top Sellers
-
No One Ever... T-Shirt
Regular price $18.00Regular priceUnit price / per$18.00Sale price $18.00 -
So You See... T-Shirt (Orchid)
Regular price $24.00Regular priceUnit price / per$24.00Sale price $24.00 -
So You See... Tri-Color T-Shirt (Black)
Regular price $24.00Regular priceUnit price / per$24.00Sale price $24.00 -
So You See... Pow YOUTH T-Shirt (Royal Blue)
Regular price $21.00Regular priceUnit price / per$21.00Sale price $21.00 -
Jay & Mikey Bookside... YOUTH T-Shirt (Royal Blue)
Regular price $21.00Regular priceUnit price / per$21.00Sale price $21.00 -
What Happens In The Dark T-Shirt
Regular price From $24.00Regular priceUnit price / per$24.00Sale price From $24.00 -
So You See Classic... T-Shirt (Navy)
Regular price $24.00Regular priceUnit price / per$24.00Sale price $24.00 -
#DharMannFam Hoodie (Maroon)
Regular price From $45.00Regular priceUnit price / per$45.00Sale price From $45.00 -
Changing Lives Two-Tone T-Shirt (Dark Grey)
Regular price $24.00Regular priceUnit price / per$24.00Sale price $24.00 -
#DharMannFam Joggers (Royal Blue)
Regular price From $40.00Regular priceUnit price / per$40.00Sale price From $40.00
Faves Restock
-
So You See... Crewneck (Black)
Regular price From $35.00Regular priceUnit price / per$35.00Sale price From $35.00 -
Shocking T-Shirt
Regular price From $24.00Regular priceUnit price / per$24.00Sale price From $24.00 -
Instantly Regrets It T-Shirt
Regular price From $24.00Regular priceUnit price / per$24.00Sale price From $24.00 -
Never Judge T-Shirt
Regular price From $24.00Regular priceUnit price / per$24.00Sale price From $24.00
```
</details>


### UC_0CVCfC_3iuHqmyClu59Uw_jR-BlSiyXcs_a2b1548b

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "DISCLAIMER: This video and description contains affiliate links, which means that if you click on one of the product links, I\u2019ll receive a small commission at no extra cost to you!"}, {"flag": "misleading_claim", "quote": "their Windows 10 Pro OEM key is 19.84 but if you use code ETA at checkout you can get 25 off"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["inadequate_disclosure"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
there are a bunch of differences here from the older model but before we get into it I do want to mention that this video is brought to you by urcd Keys I've actually been using this site for a couple years now they do offer steam Keys origin you played they even offer Microsoft applications like office but the main reason that I use urcd Keys is for their Windows keys right now their Windows 10 Pro OEM key is 19.84 but if you use code ETA at checkout you can get 25 off and another great thing about buying from here is they do accept Paypal I just did this build here I need to activate Windows I'm going to head over to my updates and security we're going to go to activation as you can see I've got Windows 10 Pro but it's not activated so I'm going to change product key I'm going to paste it in here choose next choose activate and windows is now activated we're ready to go my warning is totally gone and basically that's it though email your code once your payment is processed and that's basically it if you're interested in picking up cheap Windows 10 keys for your new pc builds I'll leave a link in the description so the overall design here for the 2023

VIDEO: The New GPD Win 4 Pro Has More Power Than Ever! Ryzen 7840U & Oculink!
DESCRIPTION:
The New 2023 Win 4 is here and it has more Power than ever! GPD has upgraded the Win 4 for 2023 by adding The Ryzen 7 7840U and an Oculink eGPU Port that pairs up very well with the new GPD G1 Radeon RX 7600M XT!
In this video we do an unboxing, go over the specs, Run some Benchmarks test some AAA Games on the Radeon 780M iGPU and we even test out the GPD G1 RX 7600M XT eGPU Over the new Win 4 Oculink port.

Learn More About the 2023 gpd win 4 Pro 7849u: https://gpd.hk/gpdwin4

Buy The 7840U Win 4 Pro Here: https://www.indiegogo.com/projects/gpd-win-4-smallest-amd-apu-handheld-console?utm_source=gog&gclid=Cj0KCQjw2eilBhCCARIsAG0Pf8tYTo5AREonI8lFMxnKohSbk8Cxmwz6u9Cw_s9MCjcXt2KnxBpjoGYaAtLdEALw_wcB&utm_medium=cpc#/

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

Want to send me something?
ETAPRIME
12400 Wake Union Church Rd PMB #239
Wake Forest, NC 27587 US

THIS VIDEO IS FOR EDUCATIONAL PURPOSES ONLY!

#GPD #7840U #etaprime
OFFICIAL_DISCLOSURE: true

PAGE (Buy MS Win 10 Pro OEM KEY GLOBAL-Lifetime at vip-urcdkey.com. Check MS Win 10 Pro OEM KEY GLOBAL-Lifetime comments on Facebook, Reddit and Trustpilot.):
MS Win 10 Pro OEM KEY GLOBAL-Lifetime
Note：
1. Free Wins 11 Update Available(this product allows you to upgrade your system to Wins 11 ).
2. This product cannot be used to upgrade your system from other version(ex. cannot upgrade HOME version to PRO).
Permanent,Authorized,Global Key
Win 10 is a personal computer operating system developed and released by MS as part of the Win NT family of operating systems. It was released on July 29,2015.It is the first version of Win that receives ongoing feature updates.
Win 10 is designed to be compatible with the hardware, software, and peripherals you already own. And always-enabled updates help you stay current on features and security for the supported lifetime of your device.Win 10 gives you absolutely the best experience for doing what you do. Stay focused with easy ways to snap apps in place and optimize your screen space for getting things done. See your open tasks in a single view and create virtual desktops to gain space or group things by project, like Off apps for work and games for play.Gaming just got even better with Win 10. Not only do your existing games work great, but now you can play and connect with gamers across Xbox One and Win 10 devices. From the best casual games to a new generation of PC gaming, Win 10 is built for games you love.
This product DOESN'T support upgrading directly from the Home system to Pro system, please download and install the Win 10 Pro system before activation.
```
</details>

