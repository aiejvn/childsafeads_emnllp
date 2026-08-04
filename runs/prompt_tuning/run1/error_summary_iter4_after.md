# Error summary (7 instance(s) with at least one error)

## Per-tier error counts

- st1: 0/7
- st2: 1/7
- st3: 7/7

## st2 missing labels (gold had it, prediction missed it)

- other: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- apps: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- other -> apps: 1x

## st3 missing labels (gold had it, prediction missed it)

- insufficient_context: missing 1x
- age_restricted_or_prohibited_product: missing 1x
- no_flag: missing 1x

## st3 extra labels (prediction hallucinated, not in gold)

- inadequate_disclosure: extra 4x
- misleading_claim: extra 3x
- undisclosed_advertising: extra 2x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- insufficient_context -> undisclosed_advertising: 1x
- age_restricted_or_prohibited_product -> inadequate_disclosure: 1x
- age_restricted_or_prohibited_product -> misleading_claim: 1x
- no_flag -> inadequate_disclosure: 1x
- no_flag -> misleading_claim: 1x

## Detailed error instances

### UCshoKvlZGZ20rVgazZp5vnQ_MzDh8Gndkw4_79a5a43b

- gold: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["other"], "extra": ["apps"]}, "st3": {"missing": ["no_flag"], "extra": ["inadequate_disclosure", "misleading_claim"]}}

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
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st3": {"missing": ["age_restricted_or_prohibited_product"], "extra": ["inadequate_disclosure", "misleading_claim"]}}

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


### UC8x3sm8ITT0wyQowgeGgAOw_Pof4MzzL7zQ_c827a2a2

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "raycons are affordable great sounding earbuds that come in at half the price of other premium headphones"}]}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st3": {"missing": [], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
started but first I am literally sleeping on my dad's couch so this video is brought to you by raycon listen dog if you spent any time on YouTube you probably heard of raycon before and they're pretty slick for those of you that haven't raycons are affordable great sounding earbuds that come in at half the price of other premium headphones I've been using it at the gym whenever I'm bored as hell I just put on podcasts or a long ass wendon video and it helps me tune out while I pick up heavy objects and put them down again for 1 and 1/2 hours they also got these extra little protective cases which you can get for them I got the pink Cloud's one cuz I'm fruity like that but I genuinely don't know why other headphone Brands don't do this they also come with a [ __ ] ton of different earplug sizes so no matter howed up your ears are you can still get a comfortable and noise isolating fit it also comes in a ton of different colors and has a long ass battery life so do yourself a favor by clicking that link in the description and go to by ron.com Leon talkot to get up to 30% off sitewide massive shout out to rayon for sponsoring this video and I hope you all enjoy all right back to the video Welcome to Cracker space or as the

VIDEO: Nvm, Omori is Better
DESCRIPTION:
Go to https://buyraycon.com/leontalksalot to get up to 30% off sitewide! Brought to you by Raycon.

Please criticize my videos as harshly as possible.
OFFICIAL_DISCLOSURE: false

PAGE (Leon Talks a Lot Viewers):
Leon Talks a Lot Viewers
Bringing Back The Fan Faves
Millions of units sold - Now with ANC mode
Active Noise Cancellation
With ANC and Awareness modes, you choose the vibe. Tune out the train or tune into your surroundings.
Fast Charge
With 8 hours of playtime and a fast charging case, the earbuds will last when you need them most.
Perfect Size For Every Ear
Every ear is different (obviously) so we decided to make 6 differently sized gel tips designed to fit any size.
Plus...
32 Hours Battery Life
Capsule charges the earbuds, so you don't have to.
Crystal Clear Call
Built in microphone for making phone calls.
Weather Resistant
Withstand rain, snow, or even the sweatiest workouts.
Bluetooth 5.3
Pairs with Bluetooth devices such as iPhone and Android.
Limited Time Offer - Save Now
All viewers can save!
Take 20% OFF
Discount is automatically applied!
35 UNITS REMAINING
"Long-lasting, high-quality audio"
"High demand, high quality, but affordable"
We Care About the Smallest Detail
We spent two years developing The Everyday Earbuds because every little detail matters. And partly because we’re a bit insane.
The final result? A crisp sounding earbud that’s a pleasure to wear, easy to use, loud enough to drown out your neighbor’s lawnmower, and a battery that stays charged longer. We hope you love it as much as we do.
```
</details>


### UC7-hR5EfgpM6oHfiGDkxfMA_0_yTDGioWyg_811b53fc

- gold: {"st1": "physical_goods", "st2": ["other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "Wow 25 off of a helix mattress plus two free pillows"}, {"flag": "misleading_claim", "quote": "with free shipping in the United States"}, {"flag": "misleading_claim", "quote": "Helix has a 100 night sleep trial"}, {"flag": "misleading_claim", "quote": "Helix mattresses have a 10 year warranty and they even offer financing options and flexible payment plans"}]}
- pred: {"st1": "physical_goods", "st2": ["other"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st3": {"missing": [], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
by much [Music] but first this video is sponsored by Helix sleep maker of Premium mattresses and bedding that is customized to fit your needs do you feel anxiety at the thought of shopping for a new mattress well Helix is conveniently shipped right to your door and I'm being totally honest with you when I tell you that I really do sleep on a helix mattress my old mattress needed to be replaced and Along Came Helix we've had our Helix for about a year now and my wife and I both still comment on how comfortable it is we've even recommended it to friends and family actually this isn't even in the script we were going to visit some in-laws and their mattress was terrible and we're like What if we bought you a present a new mattress a helix mattress and we did that just because we didn't want to sleep on their mattress when we wanted to sleep on a helix for that we really did that that's how good they are anyway back to the script hey use my link and take the Helix sleep quiz to find out which mattress is the best fit for you I sleep on my back and my wife sleeps on her stomach the dust Lux mattress was suggested and has worked out great the best part about all of this is that Helix delivers your mattress right to your door with free shipping in the United States the mattress comes rolled up in a box and it's super easy to set up by yourself and if it makes you nervous to buy something that you haven't tried relax because Helix has a 100 night sleep trial so you get more than three months to make sure that you love it and believe me you will love it yeah I was skeptical about a mattress delivered in a box but it is not one of those foam Toppers that instantly turns to Mush it's a mix of foam and coil and it is an actual real comfortable mattress plus Helix mattresses have a 10 year warranty and they even offer financing options and flexible payment plans so a great night's sleep is never far away I love my Helix mattress and I think you will too if you're looking for a new bed check out Helix sleep it's the perfect time to upgrade your sleep with Wow 25 off of a helix mattress plus two free pillows click the link in this video's description below or just go to Helix sleep dot to find out more about this limited time offer let's begin our proper analysis by

VIDEO: Is It Worth It To Spend $40.00 on $0.36 Worth Of Magic: The Gathering Cards? A New Secret Lair Fail
DESCRIPTION:
Thank you Helix Sleep for sponsoring! Click here https://helixsleep.com/tolarian to get 25% off your Helix mattress (plus two free pillows!) during their 4th of July Sale. If you miss this limited time offer, you can still get 20% off using my link! Offers subject to change. #helixsleep 

Watch Jim Davis And Bloody Play By Different Standards on Shuffle Up & Play: https://youtu.be/IZJw0wuDlYE

Looking to draft Lord Of The Rings? Check out our complete set draft guide here: https://youtu.be/n_e-fchpck0

Are you looking to Shuffle Up & Play games of Magic: The Gathering over webcam? The "Looking For Game" section of our Patron Discord is 100% free and open to everyone: https://discord.gg/tolariancommunitycollege

#MTG #magicthegathering    

The Professor's special Card Kingdom link: 
 http://www.cardkingdom.com/TCC

TCC Shirts and Playmats http://www.tolariancommunitycollege.com/

Or you can support me directly over at Patreon -https://www.patreon.com/tolariancommunitycollege

Music Courtesy Of
"Vintage Education" Kevin MacLeod (incompetech.com) 
Licensed under Creative Commons: By Attribution 3.0
http://creativecommons.org/licenses/by/3.0/
OFFICIAL_DISCLOSURE: true

PAGE (Why Helix is the Best Mattress for Couples):
Customers who have slept on a Helix for over 100 nights report a better sleep quality from customers sleeping on the one size fits all models from other brands. Custom is better. It’s just that simple. But don’t just take it from us. Here’s what everyone’s saying:
Customers who have slept on a Helix for over 100 nights report a better sleep quality from customers sleeping on the one size fits all models from other brands. Custom is better.
It’s just that simple. But don’t just take it from us.
Here’s what everyone’s saying:
"We went with the split option because of our very different sleep preferences, and we are both sleeping like babies.
Jared & Regan
“The custom sides of our Helix leave us both feeling great from the moment we lay down until we begrudgingly crawl out of bed in the morning.”
Jeff & Julie
"The split mattress allows both my husband and me to experience our individual sleep styles without disturbing each other!"
Therese & Joe
Supremely contouring and reactively comfortable. Helix’s proprietary cool sleeping foam.
Individually pocketed coils, optimized for pressure relief, improved airflow, and reduced transfer of motion.
Varying densities and high quality allow us to get specific with personalization.
A hybrid mattress is a dream comfort team that knows how to work together. Don’t settle for one type of material when you can have a complementary mix of three.
Supremely contouring and reactively comfortable. Helix’s proprietary cool sleeping foam.
Individually pocketed coils, optimized for pressure relief, improved airflow, and reduced transfer of motion.
Varying densities and high quality allow us to get specific with personalization.
A hybrid mattress is a dream comfort team that knows how
to work together.
Don’t settle for one type of material when you can have a complementary mix of three.
Jane
Jane and Kristian just got married and need a new mattress. Kristian needs his mattress to be as firm as a table top, while Jane likes things more on the medium soft side. Jane never gets hot and Kristian is always hot. Jane is a back sleeper while Kristian is a side sleeper. She’s a petite 5’1” while he’s got a bulkier build and towers at 6’6”.
Unlike the competition, Helix can offer Jane and Kristian a Dual Comfort mattress
to begin them on marital sleep bliss.
Kristian
FEEL
Medium-Soft
FEEL
Low BMI
TEMPERATURE
Sleeps Cool
POSITION
Back
FEEL
Firm
POSITION
Side Sleeper
TEMPERATURE
Always Hot
FEEL
High BMI
Jane and Kristian just got married and need a new mattress. Kristian needs his mattress to be as firm as a table top, while Jane likes things more on the medium soft side. Jane never gets hot and Kristian is always hot. Jane is a back sleeper while Kristian is a side sleeper. She’s a petite 5’1” while he’s got a bulkier build and towers at 6’6”.
Unlike the competition, Helix
can offer Jane and Kristian a Dual Comfort mattress to begin them on marital sleep bliss.
Top Layer
Softer piece of foam with the right amount of sink.
Top-Support Layer
Medium dense support layer placed high in the mattress because she’s a back sleeper.
Bottom-Support Layer
Pressure relief lower down since she doesn’t have obvious pressure points like Kristian.
Foundation Layer
Same support layer across the bottom as all Helix Mattresses.
Top Layer
Firmer piece on top with less sink.
Jane's Side
Kristian's Side
Bottom-Support Layer
Pressure relief layer more supportive to support his larger frame.
Top-Support Layer
Microcoils closer to the top for pressure relief since he exclusively sleeps on his side and improved airflow to keep him cool.
Foundation Layer
Same support layer across the bottom as all Helix Mattresses.
Jane and Kristian just got married and need a new mattress. Kristian needs his mattress to be as firm as a table top, while Jane likes things more on the medium soft side. Jane never gets hot and Kristian is always hot. Jane is a back sleeper while Kristian is a side sleeper. She’s a petite 5’1” while he’s got a bulkier build and towers at 6’6”.
Unlike the competition, Helix
can offer Jane and Kristian a Dual Comfort mattress to begin them on marital sleep bliss.
Jane
Jane and Kristian just got married and need a new mattress. Kristian needs his mattress to be as firm as a table top, while Jane likes things more on the medium soft side. Jane never gets hot and Kristian is always hot. Jane is a back sleeper while Kristian is a side sleeper. She’s a petite 5’1” while he’s got a bulkier build and towers at 6’6”.
Unlike the competition, Helix can offer Jane and Kristian a Dual Comfort mattress
to begin them on marital sleep bliss.
Kristian
FEEL
Medium-Soft
FEEL
Low BMI
TEMPERATURE
Sleeps Cool
POSITION
Back
FEEL
Firm
POSITION
Side Sleeper
TEMPERATURE
Always Hot
FEEL
High BMI
Jane's Side
Top Layer
Softer piece of foam with the right amount of sink.
Top-Support Layer
Medium dense support layer placed high in the mattress because she’s a back sleeper.
Bottom-Support Layer
Pressure relief lower down since she doesn’t have obvious pressure points like Kristian.
Foundation Layer
Same support layer across the bottom as all Helix Mattresses.
Foundation Layer
Same support layer across the bottom as all Helix Mattresses.
Top-Support Layer
Microcoils closer to the top
for pressure relief since he exclusively sleeps on his side and improved airflow to keep him cool.
Bottom-Support Layer
Pressure relief layer more supportive to support his
larger frame.
Kristian's Side
Top Layer
Firmer piece on top with less sink.
Supremely contouring and reactively comfortable. Helix’s proprietary cool sleeping foam.
Individually pocketed coils, optimized for pressure relief, improved airflow, and reduced transfer of motion.
Varying densities and high quality allow us to get specific with personalization.
A hybrid mattress is a dream comfort team that knows how to work together. Don’t settle for one type of material when you can have a complementary mix of three.
Jeff & Julie
“The split mattress allows both my husband and me to experience our individual sleep styles without disturbing each other!"
Therese & Joe
“The custom sides of our Helix leave us both feeling great from the moment we lay down until we begrudgingly crawl out of bed in the morning."
Jared & Regan
“We went with the split option because of our very different sleep preferences, and we are both sleeping like babies."
Find Your Perfect Mattress Match
Flexible Payment Plans
Fourth of July Sale:
Use discount code HELIXPARTNER20 for 20% off sitewide
Or enjoy special discounts on Luxe and Elite mattresses:
Use discount code LUXE25 for 25% off Luxe mattresses
Use discount code ELITE30 for 30% off Elite mattresses
"I've always had a lot of trouble sleeping. Once I switched to a Helix that was precisely matched to my needs, I found that I could sleep through the night, which has made a tremendous difference."
Dr. Andrew Huberman
Professor of Neurobiology and Host, Huberman Lab
Dr. Andrew Huberman
"We've had our Helix mattress for two and a half years and are thrilled with how well we sleep and how well it has kept its shape. My husband had constant back problems with our old mattresses, but now we both wake up feeling rested and recharged and recommend Helix to everyone we know."
Dawn Madsen
"I might be Helix's biggest fan. I am a 4x Moonlight Luxe owner, and have gotten mattresses for multiple family members and friends (who all are sleeping better now, of course). I can't imagine life without my Helix mattress...and bed frame...and pillows. At least it's a healthy obsession!"
Ashley Hesseltine
Co-host, Girls Gotta Eat
"Sleep and sex are the two most important things in my life, so a good mattress is a necessity. I couldn’t live without my Helix mattress and pillows, and can’t recommend the mattress topper enough, too."
Rayna Greenberg
Co-host, Girls Gotta Eat
Ashley Hesseltine and Rayna Greenberg
"My family loves our Helix mattresses! After taking the online sleep quiz we were paired with the Midnight Luxe. We put one on every
```
</details>


### UCd21m0AHf4Vx88Znty7v4Cw_1ZemHYCcHkA_af5ff07e

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "Before we continue, I'd like to give a shout out to the sponsors of this video. Honkai Star Rail"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st3": {"missing": [], "extra": ["misleading_claim"]}}

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
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["undisclosed_advertising", "misleading_claim"]}
- errors: {"st3": {"missing": [], "extra": ["undisclosed_advertising"]}}

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

