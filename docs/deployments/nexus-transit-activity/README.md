# Nexus Transit Activity — Phase 1 deployment

This deployment artifact consolidates ownership of `light.stairs` around one
derived corridor-occupancy entity. It was built from the live reference in
`ha-live-reference` and is not connected to Home Assistant automatically.

## Deploy

1. Ensure Home Assistant loads `/config/packages/` with
   `homeassistant: packages: !include_dir_named packages`.
2. Copy `packages/nexus_transit_activity.yaml` to
   `/config/packages/nexus_transit_activity.yaml`.
3. Replace `/config/automations.yaml` with the `automations.yaml` in this
   directory, after reviewing the snapshot against the current live file.
4. Run Home Assistant's configuration check.
5. Reload Template entities and Automations, or restart Home Assistant.
6. Confirm `binary_sensor.nexus_transit_activity` appears and that only the
   Nexus Transit Activity automation controls `light.stairs`.

The replacement `automations.yaml` preserves the unrelated automations from
the supplied live reference. It removes the stair branch from
`Motion Lighting - Hallway and Sleep Navigation` and removes the obsolete
`Night Hallway Guide`; the package owns the consolidated stair-light behavior.

## Behavior

Transit Activity turns on when any verified corridor sensor is on and turns off
only after all three have been continuously off for three minutes. Daytime
behavior remains 50% at 6535 K. Evening, Night, and Movie remain 30% cool blue.
Sleep uses the existing intentional 20% warm navigation behavior at 2200 K.

The automation reacts only to Transit Activity transitions. It does not
reassert the light while Transit Activity remains on, so a manual light-off
command is not immediately defeated.
