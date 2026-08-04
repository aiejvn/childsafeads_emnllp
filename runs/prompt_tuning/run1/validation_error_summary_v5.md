# Error summary (82 instance(s) with at least one error)

## Per-tier error counts

- st1: 8/82
- st2: 37/82
- st3: 68/82

## st1 gold -> pred confusions

- physical_goods -> digital_content_or_services: 4x
- physical_services -> physical_goods: 2x
- digital_content_or_services -> physical_goods: 1x
- none -> physical_services: 1x

## st2 missing labels (gold had it, prediction missed it)

- other: missing 10x
- creator_community: missing 6x
- hardware_electronics: missing 6x
- health: missing 4x
- apps: missing 3x
- food: missing 3x
- fashion: missing 2x
- financial: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- apps: extra 8x
- hardware_electronics: extra 6x
- education: extra 4x
- fashion: extra 3x
- health: extra 2x
- other: extra 1x
- financial: extra 1x
- creator_community: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- other -> apps: 4x
- other -> education: 4x
- apps -> hardware_electronics: 2x
- health -> other: 1x
- financial -> apps: 1x
- financial -> hardware_electronics: 1x
- hardware_electronics -> financial: 1x
- other -> financial: 1x
- health -> fashion: 1x
- creator_community -> education: 1x
- creator_community -> apps: 1x
- food -> fashion: 1x
- fashion -> apps: 1x
- food -> apps: 1x
- apps -> creator_community: 1x
- food -> hardware_electronics: 1x

## st3 missing labels (gold had it, prediction missed it)

- no_flag: missing 24x
- undisclosed_advertising: missing 6x
- age_restricted_or_prohibited_product: missing 3x
- misleading_claim: missing 3x
- direct_exhortation: missing 2x
- inadequate_disclosure: missing 2x
- insufficient_context: missing 2x
- hfss_food_marketing: missing 1x

## st3 extra labels (prediction hallucinated, not in gold)

- direct_exhortation: extra 32x
- misleading_claim: extra 28x
- inadequate_disclosure: extra 25x
- undisclosed_advertising: extra 4x
- hfss_food_marketing: extra 2x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- no_flag -> misleading_claim: 18x
- no_flag -> inadequate_disclosure: 10x
- no_flag -> direct_exhortation: 9x
- undisclosed_advertising -> inadequate_disclosure: 6x
- age_restricted_or_prohibited_product -> inadequate_disclosure: 3x
- undisclosed_advertising -> direct_exhortation: 2x
- insufficient_context -> undisclosed_advertising: 2x
- direct_exhortation -> hfss_food_marketing: 1x
- direct_exhortation -> undisclosed_advertising: 1x
- inadequate_disclosure -> undisclosed_advertising: 1x
- age_restricted_or_prohibited_product -> direct_exhortation: 1x
- misleading_claim -> undisclosed_advertising: 1x
- inadequate_disclosure -> misleading_claim: 1x
- age_restricted_or_prohibited_product -> misleading_claim: 1x
- insufficient_context -> hfss_food_marketing: 1x
- misleading_claim -> inadequate_disclosure: 1x
- undisclosed_advertising -> misleading_claim: 1x
