# m5paper-homeassistant-remote
UI for m5paper device to control a home assistant over rest and mqtt

## To-do
- Read configuration from a file

## Instructions


## Idea
The goal of this project is to provide an adaptable user interface for home assistant on the m5paper device. 
The m5paper is an esp32 based microcontroller with a 4.7" E-INK touchscreen, a battery and a lot of other peripherals. 
As my Home Assistant is a playground and evolving quiet a lot during time I would like to adapt the UI to my needs as easy as possible.

## Base-Layout
The basic layout was designed in UI-Flow by placing labels, images and frames. The initial template is stored in (documentation)[documentation]


## Logic
- Define the entities and button positions in a configuration
- Each button instance fetches some data from home assistant over the REST API for ex. "friendly-name", "state"
- The device is listening for state changes over mqtt statestream integration