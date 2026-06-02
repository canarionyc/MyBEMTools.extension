cd bem_api/data

jq ".Walls | to_entries | map({Name: .key} + .value)" catalog.json > walls.json
jq ".Roofs | to_entries | map({Name: .key} + .value)" catalog.json > roofs.json
jq ".Floors | to_entries | map({Name: .key} + .value)" catalog.json > floors.json

jq '.["Structural Foundations"] | to_entries | map({Name: .key} + .value)' catalog.json > structural_foundations.json

jq '.["Stacked Walls"] | to_entries | map({Name: .key} + .value)' catalog.json > stacked_walls.json