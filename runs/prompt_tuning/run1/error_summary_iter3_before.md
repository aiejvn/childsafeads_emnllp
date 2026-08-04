# Error summary (9 instance(s) with at least one error)

## Per-tier error counts

- st1: 2/9
- st2: 3/9
- st3: 8/9

## st1 gold -> pred confusions

- none -> digital_content_or_services: 1x
- digital_content_or_services -> physical_services: 1x

## st2 missing labels (gold had it, prediction missed it)

- creator_community: missing 1x
- other: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- apps: extra 2x
- food: extra 1x
- fashion: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- creator_community -> apps: 1x
- creator_community -> food: 1x
- other -> apps: 1x

## st3 missing labels (gold had it, prediction missed it)

- no_flag: missing 2x
- inadequate_disclosure: missing 2x
- undisclosed_advertising: missing 1x
- insufficient_context: missing 1x
- direct_exhortation: missing 1x

## st3 extra labels (prediction hallucinated, not in gold)

- misleading_claim: extra 5x
- inadequate_disclosure: extra 2x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- no_flag -> misleading_claim: 2x
- undisclosed_advertising -> inadequate_disclosure: 1x
- insufficient_context -> inadequate_disclosure: 1x
- insufficient_context -> misleading_claim: 1x
- inadequate_disclosure -> misleading_claim: 1x

## Detailed error instances

### UCkxctb0jr8vwa4Do6c6su0Q_gg_NbE6_6p4_d7af87bb

- gold: {"st1": "none", "st2": ["creator_community"], "st3": ["undisclosed_advertising"], "st3_evidence": [{"flag": "undisclosed_advertising", "quote": "Get $5 off your first order of $15 or more when you download the DoorDash app and enter promo code AHLIVESTREAM."}]}
- pred: {"st1": "digital_content_or_services", "st2": ["food", "apps"], "st3": ["inadequate_disclosure"]}
- errors: {"st1": {"gold": "none", "pred": "digital_content_or_services"}, "st2": {"missing": ["creator_community"], "extra": ["apps", "food"]}, "st3": {"missing": ["undisclosed_advertising"], "extra": ["inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
we're gonna look for a Thomas Sackville he torments another ghost a young girl named Rosie he had something to say for yourself oh they like little girls in my house we're good hey what's up so hard

VIDEO: I Am NOT Saying THAT - Drawful 2
DESCRIPTION:
Get $5 off your first order of $15 or more when you download the DoorDash app and enter promo code AHLIVESTREAM.
Watch Haunter Season 2 here! ► http://bit.ly/HaunterS2
The gang are spreading their artistic wings in this Jackbox Drawful 2 gameplay.
More Jackbox ► https://www.youtube.com/playlist?list=PL1cXh4tWqmsHnR_uAGvziL8EDoPZ30Edd

Head to our site for early, uncensored content: http://bit.ly/AHSite

» Get your Let's Play merch: http://bit.ly/AHmerch
» Subscribe: http://bit.ly/SubToLP

About Let's Play:
Hello fellow Gamer. This you should watch me. I play game. Good. Thank you, thank you. If you watch me, I'm hot. Videos, they'll be better... The Let's Play view is the right thing to do YouTube, so do.

More from Let's Play:
» Achievement Hunter: http://bit.ly/AHYTChannel

https://www.youtube.com/user/letsplay

#Drawful2 #Jackbox
OFFICIAL_DISCLOSURE: false

PAGE (Rooster Teeth):
The funniest goddamn channel on the Internet, making you laugh since 2003. For more information, we’ve put together a handy guide...
There’s really no reason to visit any other website, given that we have everything you need here. But if you insist on going elsewhere you might as well follow us.
```
</details>


### UCg-e04O2EHuoIq2sLNJ9JoA_V1YLuawnI88_12b06d4d

- gold: {"st1": "physical_goods", "st2": ["food"], "st3": ["insufficient_context"], "st3_evidence": [{"flag": "insufficient_context", "quote": "[Music]"}]}
- pred: {"st1": "physical_goods", "st2": ["food", "fashion"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st2": {"missing": [], "extra": ["fashion"]}, "st3": {"missing": ["insufficient_context"], "extra": ["inadequate_disclosure", "misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
[Music]

VIDEO: YOU LAUGH YOU SPIN THE WHEEL (this was a mistake...)
DESCRIPTION:
BIGPUFFER X GAMERSUPPS SHAKER CUP + SHIRT - https://gamersupps.gg/Puffer
CODE PUFFER FOR 10% OFF - https://gamersupps.gg/Puffer
FREE SHIPPING FOR ORDERS OVER $39.69 - https://gamersupps.gg/Puffer

Other Channels:
Bigpuffer: https://www.youtube.com/c/Bigpuffer
Twitch: http://twitch.tv/bigpuffer
LittlePuffer (Clips Channel): https://bit.ly/2QXDyfo
HugePuffer (VOD Channel): https://www.youtube.com/@hugepufferbigpuffervods5620

MERCH MERCH MERCH
https://bigpuffer.3blackdot.com/

Socials:
Twitter: http://twitter.com/Bigpuffer
Instagram: http://instagram.com/Bigpufferr
Discord: https://discord.gg/QkFPbnc
Reddit: https://www.reddit.com/r/Bigpuffer/

Friends: 
no friends

Intro/Outro Song: https://www.youtube.com/watch?v=HClyQjRkJbU

#Bigpuffer #Reaction
OFFICIAL_DISCLOSURE: false

PAGE (BBL):
-
Afghanistan
(AFN ؋)
-
Åland Islands
(EUR €)
-
Albania
(ALL L)
-
Algeria
(DZD د.ج)
-
Andorra
(EUR €)
-
Angola
(USD $)
-
Anguilla
(XCD $)
-
Antigua & Barbuda
(XCD $)
-
Argentina
(USD $)
-
Aruba
(AWG ƒ)
-
Ascension Island
(SHP £)
-
Australia
(AUD $)
-
Austria
(EUR €)
-
Azerbaijan
(AZN ₼)
-
Bahamas
(BSD $)
-
Bahrain
(USD $)
-
Bangladesh
(BDT ৳)
-
Barbados
(BBD $)
-
Belgium
(EUR €)
-
Belize
(BZD $)
-
Benin
(XOF Fr)
-
Bermuda
(USD $)
-
Bhutan
(USD $)
-
Bolivia
(BOB Bs.)
-
Bosnia & Herzegovina
(BAM КМ)
-
Botswana
(BWP P)
-
Brazil
(BRL R$)
-
British Indian Ocean Territory
(USD $)
-
British Virgin Islands
(USD $)
-
Brunei
(BND $)
-
Bulgaria
(EUR €)
-
Burkina Faso
(XOF Fr)
-
Burundi
(BIF Fr)
-
Cambodia
(KHR ៛)
-
Cameroon
(XAF CFA)
-
Canada
(CAD $)
-
Cape Verde
(CVE $)
-
Caribbean Netherlands
(USD $)
-
Cayman Islands
(KYD $)
-
Central African Republic
(XAF CFA)
-
Chad
(XAF CFA)
-
Chile
(USD $)
-
China
(CNY ¥)
-
Christmas Island
(AUD $)
-
Cocos (Keeling) Islands
(AUD $)
-
Colombia
(USD $)
-
Congo - Brazzaville
(XAF CFA)
-
Congo - Kinshasa
(CDF Fr)
-
Costa Rica
(CRC ₡)
-
Côte d’Ivoire
(XOF Fr)
-
Croatia
(EUR €)
-
Curaçao
(ANG ƒ)
-
Cyprus
(EUR €)
-
Czechia
(CZK Kč)
-
Denmark
(DKK kr.)
-
Djibouti
(DJF Fdj)
-
Dominica
(XCD $)
-
Dominican Republic
(DOP $)
-
Ecuador
(USD $)
-
Egypt
(EGP ج.م)
-
El Salvador
(USD $)
-
Equatorial Guinea
(XAF CFA)
-
Eritrea
(USD $)
-
Estonia
(EUR €)
-
Eswatini
(USD $)
-
Ethiopia
(ETB Br)
-
Falkland Islands
(FKP £)
-
Faroe Islands
(DKK kr.)
-
Fiji
(FJD $)
-
Finland
(EUR €)
-
France
(EUR €)
-
French Guiana
(EUR €)
-
French Polynesia
(XPF Fr)
-
French Southern Territories
(EUR €)
-
Gabon
(XOF Fr)
-
Gambia
(GMD D)
-
Georgia
(USD $)
-
Germany
(EUR €)
-
Ghana
(USD $)
-
Gibraltar
(GBP £)
-
Greece
(EUR €)
-
Greenland
(DKK kr.)
-
Grenada
(XCD $)
-
Guadeloupe
(EUR €)
-
Guatemala
(GTQ Q)
-
Guernsey
(GBP £)
-
Guinea
(GNF Fr)
-
Guinea-Bissau
(XOF Fr)
-
Guyana
(GYD $)
-
Haiti
(USD $)
-
Honduras
(HNL L)
-
Hong Kong SAR
(HKD $)
-
Hungary
(HUF Ft)
-
Iceland
(ISK kr)
-
India
(INR ₹)
-
Indonesia
(IDR Rp)
-
Iraq
(USD $)
-
Ireland
(EUR €)
-
Isle of Man
(GBP £)
-
Italy
(EUR €)
-
Jamaica
(JMD $)
-
Japan
(JPY ¥)
-
Jersey
(USD $)
-
Jordan
(USD $)
-
Kazakhstan
(KZT ₸)
-
Kenya
(KES KSh)
-
Kiribati
(USD $)
-
Kosovo
(EUR €)
-
Kuwait
(USD $)
-
Kyrgyzstan
(KGS som)
-
Laos
(LAK ₭)
-
Latvia
(EUR €)
-
Lebanon
(LBP ل.ل)
-
Lesotho
(USD $)
-
Liberia
(USD $)
-
Libya
(USD $)
-
Liechtenstein
(CHF CHF)
-
Lithuania
(EUR €)
-
Luxembourg
(EUR €)
-
Macao SAR
(MOP P)
-
Madagascar
(USD $)
-
Malawi
(MWK MK)
-
Malaysia
(MYR RM)
-
Maldives
(MVR MVR)
-
Mali
(XOF Fr)
-
Malta
(EUR €)
-
Martinique
(EUR €)
-
Mauritania
(USD $)
-
Mauritius
(MUR ₨)
-
Mayotte
(EUR €)
-
Mexico
(MXN $)
-
Moldova
(MDL L)
-
Monaco
(EUR €)
-
Mongolia
(MNT ₮)
-
Montenegro
(EUR €)
-
Montserrat
(XCD $)
-
Morocco
(MAD د.م.)
-
Mozambique
(USD $)
-
Myanmar (Burma)
(MMK K)
-
Namibia
(USD $)
-
Nauru
(AUD $)
-
Nepal
(NPR Rs.)
-
Netherlands
(EUR €)
-
New Caledonia
(XPF Fr)
-
New Zealand
(NZD $)
-
Nicaragua
(NIO C$)
-
Niger
(XOF Fr)
-
Nigeria
(NGN ₦)
-
Niue
(NZD $)
-
Norfolk Island
(AUD $)
-
North Macedonia
(MKD ден)
-
Norway
(USD $)
-
Oman
(USD $)
-
Pakistan
(PKR ₨)
-
Palestinian Territories
(ILS ₪)
-
Panama
(USD $)
-
Papua New Guinea
(PGK K)
-
Paraguay
(PYG ₲)
-
Peru
(PEN S/)
-
Philippines
(PHP ₱)
-
Pitcairn Islands
(NZD $)
-
Poland
(PLN zł)
-
Portugal
(EUR €)
-
Qatar
(QAR ر.ق)
-
Réunion
(EUR €)
-
Romania
(RON Lei)
-
Rwanda
(RWF FRw)
-
Samoa
(WST T)
-
San Marino
(EUR €)
-
São Tomé & Príncipe
(STD Db)
-
Saudi Arabia
(SAR ر.س)
-
Senegal
(XOF Fr)
-
Serbia
(RSD РСД)
-
Seychelles
(USD $)
-
Sierra Leone
(SLL Le)
-
Singapore
(SGD $)
-
Sint Maarten
(ANG ƒ)
-
Slovakia
(EUR €)
-
Slovenia
(EUR €)
-
Solomon Islands
(SBD $)
-
Somalia
(USD $)
-
South Africa
(USD $)
-
South Georgia & South Sandwich Islands
(GBP £)
-
South Korea
(KRW ₩)
-
South Sudan
(USD $)
-
Spain
(EUR €)
-
Sri Lanka
(LKR ₨)
-
St. Barthélemy
(EUR €)
-
St. Helena
(SHP £)
-
St. Kitts & Nevis
(XCD $)
-
St. Lucia
(XCD $)
-
St. Martin
(EUR €)
-
St. Pierre & Miquelon
(EUR €)
-
St. Vincent & Grenadines
(XCD $)
-
Sudan
(USD $)
-
Suriname
(USD $)
-
Svalbard & Jan Mayen
(USD $)
-
Sweden
(SEK kr)
-
Switzerland
(CHF CHF)
-
Taiwan
(TWD $)
-
Tajikistan
(TJS ЅМ)
-
Tanzania
(TZS Sh)
-
Thailand
(THB ฿)
-
Timor-Leste
(USD $)
-
Togo
(XOF Fr)
-
Tokelau
(NZD $)
-
Tonga
(TOP T$)
-
Trinidad & Tobago
(TTD $)
-
Tristan da Cunha
(GBP £)
-
Tunisia
(USD $)
-
Turkmenistan
(USD $)
-
Turks & Caicos Islands
(USD $)
-
Tuvalu
(AUD $)
-
U.S. Outlying Islands
(USD $)
-
Uganda
(UGX USh)
-
United Kingdom
(GBP £)
-
United States
(USD $)
-
Uruguay
(UYU $U)
-
Uzbekistan
(UZS so'm)
-
Vanuatu
(VUV Vt)
-
Vatican City
(EUR €)
-
Venezuela
(USD $)
-
Vietnam
(VND ₫)
-
Wallis & Futuna
(XPF Fr)
-
Western Sahara
(MAD د.م.)
-
Yemen
(YER ﷼)
-
Zambia
(USD $)
-
Zimbabwe
(USD $)
```
</details>


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


### UCto7D1L-MiRoOziCXK9uT5Q_nNDtwhUPG18_6b646fee

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["no_flag"], "st3_evidence": []}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["no_flag"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
before but they added something new so buckle up we're gonna have us some fun oh and also this video is sponsored by afk arena hold on to your britches cause i'm gonna talk about it later but first let's go into how this game

VIDEO: I Became a Billionaire by Detonating All Wildlife in Hydroneer
DESCRIPTION:
Download AFK Arena for free! http://www.inflcr.co/SH5NW | Use gift code "8vws9uf6f5" before March 11 and get 30 Faction Scrolls and 3,000 Diamonds free!

JOIN MY STREAMS! ► https://www.twitch.tv/letsgameitout

Merch!  ►
  US/CA STORE ► http://bit.ly/LetsGameItOutUSStore
  EU STORE ► http://bit.ly/LetsGameItOutEUStore

Subscribe if you enjoy! ► http://bit.ly/letsgameitout_show

Twitter ► https://twitter.com/letsgameitout
Facebook ► https://www.facebook.com/letsgameitout

Want more LGIO?!

More Simulator Mayhem ► https://www.youtube.com/watch?v=UqaNKNgSxYI&list=PLrBjj4brdIRzn3ja4BfqYUForg0p-p5wi

Funny Tycoon Games ► https://www.youtube.com/watch?v=UqaNKNgSxYI&list=PLrBjj4brdIRwf14QPGmfDXCQQrDs860ig

The Finest One-Offs ► https://www.youtube.com/watch?v=zIOFGCbwJSs&list=PLrBjj4brdIRwKf72d6spk7fSHhwwYuQu1

Some Truly Bizarre Games  ► https://www.youtube.com/watch?v=zIOFGCbwJSs&list=PLrBjj4brdIRyM5mUsHwPN0PH6UVNfeNl2

#LetsGameItOut #AFKArena #sponsored

I Became a Billionaire by Detonating All Wildlife in Hydroneer - Let's Game It Out

----------

Check it out on Steam ► https://store.steampowered.com/app/1106840/Hydroneer/

More about Hydroneer (from Steam):

Hydroneer is a mining sandbox game where you dig for gold and other resources to build massive mining machines and a base of operation. Use primitive tools, hydro-powered machines, and player-built structures to dig and evolve your operation in this tycoon-style progression system.

Using a state-of-the-art voxel based terrain system, you can create cave networks, quarry pits, or even mud mountains. Discover relics of the past in the depths of Hydroneer, with better rewards the deeper you dig.

Hydroneer features a dynamic modular system for building structures and hydro powered machinery. Create the base of operations from your own design to optimise your work. Create networks of hydro pipes, control pressure. Craft resources, weaponry, and jewellery.

Rigs are large hydro powered machines used for a variety of uses, from digging resources to transporting goods.

Various parcels of land await you in the world of Hydroneer, each with their own advantages. Deeper pits, attractive scenery, and closer stores. You decide where to build your base of operations.

Multiplayer too! At some point.
OFFICIAL_DISCLOSURE: true

PAGE (Hydroneer on Steam):
Install Steam
sign in
|
language
简体中文 (Simplified Chinese)
繁體中文 (Traditional Chinese)
日本語 (Japanese)
한국어 (Korean)
ไทย (Thai)
Bahasa Indonesia (Indonesian)
Bahasa Melayu (Malay) BETA
Български (Bulgarian)
Čeština (Czech)
Dansk (Danish)
Deutsch (German)
Español - España (Spanish - Spain)
Español - Latinoamérica (Spanish - Latin America)
Ελληνικά (Greek)
Français (French)
Italiano (Italian)
Magyar (Hungarian)
Nederlands (Dutch)
Norsk (Norwegian)
Polski (Polish)
Português (Portuguese - Portugal)
Português - Brasil (Portuguese - Brazil)
Română (Romanian)
Русский (Russian)
Suomi (Finnish)
Svenska (Swedish)
Türkçe (Turkish)
Tiếng Việt (Vietnamese)
Українська (Ukrainian)
Report a translation problem
```
</details>


### UCrPseYLGpNygVi34QpGNqpA_6EC-6MQMu2s_4115fe17

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["inadequate_disclosure"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "Play Apex Legends new Mixtape Mode Today! #ApexLegendsPartner"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["inadequate_disclosure"], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
scammed out of one hundred thousand dollars by moist critical how what actually starts with a sponsor of this video Apex Legends if you don't know it's a battle royale with good movement that usually has a pretty high skill ceiling but they added three new game modes so that anybody can have fun with the game and they asked me to show it off I think because they think I'm bad at the game and they're right the idea was pretty simple I would show it off by

VIDEO: This YouTuber Scammed Me Out Of $100,000
DESCRIPTION:
Play Apex Legends new Mixtape Mode Today! #ApexLegendsPartner
Link: https://www.inflcr.co/SHHLo

follow me on twitter ► https://www.twitter.com/ludwigahgren
follow me on tiktok ► https://www.tiktok.com/@ludwig
follow me on instagram ► https://www.instagram.com/ludwigahgren
join my subreddit ► https://old.reddit.com/r/LudwigAhgren/
join my discord ► https://discord.gg/ludwig
LINK TO EVERYTHING ► https://wlo.link/@ludwig


edited by: https://twitter.com/politesl

#ludwig #moistcr1tikal #apexlegends #ad
OFFICIAL_DISCLOSURE: true

PAGE (Important Update: Streamlabs Link Space Is Being Discontinued):
TL:DR Streamlabs Link Space will be discontinued on November 8, 2025. The tool will remain accessible for 30 days, giving you time to back up your links and transition to another service. This decision enables us to focus on developing and enhancing features that better support creators.
Support for Link Space Is Ending
We’ve made the difficult decision to discontinue Streamlabs Link Space so we can focus on building new tools and improving existing features that better serve creators’ needs. While the tool has been a helpful companion for many, we’re realigning our efforts toward tools that directly enhance live streaming and audience engagement.
Link Space will remain available for the next 30 days, giving you time to export your data and transition to another bio link service. After November 8, you’ll no longer be able to access your Link Space dashboard or pages. We recommend saving your links (listed on your Link Space profile) and any useful analytics before that date.
What’s Next
Creators looking to keep a central link hub can explore other bio link services. You can also add your social links to your Streamlabs Tip Page and utilize it as your primary destination to drive support and engagement from your audience.
If you have any questions, please don’t hesitate to reach out to our support team.
We sincerely appreciate everyone who has used Link Space as part of their creator toolkit. Your continuous support helps us evolve and deliver the best tools for streamers everywhere.
```
</details>


### UCjxBwyx2ejyMkzgBexAxfBw_LZ0n7GASMfM_c842f21f

- gold: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["direct_exhortation"], "st3_evidence": [{"flag": "direct_exhortation", "quote": "do it for them play a attorney investigations now"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["apps"], "st3": ["direct_exhortation", "misleading_claim"]}
- errors: {"st3": {"missing": [], "extra": ["misleading_claim"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
happening dollia Hawthorne Phoenix W's girlfriend oh damn Phoenix get it okay hold it you know what else you should get miles I mean Ace atorney investigations which is out today across all modern platforms this collection includes the two Ace Attorney investigations games where you could play as miles edworth himself the second game Prosecutor's Gambit has never been officially released in the west until today it also features all new full HD graphics but you'll be happy to note that there is an option available in the game to switch to the old Sprites should you prefer there are a lot of quality of life improvements and special bonus materials that come out with the collection as well this includes a story mode to help investigations go smoothly chapter select if you have played the first investigations game already and you just want to skip ahead a history to let you reread any lines that you may have skipped and illustration Gallery OST player animation viewer and many more if you're on the fence you can also play the demo now and your save will carry over if you end up buying the game in the end and when you end up buying the game because this is Peak fiction you can learn more about the Ace Attorney investigations collection in the link below to support the channel and thank you Capcom miles Edward for sponsoring this video an absolute dream sponsorship do it for them play a attorney investigations now let's get back to Mr teenage Phoenix Wright what an icon

VIDEO: Teenager Phoenix IS A MESS.  Ft. @NicoB ~ #7
DESCRIPTION:
GO CHECK OUT ACE ATTORNEY INVESTIGATIONS! Use my link here to support the channel ➤  https://bit.ly/3yW9Uxj   every click helps! Thank you so much Capcom for sponsoring this video!! Truly a dream sponsorship come true D,,,x

Shoutout to @NicoB for also coming on for this Ace Attorney episode!! Hope you guys enjoy it!

Ace Attorney Highlight Playlist can be found here ➤ https://www.youtube.com/playlist?list=PLNIjvzIQAk38pw-gN6envO7owKPc1TDT_

Full Unedited Playthrough here ➤ https://youtube.com/playlist?list=PLaTOxuJjSjGTZikhhfCmYX-dIf7tEwTyF&si=UXqrQiQ9aFWOLoFM

Video Edited by AllanRayy ➤ https://twitter.com/AllanRayy?t=Whcg55PNJ_7LKJ0N3TD5kg&s=09



~~Follow me on my socials! ~~
➤ Secondary YT VOD Channel: 
 https://www.youtube.com/channel/UC3CDvYelm0WcPXl2HNZUiVA
➤ Twitch:  https://www.twitch.tv/crystaahhl
➤ Instagram:  https://www.instagram.com/ocrystaahhl/
➤ Twitter:  https://twitter.com/CrystAAHHl
➤ Patreon:  https://www.patreon.com/crystaahhl
➤ Website:  https://crystaahhl.com/
➤ Tiktok: https://www.tiktok.com/@crystaahhl
➤ Discord: https://discord.gg/crystaahhl
➤ Join our subreddit!: https://www.reddit.com/r/Crystaahhl
OFFICIAL_DISCLOSURE: false

PAGE (Ace Attorney Investigations Collection｜CAPCOM):
Ace prosecutor Miles Edgeworth
makes his triumphant return!
Two Ace Attorney Investigations titles are coming to modern consoles in one complete collection!
There are no objections to the investigations of ace prosecutor Miles Edgeworth making their triumphant return!
Featuring full HD graphics along with quality of life improvements and special bonus materials, this two-game collection is the definitive experience!
Meet the stars of each game!
In-Game Music (Arranged) -
5 Tracks Set
Get 5 arranged in-game tracks for Ace Attorney Investigations 2: Prosecutor's Gambit!
Use them in-game or listen to them in the Gallery!
Tracks List
For Digital Version Purchases:
For Physical Version Purchases:
Digital Version
Physical Version
Play the beginning of each game's first episode!
You can transfer your save data to the full game.
Become Miles Edgeworth and get a taste of two ace investigations!
| OS | Windows® 10 (64-bit required) | Windows® 10 (64-bit required) / Windows® 11 (64-bit required) |
| Processor | Intel® Core™ Core i3 8350k AMD Ryzen3 3200G |
Intel® Core™ i3-9100F AMD Ryzen3 3200G |
| AMD Ryzen3 3200G | AMD Ryzen3 3200G | |
| Memory | 8 GB RAM | 8 GB RAM |
| Graphics Card | Intel® UHD Graphics 630 Radeon™ Vega 8 Graphics |
NVIDIA® GeForce® GT 1030 (VRAM2GB) AMD Radeon™ RX550(VRAM2GB) |
| Radeon™ Vega 8 Graphics | AMD Radeon™ RX550(VRAM2GB) | |
| DirectX | Version 12 | |
| Hard Drive Space | 10GB | |
| Additional Notes | *Monitor refresh rate needs to be set at 60Hz or higher. |
```
</details>


### UCzlXf-yUIaOpOjEjPrOO9TA_-f6fHLiymQo_23d56510

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "I've teamed up with the lovely folks over at castify who are very kindly sponsoring this video"}, {"flag": "misleading_claim", "quote": "dissipating up to 95% of the impact"}]}
- pred: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["inadequate_disclosure"], "extra": []}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
than it was at launch with last year's 14 series But whichever phone you pick make sure you keep it safe and so I've teamed up with the lovely folks over at castify who are very kindly sponsoring this video to show you just how safe these cases are and in fact they sent me this nice big block of their ecoshock material and they use it in their protective cases and just look at how it absorbs the shock of this metal ball landing on it compared to some competing material at the molecular level this plant-based ecoshock material turns the kinetic energy of dropping a phone into heat while its twister pattern dissipates the energy across the surface of the case dissipating up to 95% of the impact you could drop your shyy new iPhone 15 Pro Max in an ultra bounce case with a screen protector of course from over 32 ft and it should be fine now I have a selection of the latest bounce Ultra pounce impact and impact ring stand cases all of which have been refreshed for the iPhone 15s and of course the latest Samsung and Google devices so they're tough they look good with tons of customization options and then check this bad boy out this is casy's impact ring stand case this little guy just folds out from the back of the camera module here and you can use it like you have a popsocket it still gives you over 6 ft of drug protection it's made from 65% recycled and plant-based materials and then you can watch your movies or do whatever you like without having to hold your phone so keep your phone safe and click my link in the description below to get 10% off your next casify order and experience the protective power of ecoshock in terms of battery over the

VIDEO: iPhone 15 Pro Max - 2 MONTHS Later... was it worth it?
DESCRIPTION:
2 MONTHS with the iPhone 15 Pro Max - was it worth the upgrade?  ▶ Go to https://www.casetify.com/thetechchap for 10% off your CASETiFY order - and keep your new iPhone 15 protected!

Can't get enough of your TECH? Why not SUBSCRIBE? (it's free!) 😄
▶ YouTube: https://bit.ly/2UyCBGq 
📷 Instagram: https://www.instagram.com/TheTechChap
🐦Twitter: https://twitter.com/TheTechChap
🎵 Music by Epidemic & Artlist

#iPhone #iPhone15ProMax #Phones
OFFICIAL_DISCLOSURE: false

PAGE (The Tech Chap's iPhone 15 Favourites):
Manage Cookies
You can manage your preferences below.
Preference
These cookies are essential for this site to work properly, and are used for things such as navigation, saving your preferences, and allowing images to load.
Functional cookies are used to enable specific site features as well as a number of options (e.g. preferred language, products selected for purchase) in order to improve the service provided. By disabling this type of cookie, certain services or functions of our site may not be available or may not function properly, and you may be forced to modify or manually enter certain information or preferences each time you visit our site.
Targeting (or "Advertising") cookies, including those from third parties, are cookies aimed at creating user profiles and are used to display advertisements based on your preferences when browsing the web.
```
</details>


### UC8JOgFXp-I3YV6dsKqqQdUw_Ij8zjnO5zfY_8b447c43

- gold: {"st1": "physical_goods", "st2": ["fashion"], "st3": ["direct_exhortation", "misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "who makes the most comfortable bombas socks in the history of feet it's bombas as well as underwear t-shirt slippers"}, {"flag": "direct_exhortation", "quote": "it's time that you tried bombas plus new customers get 20% off their first purchase just go to bombas.com Caroline and use code caroline2 at checkout"}]}
- pred: {"st1": "physical_goods", "st2": ["fashion"], "st3": ["misleading_claim"]}
- errors: {"st3": {"missing": ["direct_exhortation"], "extra": []}}

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


### UCB_qr75-ydFVKSF9Dmo6izg_WQtdQb-m4Sk_67f0ddda

- gold: {"st1": "digital_content_or_services", "st2": ["other"], "st3": ["inadequate_disclosure", "misleading_claim"], "st3_evidence": [{"flag": "inadequate_disclosure", "quote": "This episode is brought to you by T-Mobile, official 5G partner of F1 Las Vegas Grand Prix."}, {"flag": "misleading_claim", "quote": "this holiday get four lines for 25 bucks a line plus four iPhone 16s with apple intelligence and the allnew camera control on us"}]}
- pred: {"st1": "physical_services", "st2": ["other"], "st3": ["inadequate_disclosure", "misleading_claim"]}
- errors: {"st1": {"gold": "digital_content_or_services", "pred": "physical_services"}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
then yeah next year is next year GP very well done thank you thank you very much this holiday at T-Mobile I'm joined by a special co-anchor what up everybody it's your boy big Snoop deal double je Snoop let's talk about T-Mobile okay cool this holiday get four lines for 25 bucks a line plus four iPhone 16s with apple intelligence and the allnew camera control on us let's get cracking like a breakfast egg you can use those eggs eggs to make some eggnog Snoop respect and people do love T-Mobile where you can save on every plan versus the other big guys you know y'all can take some of those savings and buy some Snoop merchandise always a great stocking stuffer Snoop we up out of here hold your horses Snoop Dog let's remind people one more time head to t-mobile.com and get four iPhone 16s with apple Intelligence on us plus four lines for 25 bucks now drop that J with 24 monthly bill credits four eligible tradein and four new lines with auto pay well qualified customers plus taxes and fees and $35 per connection charge cancel entire account before receiving 24 Bill credits and credit stop and balance on required Finance agreements du $29.99 credits Envy payoff device early see how you can save on wireless and streaming versus the other big guys at t-mobile.com switch Apple intelligence available

VIDEO: Verstappen Makes It Four | 2024 Las Vegas GP Review With Gianpiero Lambiase | F1 Nation Podcast
DESCRIPTION:
This episode is brought to you by T-Mobile, official 5G partner of F1 Las Vegas Grand Prix.

Tom Clarkson is joined in the paddock by F1 correspondent and presenter Lawrence Barretto to celebrate Max Verstappen becoming a four-time World Champion at the Las Vegas Grand Prix

Was this Verstappen’s best title? How does he compare to other sporting greats? And what can he still go on to achieve in Formula 1? His race engineer Gianpiero Lambiase tells the guys why this championship was more ‘emotional’ than he expected, while Red Bull Team Principal Christian Horner explains how Max has made the difference this season.

Tom and Lawrence also discuss what Lando Norris will have learnt from his title fight with Verstappen and what we can expect from their battles in 2025.

Plus, was George Russell’s phenomenal victory in Vegas a ‘statement’ to Toto Wolff? And were Ferrari’s mistakes a first real ‘test’ of Fred Vasseur’s new culture at the team?

Chapters

06:10 – Why GP was ‘emotional’
12:53 – Where Horner thinks Max made the difference
23:24 – Why Verstappen is the ‘ultimate racing driver’
35:07 – Russell’s message to Toto?
43:23 – First test of Ferrari’s new culture?
56:34 – Driver of the Day

For more F1® videos, visit https://www.Formula1.com

Follow F1®:
https://www.instagram.com/F1
https://www.facebook.com/Formula1/
https://www.twitter.com/F1
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

