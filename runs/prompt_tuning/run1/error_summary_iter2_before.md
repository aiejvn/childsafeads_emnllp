# Error summary (9 instance(s) with at least one error)

## Per-tier error counts

- st1: 1/9
- st2: 2/9
- st3: 7/9

## st1 gold -> pred confusions

- physical_services -> digital_content_or_services: 1x

## st2 missing labels (gold had it, prediction missed it)

- other: missing 1x
- hardware_electronics: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- apps: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- other -> apps: 1x

## st3 missing labels (gold had it, prediction missed it)

- no_flag: missing 5x
- inadequate_disclosure: missing 2x

## st3 extra labels (prediction hallucinated, not in gold)

- misleading_claim: extra 4x
- direct_exhortation: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- no_flag -> misleading_claim: 4x
- no_flag -> direct_exhortation: 1x

## Detailed error instances

### UCvjsnl6wNtVIm0i1sCpN9Uw_ZtfPjRzDFlk_0e0fd08f

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics", "health"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "physical_goods", "st2": ["health"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": ["hardware_electronics"], "extra": []}, "st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
for midgame trainers and bosses but they just don't have enough to hack it in the Elite 4 speaking of these three there's something I discovered about this game while testing if You' like to know something cool I learned about nuz loocking this game that doesn't really have much to do with the tier list itself I'll tell you about it in today's sponsor segment presented by manscaped you see during my testing fired leaf green I found out that when you reach sadon city you actually gain access to the secret power TM just how today's sponsor manscape can help you access the secret power of a clean shave experience with the chairman pro package the main event is of course the chairman Pro manscapes premium electric foil shaver it's got those four blades for a super close shave it's waterproof and charges via USBC like we're used to for manscape and it's Flex adjust technology lets it perfectly adjust to your face to upgrade your shaving game kind of like how the infinite supply of secret power TMS and seladon lets use substantially upgrade a lot of kind of man midgame physical attackers 70 base power is quite High when you consider how bad a lot of the Gen 3 learn sets are and the best part is every Pokemon in the game learns it the best part of the chairman pro package on the other hand is that it not only comes with the premium chairman shaver it also comes with the manscape power shave gel for that satisfying safe wet wet shave experience it also includes the face Soother which is an after shave serum to cap things off at the end head on over to manscape.com peachell for 20% off this perfect gift for loved ones or for yourself and head on over to the department store and sell iton to gift otherwise terrible Pokémon their highest power physical move Pokemon like Pidgeotto Flareon Pinsir and Gyarados really appreciate this one Gyarados might be the biggest surprise

VIDEO: The Definitive Fire Red Nuzlocke Tier List
DESCRIPTION:
Thanks to MANSCAPED for sponsoring today's video! Get The Chairman™ Pro Package for 20% OFF + Free International Shipping this holiday season with promo code "PCHAL" at https://manscaped.com/pchal



Follow PokemonChallenges:
WATCH LIVE: http://www.twitch.tv/pchal
HIGHLIGHT CHANNEL:  https://www.youtube.com/pchaldaily

SUPPORT ON PATREON: http://www.patreon.com/pchal

TWITTER: http://www.twitter.com/pchaltv
REDDIT: http://www.reddit.com/r/pchaltv
INSTAGRAM: http://www.instagram.com/pchaltv
DISCORD: http://www.discord.gg/pchal

--------------------------------

Edited by: https://twitter.com/McWkEditing


Thumbnail by: https://twitter.com/magdraws


Script by: https://twitter.com/jackie_peanuts


--------------------------------

Channel Branding: https://twitter.com/NightkinStudio and https://twitter.com/cayiika



#pokemon #pokemonchallenges #nuzlocke
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


### UCkxctb0jr8vwa4Do6c6su0Q_WXIHmzIV-2s_441aa5d4

- gold: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "don't let hackers steal your financial details secure your data at expressvpn.com let's play"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st2": {"missing": ["other"], "extra": ["apps"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
let's play is sponsored by expressvpn don't let hackers steal your financial details secure your data at expressvpn.com let's play what's up all welcome to ttt

VIDEO: Attack of the Ghost Props! - Gmod: TTT
DESCRIPTION:
Check out bonus rounds here! ►  https://bit.ly/2KHsnEC
Thanks to ExpressVPN for sponsoring our channel http://expressvpn.com/letsplay
We're back with more Gmod: TTT! In this gameplay, the ghost props gang up on the traitors!
More TTT ►  https://bit.ly/3uiInj1
More Gmod ► https://bit.ly/3txkKEi

Innocent Roles:
• Innocent - No special abilities or weapons. Must take out all Traitors to win.
• Detective - Has equipment to find out who the Traitors are.
• Mercenary - Can buy both Traitor and Detective's Equipment.
• Glitch - Looks like a Traitor to other Traitors. Cannot see who the Traitors are.
• Phantom - Haunts their killer on Death. If that person dies, the Phantom comes back to life.

Traitor Roles:
• Traitor - Can buy unique equipment and weapons. Must take out all Innocents to win.
• Hypnotist - Can revive dead players into Traitors.
• Assassin - Has one Innocent as their target. Does extra damage to that target and half damage to everyone else. Gets a new target when the current target dies.

Monster Roles:
• Vampire - Can briefly become invisible. Gets health from dead players.
• Zombie - Can kill other players with a knife and turn them into other Zombies.

Other Roles:
• Jester - Role is shown to Traitors. If they die, they win. Cannot do damage to other players. Cannot be hurt by environmental or fall damage.
• Swapper - Appears as Jester to Traitors. If they are killed, the killer dies and the Swapper is revived as the killer's role.
• Killer - Needs to be the last player standing. Will start smoking if they don't kill anyone.

Detective Only Weapons:
• Randomat 4000 2.0 - Adds a random effect to the current round.
• Golden Deagle - One hit kill on Traitors, but will kill the holder if they shoot an innocent.
• Taser - Rag dolls a player when shot.
• Lightsaber - Gives the user a Lightsaber and Jedi powers.
• Homerun Bat - Hits a player into the air.
• Health Station - Heals anyone that uses it (Can also be bought by Mercenaries)
• Grappling Hook - Allows the user to swing around the map
• Freeze Grenade - Freezes all caught in the blast radius
• Demonic Possession - Allows the placer to take over someone elses body
• The Portal Gun - Places 2-way portals on most surfaces

Traitor Only Weapons
• Boomerang - Insta-kill throwable weapon that returns to the user.
• Barnacle Gun - Places an invisible Barnacle on the ceiling.
• Spring Trap - Launches someone into the air.
• Mimic Spawner - Creates Mimic props that spawn and attack players
• Bear Trap - Lays down a bear trap trapping anybody that steps in it.
• Weeping Angel Gun - Spawns a Weeping Angel on a targeted player
• Bee Grenade - Explodes releasing a swarm of bees that attack all players
• Harpoon - A thrown weapon that can one-shot the target
• Explosive Health Station - Fake health station that explodes after minimal use.
• Death Faker - Creates a decoy body of the user.
• Minifier - Makes the user smaller with less health.

Head to our site for early, uncensored content: http://bit.ly/AHSite

» Get your Let's Play merch: http://bit.ly/AHmerch
» Subscribe: http://bit.ly/SubToLP

About Let's Play:
Hello fellow Gamer. This you should watch me. I play game. Good. Thank you, thank you. If you watch me, I'm hot. Videos, they'll be better... The Let's Play view is the right thing to do YouTube, so do.

More from Let's Play:
» Achievement Hunter: http://bit.ly/AHYTChannel

https://www.youtube.com/user/letsplay

#Gmod #GarrysMod #TTT
OFFICIAL_DISCLOSURE: true

PAGE (ExpressVPN - A Fast and Secure VPN):
Protect Your Online Privacy with ExpressVPN
(Special offer for Let's Play Rockstar - LetsPlay viewers)
Secure access worldwide
Get the internet you expect with blazing-fast servers in 105 countries. Bypass content-based throttling, censorship, and blocking by schools or offices.
Use ExpressVPN
on every device
Phone, tablet, computer, router—no matter where you are or what devices you’re using, a single ExpressVPN subscription has got you covered.
One click to a safer internet
Going online doesn’t have to mean being exposed. Whether you’re shopping online or connecting to public Wi-Fi, keep your personal information more private and secure.
As seen in:
We sometimes pay expert sites to refer customers to us.
Why choose ExpressVPN?
Lightning-fast connectivity
Don’t wait. Our VPN network is built for speed, powered by next-generation technology.
Enjoy a borderless internet
Choose a VPN server location in one of 105 countries. Keep your real location to yourself.
Secure streaming on any network
Safely access all kinds of content, apps, and services, even over public Wi-Fi. You’ll get unlimited bandwidth, too.
Keep your online activity private
You’ll get a different IP address, helping to shield your identity. ExpressVPN keeps no connection or activity logs.
Stronger data protection
Stay secure with best-in-class encryption, DNS/IPv6 leak protection, kill switch, and split tunneling.
Live, 24-hour customer support
Email or chat live with members of our Support Team, anytime. ExpressVPN is here to help.
ExpressVPN is a VPN service not intended to be used as a means of copyright circumvention. Please read the ExpressVPN Terms of Service for more details.
The ExpressVPN 30-day money-back guarantee
If you’re not 100% satisfied with ExpressVPN, let us know within 30 days and we’ll refund your payment. It’s that simple.
30-day money-back guarantee
```
</details>


### UCUIJFJJLhxIrZVdAVdwL3bQ__i1RSaOkrq0_d4867adb

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
shiny pokemon recolor can even change yeah today's video is once again brought to you guys by expressvpn Virtual Private Networks allow you to freely browse the internet while keeping your private browsing data safe from government's ISPs and potential hacking threats with the click of a button expressvpn zap can instantly connect you to a network from all over the world even allowing you to access region-locked content one big thing that expressvpn helps me with is dealing with my own Internet service provider my wife and I both stream multiple days a week so we use a lot of data because streaming is their job we can't afford moments for my ISP throttles our internet speed with expressvpn I can connect to their private networks instead their network upload speeds are fast enough to stream at the bit rate I normally use and my ISP can't track our internet data expressvpn continues to be a top rated VPN service and if you're interested in trying it out you can get three months free with our special deal at expressvpn comm slash the j wits I'm very thankful to have a service that I use on a daily basis as a sponsor for the show and if you want to learn more you can find that in the link in the description box as well so let's talk good and bad Chinese we're gonna jump

VIDEO: Top 10 BEST (and WORST) Sword/Shield Shiny Pokemon
DESCRIPTION:
Get 3 FREE months of ExpressVPN:  http://expressvpn.com/TheJWittz

This video was sponsored by ExpressVPN

A new Pokémon generation means a whole new set of shiny Pokémon to hunt for! Today, I talk about my favorite (and least favorite) shiny designs from the new 'mons exclusive to the Galar region. 

Thumbnail art by @S3APARTY
http://Twitter.com/s3aparty

Sword/Shield Shiny Models Used from:
https://github.com/dokkanart/swsh-gifs
http://pkparaiso.com/

Want to follow my newest stuff? Follow me at:
Twitch.tv Streaming: http://twitch.tv/TheJWittz
Facebook: http://facebook.com/thejwittz
Twitter: http://twitter.com/thejwittz
OFFICIAL_DISCLOSURE: true

PAGE (ExpressVPN - A Fast and Secure VPN):
Protect Your Online Privacy with ExpressVPN
(Special offer for TheJWittz viewers)
Secure access worldwide
Get the internet you expect with blazing-fast servers in 105 countries. Bypass content-based throttling, censorship, and blocking by schools or offices.
Use ExpressVPN
on every device
Phone, tablet, computer, router—no matter where you are or what devices you’re using, a single ExpressVPN subscription has got you covered.
One click to a safer internet
Going online doesn’t have to mean being exposed. Whether you’re shopping online or connecting to public Wi-Fi, keep your personal information more private and secure.
As seen in:
We sometimes pay expert sites to refer customers to us.
Why choose ExpressVPN?
Lightning-fast connectivity
Don’t wait. Our VPN network is built for speed, powered by next-generation technology.
Enjoy a borderless internet
Choose a VPN server location in one of 105 countries. Keep your real location to yourself.
Secure streaming on any network
Safely access all kinds of content, apps, and services, even over public Wi-Fi. You’ll get unlimited bandwidth, too.
Keep your online activity private
You’ll get a different IP address, helping to shield your identity. ExpressVPN keeps no connection or activity logs.
Stronger data protection
Stay secure with best-in-class encryption, DNS/IPv6 leak protection, kill switch, and split tunneling.
Live, 24-hour customer support
Email or chat live with members of our Support Team, anytime. ExpressVPN is here to help.
ExpressVPN is a VPN service not intended to be used as a means of copyright circumvention. Please read the ExpressVPN Terms of Service for more details.
The ExpressVPN 30-day money-back guarantee
If you’re not 100% satisfied with ExpressVPN, let us know within 30 days and we’ll refund your payment. It’s that simple.
30-day money-back guarantee
```
</details>


### UCkxctb0jr8vwa4Do6c6su0Q_ftivh-R5yxQ_d7af87bb

- gold: {"st1": "digital_content_or_services", "st2": ["creator_community"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["creator_community"], "st3": ["direct_exhortation"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["direct_exhortation"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
for all you reality tv show fans and gamers make sure you sign up for rt first where you can watch all nine episodes and see who becomes the champion of survive block island [Music]

VIDEO: We Go to Space! | Ya Dead, Ya Dead (Finale)
DESCRIPTION:
Watch the First Episode of Survive Block Island Now! ► https://bit.ly/3wDyzRV
This week on Minecraft YDYD, only Ky, Trevor, and Matt are left alive. It's time to finish the rockets and leave this planet behind! But will the launch end in success or failure? (Modpack: Space Settlers)
YDYD Season 4 ► https://bit.ly/3PwaV2A

Head to our site for early, uncensored content: http://bit.ly/AHSite

» Get your Let's Play merch: http://bit.ly/AHmerch
» Subscribe: http://bit.ly/SubToLP

About Let's Play:
Hello fellow Gamer. This you should watch me. I play game. Good. Thank you, thank you. If you watch me, I'm hot. Videos, they'll be better... The Let's Play view is the right thing to do YouTube, so do.

More from Let's Play:
» Achievement Hunter: http://bit.ly/AHYTChannel

https://www.youtube.com/user/letsplay

#Minecraft #YDYD #Challenge
OFFICIAL_DISCLOSURE: true

PAGE (Rooster Teeth):
The funniest goddamn channel on the Internet, making you laugh since 2003. For more information, we’ve put together a handy guide...
There’s really no reason to visit any other website, given that we have everything you need here. But if you insist on going elsewhere you might as well follow us.
```
</details>


### UCkxctb0jr8vwa4Do6c6su0Q__PWsfLY94ps_725c2de0

- gold: {"st1": "physical_goods", "st2": ["food"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "physical_goods", "st2": ["food"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
oh my goodness sticking to your new year's resolutions can be rough but if you're looking to prioritize your wellness this year while saving money by maybe ordering a little less takeout and learning a little bit more on throwing down in the kitchen hey good news hellofresh has got you covered hellofresh has endless options to make cooking at home simple and enjoyable with their pre-portioned ingredients to your door i'm talking farm fresh produce within a week yo so skip that dreaded trip to the grocery store and stop wasting money on excess food we all know cooking at home is better than anything you could do when you order in so why not have a little help in the kitchen with hellofresh go to hellofresh.com let's play 16 and use the code let's play 16 for up to 16 free meals and three free gifts that's hellofresh.com let's play 16 and use the code let's play 16 for up to 16 free mails and three free gifts ah i think it was just that fredo caught

VIDEO: The Referee is Blind! - GTA V: Sumo
DESCRIPTION:
Go to http://hellofresh.com/LetsPlay16 and use code LetsPlay16 for up to 16 free meals AND 3 free gifts!
Joe learns the hard way that Sumo is cruel and controllers are king.
More GTA Mayhem ► https://bit.ly/3fSe0cp

Head to our site for early, uncensored content: http://bit.ly/AHSite

» Get your Let's Play merch: http://bit.ly/AHmerch
» Subscribe: http://bit.ly/SubToLP

About Let's Play:
Hello fellow Gamer. This you should watch me. I play game. Good. Thank you, thank you. If you watch me, I'm hot. Videos, they'll be better... The Let's Play view is the right thing to do YouTube, so do.

More from Let's Play:
» Achievement Hunter: http://bit.ly/AHYTChannel

https://www.youtube.com/user/letsplay

#GTAV #GTAOnline #Sumo
OFFICIAL_DISCLOSURE: true

PAGE (Podcast Promotions | HelloFresh):
Customize your box to fit your dinner needs: select how many people, how many recipes, and your meal preferences.
Choose from 100+ weekly recipes–including Veggie, Fit & Wholesome, and Quick & Easy dinner options.
We deliver meals right to your doorstep in a recyclable box.
DELICIOUS. HEALTHY.
READY FOR YOUR KITCHEN.
```
</details>


### UCl4vHlsw4s5TVGFpVsj54Rg_GmGH5tlW7TA_c5921ecb

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
who is that pokemon [Music] osotopia is a new game in dofus that offers a completely renewed experience the main goal of osotopia is to collect all 151 creatures and build a team to defeat the osotopia league even if you've never played dopes before this is the perfect time to start since all players in osotopia will start completely fresh so both new and returning players will get to discover new classes mechanics gameplay and objectives in osotopia every player gets to pick one of four starters you've got coolio the water type feveray the fire type windive the air type or drill bit the earth type i'm joining the feverey gang because i can't say no to a cute turtle with nunchucks let me know who you would pick over on the pole i'm running on my community tab if fifa a doesn't win i'm gonna riot in osotopia you can also start a guild to team up with your friends and adventure together but if you want a real challenge you can show off your skills by battling other players in one of the arenas so there's plenty to do in osotopia there's also an entirely free to play mobile version of dofus called dofa's touch they recently released a major update adding rare legendary weapons that you can hunt for kind of like a shiny hunt so check that out too there will be plenty of new players in osotopia as the servers only just launched on june 29. i'm registered for the heato server so sign up with the link in the description and maybe my fever8 and i will slap you around in the arena thanks to dofus for sponsoring the video and supporting the channel

VIDEO: Can Ash Ketchum Beat Pokemon Shield?
DESCRIPTION:
Sponsored by Osatopia, register here to check it out: https://bit.ly/3QHvHN1 Mobile users, check out DOFUS Touch: https://app.adjust.com/fcvpym5
Pokemon Shield challenge where I try to beat the game as Ash Ketchum / Satoshi. 
✅ SUBSCRIBE for more Pokemon challenges: https://www.youtube.com/keeganj?sub_confirmation=1

▶️ PLAYLIST of MONOTYPE Pokemon Hardcore Nuzlockes: https://www.youtube.com/playlist?list=PLoKICX4PmrWWSakAHQjpUtbCE_zlPwNQ4

🔴 VIDEO - Pokemon Sword with too many rules: https://youtu.be/NFMp1l9quhA

🌐 SOCIALS
 - Live on Twitch: https://twitch.tv/keeganjtv
 - Follow my Twitter: https://twitter.com/KeeganJtv
 - Join the Discord: https://discord.gg/RTKMxShMuX

Edited by Luker: https://www.youtube.com/c/LukerYT

#pokemon  #challenge  #shield  #sword  #ash
OFFICIAL_DISCLOSURE: true

PAGE (DOFUS, the Tactical MMORPG):
Dofus Retro
Dofus Touch
Wakfu
Waven
Support
Merchandising
Transmedia
Affiliate program
Game
Introduction
Classes
Gift Code
Leaderboards
Almanax
Why subscribe?
News
List of Bugs and Improvements
Check Out the Latest Update
All News
All Devblogs
All Updates (Patch Notes)
Shop
Buy Kamas
Forums
More
en
FR
ES
PT
Play
Dofus Retro
Dofus Touch
Wakfu
Waven
Support
Merchandising
Transmedia
Affiliate program
Game
Introduction
Classes
Gift Code
Leaderboards
Almanax
Why subscribe?
News
List of Bugs and Improvements
Check Out the Latest Update
All News
All Devblogs
All Updates (Patch Notes)
Shop
Buy Kamas
Forums
Play!
en
FR
ES
PT
New technology for a game that's
more lively, has better performance and boasts
new graphics.
Now in game
Download
A COMPLETE
GRAPHICAL OVERHAUL
A full graphical overhaul of the game: characters, animations and visual effects. New sensations for better immersion in the most vibrant World of Twelve you've ever seen.
* It doesn't mean anything but looks cool, right?
A COMPLETE
GRAPHICAL OVERHAUL
A full graphical overhaul of the game: characters, animations and visual effects. New sensations for better immersion in the most vibrant World of Twelve you've ever seen.
* It doesn't mean anything but looks cool, right?
MODERN AND REDESIGNED:
THE MOST
More user-friendly and fully customizable to your playstyle. Enjoy a more comfortable gaming experience thanks to the new possibilities offered by the Unity engine.
SEAMLESS
INTERFACE YET!
The turn-based combat at the core of your favorite MMO features new animations and new FX that will leave you spellbound.
CHARACTERS
AS ORIGINAL AS EVER
Attacking, defensive and strategic, 19 classes you won't see anywhere else.
Damage
Heals
Positioning
Tank
View all classes
View all classes
REORCHESTRATED
MUSIC
All the iconic themes reworked and enhanced for greater immersion. A more expansive soundtrack, ranging from the levity of a walk in the countryside to the frenetic action of a climactic battle.
Your browser does not support the audio element.
STAY TUNED!
A new era is beginning with a flood of new content coming soon!
```
</details>


### UCKUCm3FepRrl-VKhq0Wwajg_C09Azk6jgf4_ad321d22

- gold: {"st1": "physical_services", "st2": ["other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "With over 28 million downloads, SeatGeek is the number one rated ticketing app."}]}
- pred: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["misleading_claim"]}
- errors: {"st1": {"gold": "physical_services", "pred": "digital_content_or_services"}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
Hey man, y'all know I'm moving to Houston very soon. And y'all know I'mma have to go see them Texans. I'mma have to go see them Rockets. I'mma have to go see them Astros. And I'm going have to go to a lot of concerts, man. So, I'mma need some tickets. That's why I want to get a sponsor of today's video, SeatGeek. A big shout out. With over 28 million downloads, SeatGeek is the number one rated ticketing app. There are more than 70,000 events listed on SeatGeek, including sports, festivals, and concerts. Right now, you can get tickets to the weekend, the MLB, the NFL, and y'all know the NBA ain't too far behind. I love using SeatGeek because it's very easy to use. All you do is type in the event you want to go to, type in your location, where you at, look for a green icon. Green means good, red means bad. The tickets are rated on a scale of 1 to 10, so you know if you're getting a good deal or not. And to make y'all feel better, every ticket is backed by their buyer guarantee. So, I need y'all to get off that phone, go outside, touch grass, use code shack 10 to get 10% off your next set of tickets. Use code shack 10. Go have fun, man. Shout out to SeatGeek for sponsoring another video. G. Well,

VIDEO: GUNNA WENT DUMB! | GUNNA - THE LAST WUN | Album Reaction
DESCRIPTION:
#gunna #reaction #nolifeshaq 

Use my code for 10% off your next SeatGeek order*: https://seatgeek.onelink.me/RrnK/SHAQ10 Sponsored by SeatGeek. *Restrictions apply. Max $20 discount

Follow me on twitch: https://www.twitch.tv/nolifeshaq

Link to original video: 

Intro Music made by : https://www.youtube.com/user/joeynatomusic

Thanks for 4.9 Million, lets get to 5 Million by Aug.


Click Here To Subscribe! https://www.youtube.com/channel/UCKUCm3FepRrl-VKhq0Wwajg?view_as=subscriber
* FOLLOW MY SNAPCHAT: nolifeshaq
● FOLLOW YA BOY ON TWITTER https://twitter.com/NoLifeShaq
● INSTAGRAM https://instagram.com/nolifeshaq
Comment more vid ideas below!

*Copyright Disclaimer Under Section 107 of the Copyright Act 1976, allowance is made for "fair use" for purposes such as criticism, comment, news reporting, teaching, scholarship, and research. Fair use is a use permitted by copyright statute that might otherwise be infringing. Non-profit, educational or personal use tips the balance in favor of fair use. No copyright infringement intended. ALL RIGHTS BELONG TO THEIR RESPECTIVE OWNERS*
OFFICIAL_DISCLOSURE: true

PAGE (SeatGeek | Your Ticket to Sports Games, Concerts & Live Shows so Fans Can Fan):
Sports
MLB
NFL
NBA
NHL
MLS
World Cup 2026
NCAA Football
NCAA Basketball
NCAA Baseball
More College Sports
WNBA
More Baseball
More Football
More Hockey
More Soccer
Golf
Tennis
Fighting
Equestrian
Motorsports
Playoffs
More Sports
MLB All-Star Game
MLB Opening Day
MLB Spring Training
World Series
MLB Postseason
National League
American League
Arizona Diamondbacks
Athletics
Atlanta Braves
Baltimore Orioles
Boston Red Sox
Chicago Cubs
Chicago White Sox
Cincinnati Reds
Cleveland Guardians
Colorado Rockies
Detroit Tigers
Houston Astros
Kansas City Royals
Los Angeles Angels
Los Angeles Dodgers
Miami Marlins
Milwaukee Brewers
Minnesota Twins
New York Mets
New York Yankees
Philadelphia Phillies
Pittsburgh Pirates
San Diego Padres
San Francisco Giants
Seattle Mariners
St. Louis Cardinals
Tampa Bay Rays
Texas Rangers
Toronto Blue Jays
Washington Nationals
All MLB tickets
NFL Draft
Super Bowl
NFL Playoffs
Pro Bowl Games
NFC
AFC
Arizona Cardinals
Atlanta Falcons
Baltimore Ravens
Buffalo Bills
Carolina Panthers
Chicago Bears
Cincinnati Bengals
Cleveland Browns
Dallas Cowboys
Denver Broncos
Detroit Lions
Green Bay Packers
Houston Texans
Indianapolis Colts
Jacksonville Jaguars
Kansas City Chiefs
Las Vegas Raiders
Los Angeles Chargers
Los Angeles Rams
Miami Dolphins
Minnesota Vikings
New England Patriots
New Orleans Saints
New York Giants
New York Jets
Philadelphia Eagles
Pittsburgh Steelers
San Francisco 49ers
Seattle Seahawks
Tampa Bay Buccaneers
Tennessee Titans
Washington Commanders
All NFL tickets
NBA Playoffs
NBA Finals
NBA All-Star Game
NBA Eastern Conference
NBA Western Conference
Atlanta Hawks
Boston Celtics
Brooklyn Nets
Charlotte Hornets
Chicago Bulls
Cleveland Cavaliers
Dallas Mavericks
Denver Nuggets
Detroit Pistons
Golden State Warriors
Houston Rockets
Indiana Pacers
Los Angeles Clippers
Los Angeles Lakers
Memphis Grizzlies
Miami Heat
Milwaukee Bucks
Minnesota Timberwolves
New Orleans Pelicans
New York Knicks
Oklahoma City Thunder
Orlando Magic
Philadelphia 76ers
Phoenix Suns
Portland Trail Blazers
Sacramento Kings
San Antonio Spurs
Toronto Raptors
Utah Jazz
Washington Wizards
All NBA tickets
NHL Playoffs
Stanley Cup Finals
NHL All-Star Game
NHL Winter Classic
Anaheim Ducks
Boston Bruins
Buffalo Sabres
Calgary Flames
Carolina Hurricanes
Chicago Blackhawks
Colorado Avalanche
Columbus Blue Jackets
Dallas Stars
Detroit Red Wings
Edmonton Oilers
Florida Panthers
Los Angeles Kings
Minnesota Wild
Montreal Canadiens
Nashville Predators
New Jersey Devils
New York Islanders
New York Rangers
Ottawa Senators
Philadelphia Flyers
Pittsburgh Penguins
San Jose Sharks
Seattle Kraken
St. Louis Blues
Tampa Bay Lightning
Toronto Maple Leafs
Utah Mammoth
Vancouver Canucks
Vegas Golden Knights
Washington Capitals
Winnipeg Jets
All NHL tickets
MLS All-Star Game
MLS Playoffs
MLS Finals
Atlanta United FC
Austin FC
CF Montreal
Charlotte FC
Chicago Fire FC
Colorado Rapids
Columbus Crew
D.C. United
FC Cincinnati
FC Dallas
Houston Dynamo FC
Inter Miami CF
LA Galaxy
Los Angeles Football Club
Minnesota United FC
Nashville SC
New England Revolution
New York City FC
New York Red Bulls
Orlando City SC
Philadelphia Union
Portland Timbers
Real Salt Lake
San Diego FC
San Jose Earthquakes
Seattle Sounders FC
Sporting Kansas City
St. Louis CITY SC
Toronto FC
Vancouver Whitecaps FC
All MLS tickets
World Cup 2026 Final
World Cup 2026 Group Stage
World Cup 2026 Round of 32
World Cup 2026 Round of 16
World Cup 2026 Quarterfinals
World Cup 2026 Semifinals
World Cup 2026 Third Place
All World Cup 2026 tickets
Algeria National Football Team
Argentina National Football Team
Australia National Football Team
Austria National Football Team
Belgium National Football Team
Bosnia & Herzegovina National Football Team
Brazil National Football Team
Canada Mens National Soccer Team
Cape Verde National Football Team
Colombia Mens National Football Team
Croatia National Football Team
Curacao National Football Team
Czechia National Football Team
DR Congo National Football Team
Ecuador National Football Team
Egypt National Football Team
England National Football Team
France National Football Team
Germany National Football Team
Ghana National Football Team
Haiti National Football Team
Iran National Football Team
Iraq National Football Team
Ivory Coast National Football Team
Japan National Football Team
Jordan National Football Team
Mexico National Soccer Team
Morocco National Football Team
Netherlands National Football Team
New Zealand National Football Team
Norway National Football Team
Panama National Football Team
Paraguay National Football Team
Portugal Mens National Football Team
Qatar National Football Team
Saudi Arabia National Football Team
Scotland National Football Team
Senegal National Football Team
South Africa National Football Team
South Korea National Football Team
Spain National Football Team
Sweden Mens National Football Team
Switzerland National Football Team
Tunisia National Football Team
Turkey National Football Team
U.S. Mens National Soccer Team
Uruguay National Football Team
Uzbekistan National Football Team
College Football Playoffs
College Football Bowl Games
National Championship
SEC Football Schedule
Big Ten Football Schedule
Big 12 Football Schedule
ACC Football Schedule
Alabama Crimson Tide Football
Arkansas Razorbacks Football
Auburn Tigers Football
Florida Gators Football
Florida State Seminoles Football
Georgia Bulldogs Football
Indiana Hoosiers Football
Iowa Hawkeyes Football
LSU Tigers Football
Louisville Cardinals Football
Miami Hurricanes Football
Michigan State Spartans Football
Michigan Wolverines Football
Music City Kickoff
Notre Dame Fighting Irish Football
Ohio State Buckeyes Football
Oklahoma Sooners Football
Ole Miss Rebels Football
Oregon Ducks Football
Penn State Nittany Lions Football
Tennessee Volunteers Football
Texas A&M Aggies Football
Texas Longhorns Football
Texas Tech Red Raiders Football
USC Trojans Football
All NCAA Football tickets
NCAA Men's Basketball Tournament
NCAA Women's Basketball Tournament
SEC Basketball
Big Ten Basketball
Big 12 Basketball
ACC Basketball
Big East Basketball
Arizona Wildcats Mens Basketball
Auburn Tigers Mens Basketball
Creighton Bluejays Mens Basketball
Duke Blue Devils Mens Basketball
Florida Gators Mens Basketball
Gonzaga Bulldogs Mens Basketball
Hall of Fame Series
Indiana Hoosiers Mens Basketball
Iowa Hawkeyes Mens Basketball
Kansas Jayhawks Mens Basketball
Kentucky Wildcats Mens Basketball
Michigan Wolverines Mens Basketball
Middle Tennessee Blue Raiders Mens Basketball
NCAA Mens Basketball Tournament - East Regional
NCAA Mens Basketball Tournament - Midwest Regional
NCAA Mens Basketball Tournament Round of 16
NCAA Mens Basketball Tournament Round of 8
NCAA Mens Tournament First and Second Round
NCAA Tournament Charlotte
North Carolina Tar Heels Mens Basketball
Purdue Boilermakers Mens Basketball
UCLA Bruins Mens Basketball
UConn Huskies Mens Basketball
Wisconsin Badgers Mens Basketball
All NCAA Basketball tickets
NCAA College World Series
SEC Baseball
Big 12 Baseball Championship
ACC Baseball Championship
All NCAA Baseball tickets
NCAA Women's Basketball
NCAA Hockey
NCAA Softball
NCAA Women's Volleyball
NCAA Wrestling
All College Teams
WNBA All-Star Game
WNBA Finals
WNBA Playoffs
Atlanta Dream
Chicago Sky
Connecticut Sun
Dallas Wings
Golden State Valkyries
Indiana Fever
Las Vegas Aces
Los Angeles Sparks
Minnesota Lynx
New York Liberty
Phoenix Mercury
Portland Fire
Seattle Storm
Toronto Tempo
Washington Mystics
All WNBA tickets
MiLB
Triple-A Baseball
Double-A Baseball
High-A Baseball
Single-A Baseball
Banana Ball
UFL
CFL
IFL
All football tickets
PWHL
AHL
ECHL
WHL
SPHL
OHL
All hockey tickets
World Cup
NWSL
USL Championship
World Cup Group Stage
World Cup Quarterfinals
World Cup Round of 16
World Cup Round of 32
All soccer tickets
U.S. Open Golf
U.S. Women's Open Golf
PGA Championship
The Genesis Invitational
KPMG Women's PGA Championship
The Masters
The Chevron Championship
2026 U.S. Amateur Golf Championship
2026 U.S. Senior 
```
</details>


### UCRcam0RTtiv85oGAiPpbz6g_0wReI3gLnhQ_e9f142ca

- gold: {"st1": "digital_content_or_services", "st2": ["education"], "st3": ["inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "Backend devs make a median salary of 175k."}, {"flag": "inadequate_disclosure", "quote": "Thanks to BADEV for sponsoring this video."}]}
- pred: {"st1": "digital_content_or_services", "st2": ["education"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["inadequate_disclosure"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
this. Boom. Boom. Boom. Boom. Boom. Oh my god. Yes. We got like four fireballs right there. So, yeah, I just destroyed the entire Minecraft world by just changing a few lines of code. And that is a power of programming. So if you ever wanted to learn how to code, try boot thedev. They focus on back-end development by using Python, JavaScript, and more. And you learn by building real project like a real job. They even teach you how to build your own AI agent in Python. So when I'm modify Minecraft logic, like how fire spreads, that's basically the back end. So coding is way easier than you think. So, this bug makes a [music] sword tag add health point instead of removing it. So, I changed one plus sign to a minus and boom, it is fixed. If you ever get stuck, they've got an AI tutor to guide you and when you finish, you earn a certificate that can help you land a job. Backend devs make a median salary of 175k. So, if I can accidentally delete the world, imagine what you can build on purpose. Try it for free to see how it works [music] and then use my code element X to get 25% off for your first year to unlock everything. Thanks to BADEV for sponsoring this video. Okay, so I've changed the fire code a

VIDEO: So I changed the FIRE's code in Minecraft
DESCRIPTION:
Click this link https://boot.dev/?promo=ELEMENTX and use my code  ELEMENTX  to get 25% off your first payment for boot.dev.


In this video I made the fire block in minecraft more EXTREME
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

I make clickbait videos.. that aren't clickbaits, because I code the most unthinkable ideas in Minecraft that looks like clickbaits.

I use all sorts of technology! I use AI, such as Chat GPT or Claude.AI, the Java programming language and MCP reborn to modify the video game's code. Artificial Intelligence definitely helps a lot, but only used for the most basic tasks.

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 
My Computer specs


RTX 4080 Super with i9-14900K
RTX4060 + i9 14900HX

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
♫Music used:♫
🎸https://open.spotify.com/artist/6bnZW05ijGE4iuyfiVd3km
(These are my own music, and you may use them for free if you're a content creator. We just ask to credit the music in your video with a link.)
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
👥Social Media👥

✅ EMAIL for business, brand partnerships and for personal: officialelementx47@gmail.com
✅ Everything else: http://linktr.ee/elementxyt

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
OFFICIAL_DISCLOSURE: true

PAGE (Learn to Code | Boot.dev):
Avoid tutorial hell
by writing a ton of code
Stay motivated with
a game-like curriculum
Build portfolio projects
to prove your skills
Delve deeper
into foundational concepts
Learn flexibly online
without interrupting your life
For 1% the price of college
to minimize your financial risk
Backend Path
Learn Backend development with our curriculum packed with courses on API design, authentication, databases, and CDNs.
Explore the Backend course roadmap
DevOps Path
Master DevOps engineering by following our courses on Linux, Docker, AWS, CI/CD, cloud deployments, and kubernetes.
Explore the DevOps course roadmap
Help! I don't get why my code makes the player's health go up when she's hit by the sword.
*Adjusts wizard hat thoughtfully*
Ah, it looks like you used the wrong operator! Which one do you think will subtract from her health (instead of adding to it) in your take_damage
function?
lessons completed
courses completed
xp earned
Showing 1-9 of 5882
Learn in-demand back-end technologies like Python, SQL, and Go
Spend about 12 months if you're doing it part-time
We don't tolerate unhappy students: ask for a refund within 30 days and it's yours
Cloud Engineer
$189,000
Backend Developer
$175,000
Site Reliability Engineer
$165,000
DevOps Engineer
$165,000
Data Engineer
$150,000
Frontend Developer
$145,000
Data Analyst
$100,956
Some folks look at the job data and assume that front-end positions are the only option for new learners. On the contrary, there is big demand for backend and data-oriented positions!
If you like working with data, logic, and servers, you might just enjoy the back-end, data-focused curriculum here on Boot.dev. And similar to the frontend, most data and backend positions don't require a specific degree from a university... but you do need to know your stuff!
Yes! It's free to create an account and start learning. You'll get all the immersive and interactive features for free for a few chapters. After that, if you still haven't paid for a membership, you'll be in read-only (content only) mode.
```
</details>


### UCshoKvlZGZ20rVgazZp5vnQ_P0frYN-VOOA_c35603f8

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "Thanks to Apex Hosting for sponsoring this series! Use code \"CaptainSparklez\" to get 25% off your own server's first month: https://apexhost.gg/CaptainSparklez"}, {"flag": "misleading_claim", "quote": "Use code \"CaptainSparklez\" to get 25% off your own server's first month"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["inadequate_disclosure"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
if you've enjoyed, playlist if you've missed any episodes in the description. And of course, code CaptainSparklez if you feel like picking up Hytale or a server through Apex Hosting. Thanks for watching and I'll see you in the next

VIDEO: Hytale Ep. 4 - Devastated Lands
DESCRIPTION:
Today in Hytale we discover memories and go on an expedition
Thanks to Apex Hosting for sponsoring this series! Use code "CaptainSparklez" to get 25% off your own server's first month: https://apexhost.gg/CaptainSparklez
Hytale Playlist ► https://www.youtube.com/playlist?list=PLSUHnOQiYNg3j8EdchPMposlHY3QZXje8

My Links
● My gear (code CaptainSparklez): https://logi.gg/captainsparklez
● Live streams: https://www.twitch.tv/captainsparklez
● Tiktok: https://www.tiktok.com/@realcaptainsparklez
● Twitter: http://twitter.com/CaptainSparklez
● Instagram: http://instagram.com/jordanmaron

Thanks for watching, dudes! Likes and feedback are always appreciated :)
OFFICIAL_DISCLOSURE: false

PAGE (Apex Hosting):
Get the extreme performance of dedicated processor cores up to 4.8 GHz with our EX Series servers featuring 4 exclusive vCores of a Ryzen 9 5900X (US & EU) | Ryzen 7 5800X (APAC) CPU to ensure your server is operating at peak performance. This plan is great for demanding servers or large communities, and easy to manage through our control panel.
The Ultimate Server Experience
Instantly switch between 20+ games, and over 200+ mod packs at the click of a button.
We combine cutting edge hardware with industry-leading service to deliver unmatched performance, reliability, and ease of use — whether you're running a private server or growing a large gaming community.
All orders include a free web address for your server making it easy to connect for all.
All our servers come with unlimited slots, so your community can grow without boundaries — no caps, no extra fees, just freedom.
The best customer service team in the industry featuring 24/7 live chat assistance from experienced server administrators for your always online server.
Offsite automatic backups guarantee your data will not be lost due to any bad configurations or hardware failures.
Our test servers around the world provide the lowest ping for you and your players.
Trusted by players who know what smooth gameplay feels like.
Everytime i get a server with friends i come to apex hosting its simple to use and the customer support is amazing everyone is always so helpful. when i have from the easiest problem to something more complex they are always there to help 100/10 Apex hosting is the goat !!!!!
DeliveredAgents are always patient and share the same interest of solving the problem with you. ive never had a bad experience with support here, this is the perfect hosting company to host a server through with its versatile features and support. really its great, fi you need a server to run choose this
DeliveredHosted with Apex 4 times now, never let me down. Decent prices for the packs I buy, and the support is always punctual and helps so much. Always gonna come back to Apex :)
DeliveredConnect with fellow gamers, get quick support, and stay updated on news & events.
Join NowGet tips, updates & exclusive offers for your multiplayer server adventures — straight to your inbox.
We care about the protection of your data. Read our Privacy Policy.
```
</details>

