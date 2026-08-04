# Error summary (8 instance(s) with at least one error)

## Per-tier error counts

- st1: 1/8
- st2: 5/8
- st3: 8/8

## st1 gold -> pred confusions

- physical_goods -> digital_content_or_services: 1x

## st2 missing labels (gold had it, prediction missed it)

- fashion: missing 3x
- creator_community: missing 1x
- hardware_electronics: missing 1x
- gambling_adjacent: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- health: extra 1x
- apps: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- fashion -> health: 1x
- creator_community -> apps: 1x
- fashion -> apps: 1x

## st3 missing labels (gold had it, prediction missed it)

- direct_exhortation: missing 3x
- no_flag: missing 2x
- undisclosed_advertising: missing 1x

## st3 extra labels (prediction hallucinated, not in gold)

- inadequate_disclosure: extra 7x
- misleading_claim: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- direct_exhortation -> inadequate_disclosure: 2x
- no_flag -> inadequate_disclosure: 2x
- undisclosed_advertising -> inadequate_disclosure: 1x
- no_flag -> misleading_claim: 1x

## Detailed error instances

### UCeePGrzBN3B2GurSkd_bwPQ_LYKOF4ng50A_74fbff80

- gold: {"st1": "physical_goods", "st2": ["creator_community", "fashion"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure"]}
- errors: {"st1": {"gold": "physical_goods", "pred": "digital_content_or_services"}, "st2": {"missing": ["creator_community", "fashion"], "extra": ["apps"]}, "st3": {"missing": ["no_flag"], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
at the start of the game. Let's go and Hang on. Hang on. Let's fix this problem. It's time for a huge community challenge and I need you guys to help me on this one. This video is sponsored by Asphalt 9 Legends available iOS, Android, Xbox, and PC. Three rounds. Corvette versus Bentley. Me, Black Panther, versus AR12. Each round gives one point to the winning team. So, I really really do need your help on this one. From June 1st to 2nd, we'll be picking from you guys. So, please do help me. Leave your Asphalt 9 player ID down below in the comments. And also let us know what platform you play on. From June 9th to 15th, we'll play events together against the opposing club. But also from June 9th to 15th, this is where the bulk of you guys have to help us. If you jump into the daily event section, you'll be able to choose the big clash event. Choose my car, the Chevrolet Corvette Stingray. That's the better one. Complete the event is how you place a vote. And placing a vote with the one with the most votes will win. And then finally, the big event. Me versus AR12 Gaming head to head. And the winner wins $10,000. We're actually going to be like in the game. Download the game. There's a link below in the description to check out more information. Down below in the comments, let us know your ID and your platform. And of course, let's show them how we do. Welcome to my one of my most

VIDEO: The Last Need for Speed Game by Criterion...
DESCRIPTION:
Download Asphalt 9 Legends now! - https://gmlft.co/BP-BigClash-Int
Thank you to Gameloft for sponsoring the video
I'm sure we all know this game very well by now, but before we jump into their next world with Need for Speed 2022... let's jump into their previous NFS title!
❱ Subscribe for more NFS gameplay! - http://sub.bpyt.me/
❱ Watch me LIVE - Right here!
❱ Official Store  - http://panthaa.store
❱ Support the channel! - http://member.bpyt.me

❱ Twitter - http://twitter.com/BlackPanthaaYT
❱ Instagram - https://www.instagram.com/blackpanthaayt/
❱ Join our community Discord http://discord.gg/blackpanthaa

❱ My gameplay, lighting and camera are all captured using Elgato - http://e.lga.to/BlackPanthaa

❱ Outro by Madloops - http://outro.bpyt.me/

#a9TheBigClash #sponsoredbygameloft
OFFICIAL_DISCLOSURE: true

PAGE (BlackPanthaa Official Merchandise - BlackPanthaa Store):
let's get started
-
Always Online Bad (Limited PRE-PURCHASE)
- Vendor
- BlackPanthaa
- Regular price
- €17,95
- Sale price
- €17,95
- Regular price
-
- Unit price
- per
Sold out -
NEW Classic Hoodie
- Vendor
- BlackPanthaa
- Regular price
- €46,95
- Sale price
- €46,95
- Regular price
-
- Unit price
- per
Sold out -
BlackPanthaa Original Sticker
- Vendor
- BlackPanthaa
- Regular price
- €2,95
- Sale price
- €2,95
- Regular price
-
- Unit price
- per
Sold out -
NEW Classic Tee
- Vendor
- BlackPanthaa
- Regular price
- €27,95
- Sale price
- €27,95
- Regular price
-
- Unit price
- per
Sold out -
Eclipse Tee
- Vendor
- BlackPanthaa
- Regular price
- €23,95
- Sale price
- €23,95
- Regular price
-
- Unit price
- per
Sold out -
Stealth Tee
- Vendor
- BlackPanthaa
- Regular price
- €11,95
- Sale price
- €11,95
- Regular price
-
- Unit price
- per
Sold out -
Eclipse Hoodie
- Vendor
- BlackPanthaa
- Regular price
- €41,95
- Sale price
- €41,95
- Regular price
-
- Unit price
- per
Sold out -
Nobeds Original Sticker
- Vendor
- Nobeds
- Regular price
- €2,95
- Sale price
- €2,95
- Regular price
-
- Unit price
- per
Sold out -
Face Mask
- Vendor
- BlackPanthaa
- Regular price
- €8,95
- Sale price
- €8,95
- Regular price
-
- Unit price
- per
Sold out -
Street Art Tee
- Vendor
- BlackPanthaa
- Regular price
- €21,95
- Sale price
- €21,95
- Regular price
-
- Unit price
- per
Sold out -
Launch Sticker
- Vendor
- Nobeds
- Regular price
- €4,95
- Sale price
- €4,95
- Regular price
-
- Unit price
- per
Sold out
Progress Clothing line
The progress tee is the newest addition to the store. If you're reading this now, you've already missed out! Make sure to keep your eyes and ears pealed to be in with the chance of buying from the next drop!
```
</details>


### UCXwpLFOlJTROLn_26LQQVRA_HvhFVBz5n_0_5dbff9be

- gold: {"st1": "physical_goods", "st2": ["fashion", "food"], "st3": ["direct_exhortation", "misleading_claim", "undisclosed_advertising"], "st3_evidence": [{"flag": "misleading_claim", "quote": "Do you get dehydrated a lot? Need a drink that won't break the bank? Then you should get gamer subs."}, {"flag": "misleading_claim", "quote": "It's caffeine-free and caffeinated in two kinds of tubs."}, {"flag": "direct_exhortation", "quote": "Then you should get gamer subs."}]}
- pred: {"st1": "physical_goods", "st2": ["food"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["fashion"], "extra": []}, "st3": {"missing": ["direct_exhortation", "undisclosed_advertising"], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
>> I need better music to like break dance [music] probably. I should also while I'm here drink my gamer subs discount code chaa look we match hold on we match like look at this look at this COORDINATION [screaming] look behold what are you doing what are you doing with my freaking knee >> go farther up >> it needs to go >> like that >> see much better >> gamer subs Discount code chaa. Do you get dehydrated a lot? Need a drink that won't break the bank? Then you should get gamer subs. They believe in traditional American values like anime girl. It's caffeine-free and caffeinated in two kinds of tubs. Gamers improved my SOCIAL LIFE AND NOW I can stop seeing people in the mirror. Popular flavors include guacamole gamer fart 9000, sweet sixpack, blowhole blast, and sploosh. Use discount chaa at checkout [music] for 10% off. Stay hydrated. Stay hydrated. Stay hydrated. Always love you. Let me just

VIDEO: She said WHAT?!
DESCRIPTION:
ChaCha your VTuber Mom cooks and shames an entire culture!
Come visit me LIVE! ➡️ https://www.twitch.tv/chachayourvmom ⬅️

☕💟 SOCIALS 💟☕
💟 https://www.youtube.com/@Chachavodsofficial
☕ https://twitter.com/ChaChayourvmom
💟 https://www.instagram.com/chachayourvmom/
☕ https://www.tiktok.com/@chachayourvmom/
💟 https://discord.com/invite/chachayourvmom

✨Merch✨
➡️ https://uwumarket.us/collections/chachayourvmom ⬅️

✨Gamersupps✨
❗Use code CHACHA for 10% off❗
➡️ https://gamersupps.gg/ ⬅️

🎬Editors🎬
https://twitter.com/Firehardt_ & https://twitter.com/Pewpawe
❤︎₊ ⊹ --------------------------------------------------------------------- ❤︎₊ ⊹
Hi there! I'm ChaCha, your virtual VTuber mom! I'm known as every VTubers mother. I love just chatting and reacting with my chat. I also play games and a variety of other content. So get cozy and enjoy my react videos, ASMR, unboxings, horror gameplay & much more!

#vtuber #animegirl #envtuber #chachayourvmom #vtuberen #vtubers #vtuberclips #vtuberreaction
OFFICIAL_DISCLOSURE: false

PAGE (The Leader in Gaming Energy & Nutrition; Waifu Cups/Gaming Supplements):
Guacamole Gamer Fart 9000 by RussianBadger - 100 Servings ★★★★★ (10883) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Crimson Moonburst by LordAethelstan - 100 Servings ★★★★★ (526) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
GOOD - 100 Servings ★★★★★ (3233) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
BBL GG by Clooless - 100 Servings ★★★★★ (947) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Anime Girl Thigh - 100 Servings ★★★★★ (2598) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Foxly GG by FoxyReine - 100 Servings ★★★★★ (383) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Kissy Kissy Passion GG by Numi - 100 Servings ★★★★★ (392) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Nile Nectar GG by Trickywi - 100 Servings ★★★★★ (369) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Schlatt Milk - 100 Servings ★★★★★ (497) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
CaseOh's Nuclear Bombsicle - 100 Servings ★★★★★ (605) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Sinder's Pyro Power - 100 Servings ★★★★★ (653) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Kaho's Guil-tea Pleasure - 100 Servings ★★★★★ (292) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
BaoBerry GG by Bao - 100 Servings ★★★★★ (370) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Cherry Limecicle - 100 Servings ★★★★★ (958) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Brand Risk - 100 Servings ★★★★★ (2398) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Dragonfruit Punch - 100 Servings ★★★★★ (8667) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Crusaderade GG by SwaggerSouls - 100 Servings ★★★★★ (345) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Sweet Six Pack - 100 Servings ★★★★★ (823) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK: GOOD Night - 40 Servings ★★★★★ (17) €32,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK: Cookies and Dream - 30 Servings ★★★★★ (19) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK Razzz Berry Sorbet - 40 Servings ★★★★★ (473) €32,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK Blueberry Lemon Cake - 40 Servings ★★★★★ (202) €30,00 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK: Knockout - 40 Servings ★★★★★ (4) €32,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK Grape - 40 Servings ★★★★★ (390) €32,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK: Room Service - 30 Servings ★★★★★ (10) €43,95 Add One-time purchase6 week subscription2 week subscription4 week subscription
Doggy Style GG by Buffpup Caffeine Free - 100 Servings ★★★★★ (374) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
GOOD Caffeine Free - 100 Servings ★★★★★ (799) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Goof Juice Caffeine Free - 100 Servings ★★★★★ (298) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Chug Juice GG by LazarBeam Caffeine Free - 100 Servings ★★★★★ (123) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Sinder's Pyro Power Caffeine Free - 100 Servings ★★★★★ (216) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Caseoh's Nuclear Bombsicle GAMERAID - 30 Servings ★★★★★ (16) €40,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Waifu Shirt: Knockers ★★★★★ (6) €37,95 Add Select Waifu Shirt: Knockers variant S M L XL 2XL 3XL 4XL 5XL 6XL
Brand Risk Caffeine Free - 100 Servings ★★★★★ (721) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Acid Rain GG by Rainhoe Caffeine Free - 100 Servings ★★★★★ (196) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Klaxosaur's Blood by DARLING in the FRANXX Caffeine Free - 100 Servings ★★★★★ (190) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Pestily's Antidote GG Caffeine Free - 100 Servings ★★★★★ (146) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
```
</details>


### UCUIJFJJLhxIrZVdAVdwL3bQ_DJU2mS0n7iE_47ea25ef

- gold: {"st1": "digital_content_or_services", "st2": ["apps", "gambling_adjacent"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["gambling_adjacent"], "extra": []}, "st3": {"missing": ["no_flag"], "extra": ["inadequate_disclosure", "misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
[Music] today's video is brought to you by the battle cats for iOS and Android which I can say is without a doubt the craziest tower defense game I've ever played in this strategy game you'll manage your economy create an army of chibi cats to defend yourself and summon new units to your team to take on even the nastiest threats use cheap melee units like the macho cat tank with the wall cat out range your opponent with these sexy legs yeah wait what bro god I don't even know this is a cat anymore ok I want that one wait what is the OH oh man but somehow this isn't the cat that surprised me the most the battle cats have a brand new collaboration going on right now from the last place I expected the virtual singer herself Hatsune Miku this event s limited edition characters like Miku herself Kagamine irenan Len and Miku as a cat there's also a ton of special stages featuring official Hudson and Miku music unique enemies and a ton of free rewards for players that check it out the Miku collection unfortunately won't be here forever her special event only less until April 13th you can download the battle kits for free on iOS and Android by clicking the link at the top of this video's description the battle cats franchise has been around a long time but they always find new creative ways to put a smile in my face I never bet life thought I'd get to say this but thank you to the battle cats and Hatsune Miku for helping support our content and I hope you guys will give it a shot before the event is up well mama always said

VIDEO: The "BEST" Yu-Gi-Oh Game
DESCRIPTION:
Download Battle Cats for free: http://get.gameinfluencer.com/SHaC  
Thank you PONOS for sponsoring this video!

Yu-Gi-Oh Millenium is a hideous board game from Mattel that was released in 2002. It is also, somehow, the best Yu-Gi-Oh game. Let's talk about it. 

Intro animation by Artsy Theo:
https://twitter.com/Theologicallyy

Intro theme song by Matt Houston:
https://www.twitch.tv/matthouston

Want to follow my newest stuff? Follow me at:
Twitch.tv Streaming: http://twitch.tv/TheJWittz
Facebook: http://facebook.com/thejwittz
Twitter: http://twitter.com/thejwittz
OFFICIAL_DISCLOSURE: true

PAGE (The Battle Cats App - App Store):
This game is perfect if you like weird things. The cats in this game range from adorable to an Eldritch Horrors that could destroy the universe, and I love that. I also like that it looks like an easy Mobil game at first glance, but it definitely isn’t, this game can be absurdly difficult sometimes, but that’s okay because you can just get more powerful and then come back to the really hard stage. There are some downsides though. First of all, duplicate Ubers. This is definitely one of the worst things that can happen to you, it happened to me, and it really feels like the game does that to make you upset. Second of all, the enemy cats in cat unlock stages. We all no about the we have that at home meme, and well, the cat you fight is the one you want and the one you get is usually the cat you have at home it get what I mean, I get that it has to be hard but giving crazed titan cat 1,000,000 health is a bit much. Third and final is cool looking Ubers being very weak. This might be more of a personal thing, but I feel like the cooler the uber looks, the more powerful it should be, this is defective a big issue with iron legion, because they all look awesome, but are really only good against zombie enemies, and the Nekolugas, because they all look really freaky and cool but I could literally kill them with a feather. Also please make an ultra soul that is a reference to transformers please, and make it effective against metal and alien enemies. Love this game. Battle cats forever.
```
</details>


### UCXwpLFOlJTROLn_26LQQVRA_LnTK4UWE9TQ_5dbff9be

- gold: {"st1": "physical_goods", "st2": ["fashion", "food"], "st3": ["direct_exhortation", "inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "\u2728Gamersupps\u2728\n\u2757Use code CHACHA for 10% off\u2757\n\u27a1\ufe0f https://gamersupps.gg/ \u2b05\ufe0f"}, {"flag": "misleading_claim", "quote": "Gamer Supps improved MY SOCIAL LIFE AND NOW I CAN STOP seeing people in the mirror."}, {"flag": "direct_exhortation", "quote": "Then you should get Gamer Supps."}]}
- pred: {"st1": "physical_goods", "st2": ["food", "health"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["fashion"], "extra": ["health"]}, "st3": {"missing": ["direct_exhortation"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
can reconsider the Church of Aviation again. Thank you. I appreciate that. >> Okay. Okay. Okay. Do you get dehydrated a lot and need a drink that won't break the bank? Then you should get Gamer Supps. They believe in traditional American values like anime girl thighs. IT'S CAFFEINE-FREE AND CAFFEINATED. In two kinds of tubs. Gamer Supps improved MY SOCIAL LIFE AND NOW I CAN STOP seeing people in the mirror. Popular flavors include Guacamole Gamer Fart 9000, [music] Sweet Six Pack, Blow Hole Blast, AND SPLOOSH. USE DISCOUNT CHA Cha at checkout for 10% off. Stay hydrated. Stay hydrated. Stay hydrated. Um. Let's go with it. Is this

VIDEO: A REAL LIFE Pilot Takes ChaCha on a FLIGHT!
DESCRIPTION:
ChaCha your VTuber Mom learns how planes work, then gets taken on a real flight with a pilot while live!
Come visit me LIVE! ➡️ https://www.twitch.tv/chachayourvmom ⬅️
Please check out Brendan @OnMapleWings - https://www.instagram.com/onmaplewings

☕💟 SOCIALS 💟☕
💟 https://www.youtube.com/@Chachavodsofficial
☕ https://twitter.com/ChaChayourvmom
💟 https://www.instagram.com/chachayourvmom/
☕ https://www.tiktok.com/@chachayourvmom/
💟 https://discord.com/invite/chachayourvmom
☕ VOD CHANNEL: https://www.youtube.com/@Chachavodsofficial

✨Merch✨
➡️ https://uwumarket.us/collections/chachayourvmom ⬅️

✨Gamersupps✨
❗Use code CHACHA for 10% off❗
➡️ https://gamersupps.gg/ ⬅️

🎬Editor🎬
https://twitter.com/pixelsblurred
❤︎₊ ⊹ --------------------------------------------------------------------- ❤︎₊ ⊹
Hi there! I'm ChaCha, your virtual VTuber mom! I'm known as every VTubers mother. I love just chatting and reacting with my chat. I also play games and a variety of other content. So get cozy and enjoy my react videos, ASMR, unboxings, horror gameplay & much more!

#vtuber #animegirl #airplane #flying #envtuber #chachayourvmom #vtuberen #vtubers #vtuberclips
OFFICIAL_DISCLOSURE: false

PAGE (The Leader in Gaming Energy & Nutrition; Waifu Cups/Gaming Supplements):
Guacamole Gamer Fart 9000 by RussianBadger - 100 Servings ★★★★★ (10883) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Crimson Moonburst by LordAethelstan - 100 Servings ★★★★★ (526) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
GOOD - 100 Servings ★★★★★ (3233) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
BBL GG by Clooless - 100 Servings ★★★★★ (947) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Anime Girl Thigh - 100 Servings ★★★★★ (2598) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Foxly GG by FoxyReine - 100 Servings ★★★★★ (383) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Kissy Kissy Passion GG by Numi - 100 Servings ★★★★★ (392) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Nile Nectar GG by Trickywi - 100 Servings ★★★★★ (369) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Schlatt Milk - 100 Servings ★★★★★ (497) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
CaseOh's Nuclear Bombsicle - 100 Servings ★★★★★ (605) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Sinder's Pyro Power - 100 Servings ★★★★★ (653) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Kaho's Guil-tea Pleasure - 100 Servings ★★★★★ (292) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
BaoBerry GG by Bao - 100 Servings ★★★★★ (370) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Cherry Limecicle - 100 Servings ★★★★★ (958) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Brand Risk - 100 Servings ★★★★★ (2398) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Dragonfruit Punch - 100 Servings ★★★★★ (8667) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Crusaderade GG by SwaggerSouls - 100 Servings ★★★★★ (345) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Sweet Six Pack - 100 Servings ★★★★★ (823) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK: GOOD Night - 40 Servings ★★★★★ (17) €32,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK: Cookies and Dream - 30 Servings ★★★★★ (19) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK Razzz Berry Sorbet - 40 Servings ★★★★★ (473) €32,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK Blueberry Lemon Cake - 40 Servings ★★★★★ (202) €30,00 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK: Knockout - 40 Servings ★★★★★ (4) €32,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK Grape - 40 Servings ★★★★★ (390) €32,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
AFK: Room Service - 30 Servings ★★★★★ (10) €43,95 Add One-time purchase6 week subscription2 week subscription4 week subscription
Doggy Style GG by Buffpup Caffeine Free - 100 Servings ★★★★★ (374) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
GOOD Caffeine Free - 100 Servings ★★★★★ (799) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Goof Juice Caffeine Free - 100 Servings ★★★★★ (298) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Chug Juice GG by LazarBeam Caffeine Free - 100 Servings ★★★★★ (123) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Sinder's Pyro Power Caffeine Free - 100 Servings ★★★★★ (216) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Caseoh's Nuclear Bombsicle GAMERAID - 30 Servings ★★★★★ (16) €40,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Waifu Shirt: Knockers ★★★★★ (6) €37,95 Add Select Waifu Shirt: Knockers variant S M L XL 2XL 3XL 4XL 5XL 6XL
Brand Risk Caffeine Free - 100 Servings ★★★★★ (721) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Acid Rain GG by Rainhoe Caffeine Free - 100 Servings ★★★★★ (196) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Klaxosaur's Blood by DARLING in the FRANXX Caffeine Free - 100 Servings ★★★★★ (190) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
Pestily's Antidote GG Caffeine Free - 100 Servings ★★★★★ (146) €43,95 Add One-time purchase2 week subscription4 week subscription6 week subscription
```
</details>


### UC8JOgFXp-I3YV6dsKqqQdUw_Ij8zjnO5zfY_8b447c43

- gold: {"st1": "physical_goods", "st2": ["fashion"], "st3": ["direct_exhortation", "misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "who makes the most comfortable bombas socks in the history of feet it's bombas as well as underwear t-shirt slippers"}, {"flag": "direct_exhortation", "quote": "it's time that you tried bombas plus new customers get 20% off their first purchase just go to bombas.com Caroline and use code caroline2 at checkout"}]}
- pred: {"st1": "physical_goods", "st2": ["fashion"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st3": {"missing": ["direct_exhortation"], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
in there so yeah that is uh it's kind of delightful it fits in like so perfectly quickly I also wanted to take a moment to address some questions I've been getting recently people have been asking things like hey girl why you looking so comfy bombers why you looking so cozy bombers why you looking so cutie bombas bombas bombas bombas hey girl why you looking so sponsored bombas why you looking so Doner bombas why you looking so demure bombas bombas bombas who makes the most comfortable bombas socks in the history of feet it's bombas as well as underwear t-shirt slippers bombas bombas bombas bom get out of here and did you know that with every item purchased bombas donates an item to someone experiencing homelessness one item purchased equals one item donated in fact did you know that bombas makes the number one two and three most requested items in homeless shelters and with bombas there's a 100% happiness guarantee free returns and exchanges even if your dog eats a sock or you lose one during a dance it's time that you tried bombas plus new customers get 20% off their first purchase just go to bombas.com Caroline and use code caroline2 at checkout hey girl why you looking so comfy bombers why you looking so cozy bombers why you looking so cutie bombas bombas bombas bombas hey girl why you looking so bombas hey girl why you looking so bombus hey girl why you looking so bombus dang you looking freaking BB [Music]

VIDEO: TEENSY Balcony Makeover for my boyfriend...in 1 FREAKIN DAY!
DESCRIPTION:
My boyfriend's teensy tiny balcony is an industrial death hole. I'm on a mission to transform it into a tree house haven..in one freakin day. 💕 Thank you to Bombas for sponsoring this video! One Purchased = One Donated, so go to https://bombas.com/caroline and use code caroline20 at checkout for 20% off your first purchase.

Thanks to Bombas for sponsoring:)

***

*MY DATING ADVICE / BREAKUPS / CAREER ADVICE - on my podcast on YOUTUBE!*
The Dating Advice I wish I knew sooner - https://rb.gy/d1auiv
Breakups, Hookups, and Dating - https://rb.gy/662csp
Hacks for Making Friends as an ADULT! - https://rb.gy/wc428l
Career Advice I wish i knew sooner - https://rb.gy/vzgl7r

***


💕 𝗠𝗬 𝗣𝗢𝗗𝗖𝗔𝗦𝗧
○  SPOTIFY - https://shorturl.at/u9gjb
○  APPLE PODCASTS - https://shorturl.at/lstI2

💕  𝗟𝗜𝗡𝗞𝗦
○ Amazon Favorites - https://shorturl.at/OtD8M
○ Home Decor Favorites - https://shorturl.at/YcBC9
○ My Brother's Handmade Vases - https://go.magik.ly/ml/23bge/
○ Outfit Favorites - https://shorturl.at/f8uyb

💕 𝗙𝗜𝗠𝗟𝗜𝗡𝗚 𝗘𝗤𝗨𝗜𝗣𝗠𝗘𝗡𝗧
○ Microphone - https://amzn.to/3xgU4ZG
○ Camera - https://amzn.to/3ljewWU
○ Lens - https://amzn.to/3lxCAFS
○ Handheld Microphone - https://amzn.to/3OWmbGK
○ Podcasting / Voiceover Microphone - https://amzn.to/3YkmmhE
○ Camera tripod - https://amzn.to/3xfPuuw
○ Phone tripod - https://amzn.to/3xkw3AE

💕  𝐕𝐈𝐃𝐄𝐎 𝐂𝐎𝐍𝐓𝐄𝐍𝐓𝐒
00:00 - Intro
00:44 - my boyfriend's apartment
1:35 - The Balcony!
3:01 - Dealing with Rental Restrictions
4:13 - The design vision
5:00 - I LOVE THIS FLOORING
6:12 - forced compliments
7:22 - Addressing your questions
9:07 - Terrifying.
11:33 - Seating furniture!
13:50 - Space savers
15:08 - Building a VERTICAL GARDEN!
17:10 - Last minute touches
18:50 - Forced compliments PART 2!
19:26 - Before & After
21:30 - Cut footage


💕  𝐃𝐈𝐒𝐂𝐋𝐀𝐈𝐌𝐄𝐑 
All opinions are my own. Some links listed are affiliate links which means I earn a small commission if anyone decides to purchase through them. Thank you so much for your support!

Please note that I am not a professional, in fact I am the literal opposite. I am just a plebeian out here loose on the streets. Things that I am NOT: a builder, trainer, craftsman, therapist, nutritionist, physical therapist, medical professional or anything else. All projects seen on my channel must be completed at your own risk and responsibility. Please see your own professional or counselor for professional support. Do your research and be safe!

#interiordesign #washingtondc #roommakeover
OFFICIAL_DISCLOSURE: true

PAGE (Youtube LP - Video):
By providing my email, l am consenting to receive Bombas emails and Email-Based Advertising. For additional information, please see our Privacy Policy.
The Bombas Customer Happiness Team is your go-to when you need a recommendation, a return, or just a reason to smile. Seriously, reach out. Even just to say hi.
Notice to Consumers: Bombas may collect "Identifiers", “Characteristics of protected classifications" under California, federal or other applicable law, "Commercial information", "Internet or other electronic network activity", and/or "Geolocation data" when you visit this website, and may use such information to draw inferences and for other operational and commercial purposes. For more information, please see our Privacy Policy.
```
</details>


### UCzOfLNkiScJp3U_h_QlvHHg_SdreTDi0XUA_949fed47

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics", "health"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "the handyman delivers a quick close shave with a unique dualblade system the standard foil shaver combined with the long hair leveler blade can knock down up to 3 days worth of growth"}]}
- pred: {"st1": "physical_goods", "st2": ["health"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": ["hardware_electronics"], "extra": []}, "st3": {"missing": [], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
know was that this base location would take us on a roller coaster of a WIP day okay okay now you guys know the drill by now with manscaped smooth balls means better recoil control and rust obviously but I'm not here today to talk about the incredible lawn mower 4.0 with its skin safe and WS prooof technology because you know all that already so let me introduce you instead to the handyman compact face shaver sleek and stylish the handyman delivers a quick close shave with a unique dualblade system the standard foil shaver combined with the long hair leveler blade can knock down up to 3 days worth of growth helping you maintain a clean well-groomed appearance cordless and waterproof the handyman is the perfect traveling companion and it's even airplane friendly boasting up to 60 Minutes of runtime on a single charge you'll have more than enough time to squeeze in multiple shaves without running out of power so what are you waiting for head on over to manscaped and use code Will Jim today to get 20% off plus free shipping on the handyman and other manscaped products thanks again to manscaped for sponsoring today's video so Stevie and I had built

VIDEO: When a Pro Builder and a 10,000 hour Farmer play Official Rust...
DESCRIPTION:
#Rust #RustSoloSurvival 

Thanks to MANSCAPED for sponsoring today's video! Get 20% OFF + Free International Shipping with promo code "WILLJUM" at https://manscaped.com/willjum

Today, im taking on Rusts biggest clan server, main. With my favourite boyfriend @StevieDoesYT ,  Subscribe for chapter 2!!

WILLJUM'S SOLO ONLY SERVERS!

Join my servers discord for info https://discord.gg/willjum
[EU] Willjum's solo only server 
Connect willjum.eu
[NA] Willjum's solo only server
Connect willjum.US



MY SECOND CHANNEL : https://www.youtube.com/channel/UCgYBxwW1sqqKMb4KjfvDZgQ/videos

MERCH :
 https://willjum.merchforall.com/

Massive thank you to my current Patrons, Thanks to your help i was able to afford my new PC! so thank you! if you want to support me further: 

https://www.patreon.com/Willjum

MY TWITCH :
https://www.twitch.tv/willjum





You can find my amazing thumbnail artist @sinhunsan1 on twitter!

Give me a follow on twitter! https://twitter.com/willjum1

Business email (for non business stuff just message me on discord) willjum@afkcreators.com

Spinky's Base build! https://youtu.be/i_Sew1f4N14?si=TDCo2NUFjeXdkD7n

Fantastic Music From 
Velvet: https://www.youtube.com/@prodvelvet
SouthHarborMusic: https://www.youtube.com/@SouthHarborMusic
Miercoles: https://www.youtube.com/@prodmiercoles
Heydium : https://www.youtube.com/@heydium
DanDarmawan: https://www.youtube.com/@DanDarmawan
Chkody: https://www.youtube.com/@chkodybeats
AloneinTokyo: https://www.youtube.com/channel/UCnAKuzfWjjWQoGJS4ORJXag
Sugadaisy: https://www.youtube.com/channel/UC8yyVor4BCh4zXtAMdHY8oA
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


### UC1o9zvRwIqP_K5ByWs-EVwA_gA7ad8pcavQ_d603499e

- gold: {"st1": "physical_services", "st2": ["health"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "keeps comes in at about half the price of prescription medications at the pharmacy"}]}
- pred: {"st1": "physical_services", "st2": ["health"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st3": {"missing": [], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
like they seem so useless when i come up to a gate naturally hello everybody this video is indeed brought to you by keeps now i've seen a lot of you asking me a certain question which is anthony see that your hairline isn't necessarily uh improving how can you promote keeps you are a scammer and my answer to you is well have you noticed that my hairline has gotten any worse since i've started using keeps and the answer is no so suck on that you motherfu one of the key things with hair loss is prevention yes two out of three men will experience some sort of hair loss before the age of 35 but waiting until the hair loss has already started isn't necessarily the best way to go or you might end up looking like me prince vegeta with an afro if you notice your hair thinning or if you have any concerns whatsoever just give it a shot you never know sometimes your hair might just go like this in a couple of years and you start looking like this guy so that naturally leads to the next question what the heck is a keeps heaps is an online hair loss prevention service that prevents you from ever needing to leave your house ever again which if your hair is falling out i understand if you don't want to heaps is a 24 7 online service that pairs you up with a doctor that gives you a specific hair formula for your needs as well as removing the need to leave your home to see a doctor keeps also removes the need to leave your home to go get your medication that's right you never gotta leave again they ship it straight to your door on a nice monthly schedule to make sure that your good old shrubbery up top is taken care of in a timely manner and if all of that isn't enough keeps comes in at about half the price of prescription medications at the pharmacy so you're saving yourself some money as well as some embarrassment so if that all sounds good which it does go ahead and follow the link on your screen or go down to the description and click it it is heaps.com panda and you will save 50 off of your first order which is already 50 cheaper than the pharmacy medications you can do that math again that is keeps ke ps.com panda get you some savings bringing that hair back to life and let's get back to the video

VIDEO: I played Mario Party again with the boys and it was a nightmare
DESCRIPTION:
Head to https://keeps.com/panda to get 50% off your first order of Keeps hair loss treatment. Thanks to Keeps for sponsoring this video!

Well would you look at that, I made a gaming video! I know a lot of you have been asking so here yah go, almost an hour of Mario Party with fourzer0, nogla and wildcat! We totally all got along, didn't rage or argue and laughed the whole time! Yeah...something like that. 

Twitter -http://www.twitter.com/bigjigglypanda
Instagram - http://instagram.com/bigjiggly
Merch - https://shop.3blackdot.com/collections/big-jiggly-panda

Friends in the Video - Check Them Out!
@fourzer0seven @DaithiDeNogla @wildcat 

Outro Song - "Gigglebytes" by D1ofAquavibe
https://youtu.be/zyqmZgrZc9w
OFFICIAL_DISCLOSURE: true

PAGE (Take the Hair Loss Quiz | Keeps):
Internet Explorer is not supported. Please use a modern browser like Chrome, Firefox, or Edge to access this app.
Takes approximately 1 min
Answer a few questions to see if Keeps is right for you and we'll recommend a plan based on your results.
Clinically proven formula
Guidance from hair loss experts
Affordable treatment options
Prescription treatments require a medical consultation
Already know what you're looking for?
```
</details>


### UCtuLEGI-JkI6VFCW-5ZYtbw_xxZhHxBNn5Y_6912414b

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics", "other"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "The NextG upgraded hybrid mesh addressed seat provides 30% more breathability and reduces hip pressure by 20%."}]}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics", "other"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st3": {"missing": [], "extra": ["inadequate_disclosure"]}}

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

