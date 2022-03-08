# PS2 Map Hex Overlays

Several python scripts I created to render Planetside 2 map hex overlays. This generates SVG images for all main PS2 continents (as of writing), which can be found in the [svg](./svg) folder along with a few test images I created along the way.

This project uses Cairo and Pango to render the SVGs and text, respectively.

This was meant to lead into implementing mapping on [ps2alerts](github.com/ps2alerts) (https://ps2alerts.com), so if there are alert maps on that website, hooray!

To regenerate the overlays:
```sh
cd src
python3 drawing.py <service-id>
```
Using your [ps2 census service id](https://census.daybreakgames.com/#devSignup) in place of `<service-id>` (Dunno if this will work with `s:example`, never tried it)