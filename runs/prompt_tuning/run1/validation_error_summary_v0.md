# Error summary (77 instance(s) with at least one error)

## Per-tier error counts

- st1: 9/77
- st2: 37/77
- st3: 62/77

## st1 gold -> pred confusions

- physical_goods -> digital_content_or_services: 4x
- physical_services -> digital_content_or_services: 1x
- none -> digital_content_or_services: 1x
- digital_content_or_services -> physical_goods: 1x
- none -> physical_services: 1x
- physical_services -> physical_goods: 1x

## st2 missing labels (gold had it, prediction missed it)

- other: missing 11x
- hardware_electronics: missing 5x
- creator_community: missing 4x
- food: missing 4x
- apps: missing 3x
- financial: missing 1x
- health: missing 1x
- gambling_adjacent: missing 1x
- fashion: missing 1x

## st2 extra labels (prediction hallucinated, not in gold)

- apps: extra 7x
- other: extra 4x
- hardware_electronics: extra 4x
- health: extra 4x
- education: extra 4x
- gambling_adjacent: extra 3x
- financial: extra 3x
- fashion: extra 3x
- creator_community: extra 2x
- gambling: extra 1x

## st2 inferred missing -> extra substitutions (same-instance co-occurrence)

- other -> education: 4x
- other -> apps: 3x
- other -> financial: 3x
- food -> fashion: 2x
- food -> hardware_electronics: 2x
- financial -> apps: 1x
- financial -> hardware_electronics: 1x
- hardware_electronics -> financial: 1x
- health -> fashion: 1x
- creator_community -> education: 1x
- creator_community -> apps: 1x
- apps -> hardware_electronics: 1x
- food -> creator_community: 1x
- gambling_adjacent -> gambling: 1x
- apps -> other: 1x
- hardware_electronics -> other: 1x
- fashion -> apps: 1x
- food -> apps: 1x
- apps -> creator_community: 1x

## st3 missing labels (gold had it, prediction missed it)

- misleading_claim: missing 40x
- inadequate_disclosure: missing 16x
- no_flag: missing 7x
- direct_exhortation: missing 6x
- age_restricted_or_prohibited_product: missing 2x
- insufficient_context: missing 2x

## st3 extra labels (prediction hallucinated, not in gold)

- no_flag: extra 20x
- undisclosed_advertising: extra 16x
- inadequate_disclosure: extra 10x
- direct_exhortation: extra 5x
- misleading_claim: extra 1x
- hfss_food_marketing: extra 1x
- age_restricted_or_prohibited_product: extra 1x

## st3 inferred missing -> extra substitutions (same-instance co-occurrence)

- misleading_claim -> no_flag: 20x
- inadequate_disclosure -> undisclosed_advertising: 10x
- misleading_claim -> undisclosed_advertising: 6x
- no_flag -> inadequate_disclosure: 5x
- inadequate_disclosure -> no_flag: 5x
- misleading_claim -> inadequate_disclosure: 4x
- direct_exhortation -> undisclosed_advertising: 2x
- misleading_claim -> direct_exhortation: 2x
- insufficient_context -> undisclosed_advertising: 2x
- no_flag -> misleading_claim: 1x
- age_restricted_or_prohibited_product -> inadequate_disclosure: 1x
- no_flag -> age_restricted_or_prohibited_product: 1x
- no_flag -> undisclosed_advertising: 1x
- no_flag -> direct_exhortation: 1x
- age_restricted_or_prohibited_product -> direct_exhortation: 1x
- inadequate_disclosure -> direct_exhortation: 1x
- direct_exhortation -> no_flag: 1x
