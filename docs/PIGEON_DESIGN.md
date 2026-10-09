# PIGEON design system

PIGEON uses native HTML, CSS, and JavaScript modules. Keep the existing stylesheet order: the numbered legacy stylesheets retain their cascade, and `static/css/pigeon.css` owns the shared presentation layer after them.

## Identity

The approved master is preserved byte for byte in `static/branding/pigeon-master.png`. UI bird/wordmark assets are faithful deterministic extractions. Icons use the bird alone; the maskable composition fits inside its central safe circle. Do not recolor the bird with theme accents.

## Palette and roles

| Role | Default |
| --- | --- |
| Canvas | Midnight Charcoal `#0D0F14` |
| Navigation | `#151820` |
| Elevated surfaces | `#1F232D` |
| Body text | `#E9E4DF` |
| Prominent brand text | Warm Ivory `#FBE7BA` |
| Primary action | Crimson `#FB2835` |
| Deep emphasis | Burgundy `#8D071C` |
| Selected highlights | Ember `#FF6611`, Flame `#FE8F15` |
| Focus and premium emphasis | Champagne Gold `#FDCD61` |
| Control boundaries | `#766F79` |

Use semantic variables for surfaces, text, borders, actions, focus, status, elevation, spacing, radii, and motion. Solid action text is selected for contrast by `static/js/color/contrast.js`; bright crimson uses dark text. Syntax and status colors remain distinct functional roles.

## Typography and interaction

Inter is the default UI face. Fira Code serves code and technical content. Existing serif, monospace, OpenDyslexic, custom-font, density, theme, and background controls remain available. Legacy theme/font preferences keep their storage keys. New preferences identify the new implicit font default without changing API paths.

Preserve IDs, data attributes, module exports, event names, and canonical module import URLs. Shared windows keep their dragging, docking, resizing, minimization, and keyboard behavior. Reduced-motion preferences suppress decorative transitions and animation.

## Maintenance

Update the app stylesheet URLs and service-worker precache together. New assets must enter the publication ledger. Regenerate computed-style baselines only after reviewing intended visual changes; preserve raw attempts outside the published tree. Generated research, search, and authorization pages retain their original handlers and escaping while sharing the PIGEON presentation language.

Upstream acknowledgments and third-party notices remain intact. Local runtime, credentials, dependencies, raw evidence, and private planning records are excluded from Git and container build contexts.
