# Gamma Adjust layout configuration

Edit the table below to choose which existing interface sections are shown and
the order in which they appear from top to bottom. Set `enabled` to `true` or
`false`; each `order` value must be a unique positive integer.

Supported section names:

- `controls`: image-loading button and Gamma slider
- `image_comparison`: original and adjusted image previews
- `gamma_curve`: Gamma conversion curve

When `gamma_curve` is enabled, edit the curve in the application by dragging
control points. Double-click within the graph to add a point, right-click a
point to remove it, or use **重設為 Gamma 曲線** to restore the current slider
value. The adjusted image preview follows the edited curve immediately.

| section | enabled | order |
|---|---|---:|
| controls | true | 1 |
| image_comparison | true | 2 |
| gamma_curve | true | 3 |
