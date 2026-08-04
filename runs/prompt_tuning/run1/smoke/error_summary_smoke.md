# Error summary (2 instance(s) with at least one error)

## Per-tier error counts

- st1: 0/2
- st2: 1/2
- st3: 2/2

## st2 missing labels (gold had it, prediction missed it)

- hardware_electronics: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- health: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- hardware_electronics -> health: 1x

## st3 missing labels (gold had it, prediction missed it)

- misleading_claim: missing 2x

## st3 extra labels (prediction hallucinated, not in gold)

- no_flag: extra 1x
- direct_exhortation: extra 1x
- inadequate_disclosure: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- misleading_claim -> no_flag: 1x
- misleading_claim -> direct_exhortation: 1x
- misleading_claim -> inadequate_disclosure: 1x

## Detailed error instances

### UCrEUTzd1W__Y5Sb5vSbuZ5g_qbZ_TygubJM_89b608ac

- gold: {"st1": "physical_goods", "st2": ["hardware_electronics"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "it has a titanium coated stainless steel blade which will effortlessly glide through even the thickest beard providing a clean quick and precise cut every single time"}, {"flag": "misleading_claim", "quote": "meaning that this thing will knock down even long stubble and leave you with an incredibly clean shave in like less than 60 seconds"}]}
- pred: {"st1": "physical_goods", "st2": ["health"], "st3": ["inadequate_disclosure", "direct_exhortation"]}
- errors: {"st2": {"missing": ["hardware_electronics"], "extra": ["health"]}, "st3": {"missing": ["misleading_claim"], "extra": ["direct_exhortation", "inadequate_disclosure"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
though but wait before we give Greg a ride in the sleeper Volvo I need to take a moment to think this video's sponsor fanss scaped now you've probably heard about their lawn mower but did you know that they make products for face grooming as well right here I have the beard hedger and their handyman now firstly the beard hedger I wish I could use it in its full potential but unlucky for me I got blessed with bad hair jeans and bad beard jeans so I can't really grow either of those things but I can still talk to you about it there's a couple things that make the beard hedger so awesome for one it has a titanium coated stainless steel blade which will effortlessly glide through even the thickest beard providing a clean quick and precise cut every single time now tying into that this thing has an adjustable cut length it's got 20 different length settings from .5 mm all the way up to 10 mm in addition to that this thing's got a 60-minute run time a 3le led charge indicator and it's waterproof so you can use it in the shower and of course this thing comes with everything you could ever need a charger the length setting comb and a travel bag now the handyman this thing I love in this thing I can use now what sets this thing apart is that it's got a dual blade it's got a standard foil shaver as well as a long hair leveler blade meaning that this thing will knock down even long stubble and leave you with an incredibly clean shave in like less than 60 seconds the other awesome thing is that it's got skin safe technology to help reduce Nicks and cuts and it is also waterproof and I mean just look at this thing it's so Compact and ergonomic and this also has a 60-minute run time which makes this the perfect travel comparion so what are you guys waiting for upgrade your facial grooming routine today by visiting manscape.com and use code gingium to get 20% off your first purchase of the beard hedger and the handyman huge thank you to manscape for sponsoring this video I'll also have links in the description and up there in the card but anyway what does Greg think about the Sleep Volvo this your first turbo car You' ever done

VIDEO: 900HP Rust Box Challenges A 10 Second MIATA
DESCRIPTION:
Get 20% OFF + Free international shipping @manscaped with promo code GINGIUM at http://manscaped.com/gingium! #teammanscaped Today we meet up with @TheCarPassionChannel and ride in his crazy 520HP NA Miata! After that we do a roll race against the Sleeper Volvo. Which is faster? A 900HP Volvo or a 520HP Miata?

Check out Greg's video ► https://youtu.be/aLTiZ2zoTpI?si=1C_5U5Fc75OguRJm

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
OFFICIAL_DISCLOSURE: false

PAGE (Amazon.com : Panasonic LUMIX GH5M2, 20.3MP Mirrorless Micro Four Thirds Camera with Live Streaming, 4K 4:2:2 10-Bit Video, Unlimited Video Recording, 5-Axis Image Stabilizer DC-GH5M2 Black : Electronics):
Learn more
No featured offers available
We feature offers with an Add to Cart button when an offer meets our high standards for:
- Quality Price,
- Reliable delivery option, and
- Seller who offers good customer service
Panasonic LUMIX GH5M2, 20.3MP Mirrorless Micro Four Thirds Camera with Live Streaming, 4K 4:2:2 10-Bit Video, Unlimited Video Recording, 5-Axis Image Stabilizer DC-GH5M2 Black
| Compatible Mountings | Micro Four Thirds |
| Aspect Ratio | 1.50:1, 16:9, 4:3 |
| Photo Sensor Technology | MOS |
| Supported File Format | JPEG, Raw |
| Image Stabilization | Sensor-shift |
| Maximum Focal Length | 120 Millimeters |
| Optical Zoom | 5 x |
| Maximum Aperture | 2.8 f |
| Expanded ISO Minimum | 100 |
| Metering Description | Center-Weighted Average, Highlight Weighted, Multiple, Spot |
About this item
- THE ICONIC GH5, NOW WITH LIVE STREAMING: Attention hybrid content creators—the GH5M2 supports both wired and wireless unlimited live streaming for indoors and outdoors, together with a USB Power Delivery feature.
- VIDEO FORMAT OPTIONS FOR PROFESSIONAL USE: The GH5M2 is capable of unlimited video recording in various settings including C4K/4K 60p 4:2:0 10-bit and simultaneous output over HDMI during 4K 60p internal recording.
- PHOTO STYLE PRESETS MINIMIZE YOUR EDITING: Presets include V-LogL, Cinelike D2/ V2, MonochromeS and L.ClassicNeo.
- POWERFUL IMAGE STABILIZATION: Advanced I.S. to 6.5-stop slower shutter speeds for stable handheld shooting. Double SD Memory Card slot for relay recording.
- WITHSTANDS HEAVY FIELD USE: The magnesium alloy full die-cast front / rear frame and is not only splash and dust resistant, but also freezeproof down to -10 °C (14°F).
Customers who viewed this item also viewed
Product Description
The legendary LUMIX GH5 experience, now with livestreaming! The LUMIX GH5M2 draws from the GH5, an iconic camera for pro photography and videography, adding features to challenge you to your highest levels of creativity. The GH5 II is capable of wireless live streaming using the LUMIX Sync smartphone app supported by USB PD outdoors or indoors. With a future firmware update, it will support wired IP streaming. Video can be delivered either as-is, or as log recording for advanced post-production. The GH5II ensures successful shooting with a 20.3MP sensor with AR coating, the latest autofocus, and I.S. technologies with the latest Venus Engine. It is capable of unlimited video recording in various settings and can record C4K/4K 60p 4:2:0 10-bit without cropping, with simultaneous output over HDMI during internal recording. V-LogL is pre-installed to deliver a high dynamic range and broad colors, which makes you easy to match the color tone with the footage recorded in V-Log and V-LogL of Panasonic and LUMIX line-up. Cinelike D2 and V2, MonochromeS, and L.ClassicNeo have been added to Photo Style to expand your creativity. For Variable Frame Rate recording, C4K/4K 60fps, Anamorphic 50fps and FHD180fps are available with autofocus function prior to the recording starts.Tough enough to withstand even heavy field use, the GH5M2 has a magnesium alloy full die-cast front/rear frame. Secure construction and a sealing for every joint, dial, and button make it not only splash and dust resistant** but also freezeproof down to -10 degrees Celsius (14° F). Equipped with a double SD Memory Card slot compatible with high-speed, high capacity UHS-II for Relay Recording, Backup Recording, or Allocation Recording. *Based on the CIPA standard [Yaw/Pitch direction: focusing distance f=60mm (35mm camera equivalent f=120mm) when H-ES12060 is used.
From the manufacturer
LUMIX DC-GH5M2
Free Your Creativity. Go Live.
Hybrid mirrorless camera featuring live streaming capability and C4K 60p/50p 10bit video recording.
Cinema, Broadcasting, and Other Pro Applications
Unlimited recording on all settings—C4K and 6K anamorphic mode, 60p/50p 4:2:0 10-bit and C4K/4K 30p/25p/24p 4:2:2 10-bit ALL-Intra 400Mbps recording
Advanced Functions to Support All Your Needs
Pre-installed V-LogL, REC Frame Indicator, Luminance Spot Meter, Zebra Pattern, WFM/Vectorscope, and three display options for Shutter Speed and Gain (Sensitivity): Sec/ISO, Angle/ISO, or Sec/dB.
6.5-stop Dual I.S. 2 (Image Stabilizer)
Combines control of the Body I.S. and Lens O.I.S. to offer 6.5 stops’ worth of correction.*
*Based on the CIPA standard [Yaw/Pitch direction: focusing distance f=60mm (35mm camera equivalent f=120mm) when H-ES12060 is used.
Fully Weather Sealed
Durable magnesium alloy die-cast frame sealed to protect every seam, dial, and button. Dust and splash resistant*; use at temperatures as low as -10°C / 14°F.
*Dust and splash resistant does not ensure that damage will not occur if this camera is subjected to direct contact with dust and water.
Product information
| Compatible Mountings | Micro Four Thirds |
|---|---|
| Aspect Ratio | 1.50:1, 16:9, 4:3 |
| Sensor Type | MOS |
| File Format | JPEG, Raw |
| Image stabilization | Sensor-shift |
| Maximum Aperture | 2.8 f |
| Expanded ISO Minimum | 100 |
| Photo Sensor Resolution | 20.3 MP |
| Photo Sensor Size | Micro Four Thirds |
| Maximum Shutter Speed | 1/16000 Seconds |
| Minimum Shutter Speed | 60 Seconds |
| Exposure Control | Aperture Priority, Auto, Manual, Program, Shutter Priority |
| Form Factor | Mirrorless |
| Effective Still Resolution | 16 |
| Special Feature | Live View |
| Color | Black |
| Screen Size | 3 Inches |
| Shooting Modes | Bulb Mode,Aperture Priority, Auto, Manual, Program, Shutter Priority |
| Item Weight | 1.6 Pounds |
| Video Resolution | 2160p |
| Viewfinder | Electronic |
| Flash Modes | Auto, Auto/Red-Eye Reduction, Forced On, Forced On/Red-Eye Reduction, Off, Slow Sync, Slow Sync/Red-Eye Reduction |
| Camera Flash | Hotshoe |
| Skill Level | Professional |
| Specific Uses For Product | Micro Four Thirds |
| Compatible Devices | Micro Four Thirds |
| Continuous Shooting | 12 FPS |
| Aperture modes | F2.8-F4.0 |
| Viewfinder Magnification | 0.76x |
| Flash Sync Speed | 1/250 sec |
| Connectivity Technology | Wi-Fi |
|---|---|
| Wireless Technology | Bluetooth, Wi-Fi |
| Video Output | HDMI |
| Total USB 3.0 Ports | 1 |
| Total USB Ports | 1 |
| Total Video Out Ports | 1 |
| Total USB 2.0 Ports | 1 |
| Hardware Interface | USB |
| Screen Size | 3 Inches |
|---|---|
| Display Type | LCD |
| Dots Per Screen | 1,840,000 Dot |
| Display Fixture Type | Tilting |
| Display Maximum Resolution | 3,680,000 dots |
| Has Color Screen | Yes |
| Display Resolution Maximum | 3680000 dots_per_inch |
| Touch Screen Type | Capacitive |
| Flash Memory Type | Dual Slot: SD/SDHC/SDXC (UHS-II) [V90 or Faster Recommended] |
|---|---|
| Write Speed | ≥300 MB/s |
| Flash Memory Speed Class | UHS-II |
| Flash Memory UHS Speed Class | UHS-II |
| Compatible Flash Memory Type | SD |
Warranty & Support
Feedback
| Aspect Ratio | 1.50:1, 16:9, 4:3 |
|---|---|
| File Format | JPEG, Raw |
| Effective Still Resolution | 16 |
| JPEG Quality Level | Fine |
| Supported Image Format | JPEG, Raw |
| Bit Depth | 14 Bit |
| Total Still Resolution | 20.3 MP |
| Maximum Image Size | 20.3 MP |
| Maximum Focal Length | 120 Millimeters |
|---|---|
| Optical Zoom | 5 x |
| Lens Type | Wide Angle |
| Zoom | Optical Zoom |
| Camera Lens | 12-60mm f/2.8-4 ASPH. POWER O.I.S. Lens |
| Minimum Focal Length | 12 Millimeters |
| Real Angle Of View | 10.5 Degrees |
| Focal Length Description | 12-60 millimeters |
| Digital Zoom | 4 x |
| Lens Construction | 10 elements in 9 groups |
| Lens Correction Type | Micro Four Thirds |
| Metering Methods | Center-Weighted Average, Highlight Weighted, Multiple, Spot |
|---|---|
| Exposure Control | Aperture Priority, Auto, Manual, Program, Shutter Priority |
| White Balance Settings | Auto, Cloudy, Daylight, Flash torch, Shade |
| Self Timer | 10 Seconds, 2 Seconds |
| Brand | Panasonic |
|---|---|
| Model Name | Panasonic LUMIX GH5M2, Mirrorless Camera with Live Streaming |
| Built-In Media | Camera Body Only |
| A
```
</details>


### UC7-hR5EfgpM6oHfiGDkxfMA_r8vJy5W3yqY_4a68818a

- gold: {"st1": "digital_content_or_services", "st2": ["education"], "st3": ["misleading_claim"], "st3_evidence": [{"flag": "misleading_claim", "quote": "right now for a limited time save 46 off your first four months of audible that's only 7.95 a month"}]}
- pred: {"st1": "digital_content_or_services", "st2": ["education"], "st3": ["no_flag"]}
- errors: {"st3": {"missing": ["misleading_claim"], "extra": ["no_flag"]}}

<details><summary>full instance text</summary>

```
TRANSCRIPT:
want that i didn't mention let us know in the comments below and remember right now for a limited time save 46 off your first four months of audible that's only 7.95 a month give yourself the gift of listening for more go to audible.com tolariancommunity or textilariancommunity to 500-500 thanks again to audible for sponsoring this video

VIDEO: Don't Buy Innistrad! Buy These 5 Crimson Vow Cards For Commander Instead | Magic: The Gathering
DESCRIPTION:
Go to http://www.audible.com/tolariancommunity or text tolariancommunity to 500 500 to get your free trial and for a limited time, save 46% on your first 4 months of Audible!

Mistakes Magic The Gathering Players Make: https://youtu.be/Y8RfvgZDdTY

Magic Made Easy: https://youtu.be/g20FKjlQ1B0

What Guild Are You? Take The Ravnica Guild Test - https://youtu.be/PGe7mGtoabc

Magic The Gathering Is Ruined Forever - https://youtu.be/fqow0TfaT44

What MTG Color Are You? - https://youtu.be/Ez_8yLQOSSw

Liliana Reacts! Not on Modern Masters box? https://youtu.be/LWOSqsImos8

TCC Shirts! Playmats! - http://www.tolariancommunitycollege.com/

Tolarian Community College is brought to you by Card Kingdom! You can support The Professor just by checking out their store through this link: http://www.cardkingdom.com/TCC

Want to play with your Magic cards but stuck at home? No problem! Play with your friends using your paper cards, and 100% for free! Check out my guide to Magic: The Gathering Via Webcam, including where and how to find people to play with, here: https://youtu.be/CFwRZwqoy3A

Support The Professor - Patreon -https://www.patreon.com/tolariancommunitycollege

TCC Shirts! Playmats! - http://www.tolariancommunitycollege.com/

#magicthegathering #mtg #commander

MUSIC COURTESY OF:
"Vintage Education" Kevin MacLeod (incompetech.com) 
Licensed under Creative Commons: By Attribution 3.0
http://creativecommons.org/licenses/by/3.0/
OFFICIAL_DISCLOSURE: true

PAGE (Audible):
Wij hebben waar iedereen naar luistert
Bestsellers. Nieuwe releases. Dat ene verhaal waar je op hebt gewacht.Ontdek nieuwe werelden
Van epische verhalen tot persoonlijke ontwikkeling, er zijn audioboeken voor elke smaak.Misdaad en thriller
Literatuur en fictie
Politiek
Kids
Romans
Komedie en humor
Sciencefiction
Biografieën en memoires
Alleen op Audible
Spannende Audible Originals en exclusieve verhalen van de grootste sterren en nieuw talent.Wil je meer keuzes?
Vind het juiste abonnement voor jou.Hou je van audioboeken? Dan zul je Audible geweldig vinden.
Maak je dag anders en beter
Ruil eindeloos scrollen in voor eindeloos luisteren. Huishoudelijk werk kan leuk zijn.
Luister overal
Van dagelijks woon-werkverkeer tot fantastische roadtrips. Geniet van het beste audio-entertainment.
Neem gewoon je hele bibliotheek mee
Je favoriete verhalen zijn altijd bij je. Audioboeken wegen niets.
Luister en leer
Ontdek verhalen die goed zijn voor je geest, je welzijn en je leven.
Bereik je leesdoelen
Download gewoon titels en luister offline, waar je ook bent.
Vind je interesses
Tussen duizenden titels is er voor iedereen een perfecte luisterervaring.
Eén app, speciaal ontworpen voor jouw luisterbehoeften
Vind de juiste snelheid
Gebruik de bedieningsknoppen van de speler om het verhaal te vertragen of het tempo te versnellen.
Een timer instellen
Perfect om te ontspannen of te multitasken. De timer stopt je verhaal voor je.
Luisteren in de automodus
Luister onderweg met grotere, eenvoudigere bedieningsknoppen en een scherm dat nooit in slaapstand gaat.
Luister altijd en overal
Download titels en geniet ook offline bent, waar je ook bent.
Veelgestelde vragen
Hoe werkt het proefabonnement?
Alle in aanmerking komende leden kunnen zich aanmelden voor een proefabonnement. Tijdens je gratis proefperiode geniet je van dezelfde voordelen als bij een betaald abonnement. Wanneer je gratis proefperiode afloopt, worden automatisch de maandelijkse abonnementskosten in rekening gebracht. Je kunt maandelijks opzeggen.
Hoeveel kost Audible?
Audible biedt 2 maandabonnementen om uit te kiezen: - Audible Standard kost [€ 6,99] per maand. - Audible Premium kost [€ 9,95] per maand. Beide abonnementen bieden nieuwe leden een gratis proefperiode van 30 dagen. Wanneer je proefperiode afloopt, worden automatisch de maandelijkse abonnementskosten in rekening gebracht. Bezoek onze Lidmaatschapsplannen en prijzen voor meer informatie.
Wat krijg ik bij een maandelijks Audible-abonnement?
Met een Premium-abonnement ontvang je elke maand 1 credit dat je kunt gebruiken om een titel uit onze volledige catalogus te kiezen. Deze titel is voor altijd van jou, zelfs als je je abonnement opzegt. Je credits worden elke maand overgedragen totdat ze verlopen of totdat je je abonnement opzegt. Je krijgt ook toegang tot duizenden titels in de catalogus voor onbeperkt luisteren, en je kunt profiteren van exclusieve aanbiedingen voor Premium-leden en speciale kortingen bij aankoop van extra audioboeken. Met een Standard-abonnement kun je elke maand 1 audioboek kiezen uit onze volledige catalogus. Je kunt naar je geselecteerde audioboeken luisteren zolang je een abonnement hebt, en extra audioboeken kopen voor de volledige prijs. Ongebruikte maandelijkse audioboekselecties schuiven niet door naar de volgende maand.
Wat gebeurt er met de audioboeken in mijn bibliotheek als ik mijn abonnement opzeg?
Alle audioboeken die je koopt met geld of credits blijven van jou, zelfs als je je abonnement opzegt. Met een Audible Standard-abonnement verlies je de toegang tot titels uit de catalogus voor onbeperkt luisteren en alle titels die je hebt geselecteerd als onderdeel van je maandelijkse selectie. Deze titels zijn gemarkeerd met een slotpictogram in je bibliotheek. Zodra je je opnieuw abonneert, krijg je weer toegang tot deze vergrendelde titels.
Moet ik me voor een bepaalde periode binden?
Je zit nergens aan vast. Je kunt je abonnement eenvoudig maandelijks opzeggen. Alle titels die je met een credit hebt gekocht, blijven van jou, zelfs na het opzeggen.
```
</details>

