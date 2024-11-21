# switch_fan

A Home Assistant helper that combines multiple switches and lights into a fan entity.

## Installation

There are two ways this integration can be installed into [Home Assistant](https://www.home-assistant.io).

The easiest way is to install the integration using [HACS](https://hacs.xyz).

Alternatively, installation can be done manually by copying the files in this repository into the custom_components directory in the HA configuration directory:

1. Open the configuration directory of your HA configuration.
2. If you do not have a custom_components directory, you need to create it.
3. In the custom_components directory create a new directory called combined_energy.
4. Copy all the files from the custom_components/switch_fan/ directory in this repository into the switch_fan directory.
5. Restart Home Assistant
6. Add the integration to Home Assistant (see `Configuration`)

### Configuration

After you have installed the custom component (see above):

1. Goto the Settings -> Devices & Services -> Helpers
2. On the bottom right of the page, click on the + Create Helper sign to add a new fan.
3. Search for Switch Fan. (If you don't see it, try refreshing your browser page to reload the cache.)
4. Supply a name for the new fan and select all the entities to be used by the fan. The order is **very** important as it is used to determine the speed of the fan. The ordering it slowest to fastest (top to bottom).
5. Click Submit to add the fan.
