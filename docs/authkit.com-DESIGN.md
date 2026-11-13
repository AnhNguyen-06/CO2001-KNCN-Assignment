# AuthKit — luminous circuit theater

## Overview

A near-black technical world lit by icy blue type, translucent instrument panels and sculptural interface objects. Rounded grotesk headings and restrained sans-serif copy give developer-oriented products a cinematic, engineered presence. Density is low around the narrative and high inside carefully staged product illustrations, with almost no photography or warm color.

### Essentials

- The product name is the opening monument: a centered 476px × 106px wordmark inside a 512px-wide construction frame, above a 24px two-line promise and a fan of three overlapping interface panels.
- Headings look illuminated rather than white: 44px/51px aeonikPro at weight 500 with normal tracking, filled from #d8ecf8 to #98c0ef and a faint cool text glow.
- Darkness occupies almost the entire page: #05060f canvas with blue-white layers at 1–6% opacity; saturated color is confined to tiny indicators and product demonstrations, not marketing bands.
- Actions are small illuminated capsules, not solid billboards: 36px tall, 16px horizontal padding, fully rounded ends, a 6% blue wash and a 1px inset edge.
- Circuit-board staging is a signature device: orthogonal hairlines, corner registration dots, dark beveled chips and cool internal light connect product objects. When no product artwork exists, construct a simplified connected schematic with a central raised module.
- The closing conversion is an illustrated choice rather than a link directory: two 442px × 332px glass panels with 28px corners, 28px/32px titles, a short support line and one small social capsule below.

## Colors

### Brand

| Name | Value | Token | Roles | Use |
| --- | --- | --- | --- | --- |
| Ice action ink | `#d1e4fa` | `--color-action-ink` | text, action | Capsule labels and small icon fills. |
| Frost blue | `#98c0ef` | `--color-heading-blue` | text, accent | Blue end of heading gradients and circuit illumination. |
| Frost highlight | `#d8ecf8` | `--color-heading-light` | text | Light end of luminous heading gradients. |

### Accent

| Name | Value | Token | Roles | Use |
| --- | --- | --- | --- | --- |
| Periwinkle glint | `#c2ccff` | `--color-button-glow` | accent | Thin moving capsule perimeter and focus outline, not a filled button. |

### Neutral

| Name | Value | Token | Roles | Use |
| --- | --- | --- | --- | --- |
| Silver blue | `#c7d3ea` | `--color-quote` | text | Testimonials and clearer supporting details. |
| Cool body gray | `#9da7ba` | `--color-body` | text | Visible body text from rgba(200,212,234,0.78) on the midnight canvas. |
| Muted blue gray | `#81899b` | `--color-muted` | text | Secondary copy from rgba(199,211,234,0.64) on the canvas. |
| Midnight canvas | `#05060f` | `--color-canvas` | background | Continuous page background. |
| Barely raised tile | `#070811` | `--color-tile` | surface | Visible 1% rgba(186,214,247,0.01) feature tile. |
| Closing glass | `#090a14` | `--color-glass` | surface | Visible 2% rgba(186,207,247,0.02) conversion panel. |
| Raised blue wash | `#10121d` | `--color-wash` | surface | Visible 6% rgba(186,214,247,0.06) layer over the canvas. |
| Blue hairline | `#1b1e2a` | `--color-edge` | border | Visible rgba(186,207,247,0.12) edge on the canvas; brighter along the upper rim. |

### Page-type variants

| Only for | Name | Value | Token | Roles | Use |
| --- | --- | --- | --- | --- | --- |
| product demonstrations | Demo violet | `#663af3` | `--color-demo-purple` | action | Custom-branded primary action within the interface illustration. |

## Typography

- **Untitled Sans** — Support copy, labels and actions. Neutral contemporary sans with readable small forms and restrained regular weight. If unavailable, use **Inter**. Use regular weight and retain the hero's slight negative tracking. Font stack: "Untitled Sans", "Inter", system-ui, sans-serif.
- **aeonikPro** — Section headings and conversion card titles. Rounded neo-grotesk with open forms; medium rather than bold. If unavailable, use **Manrope**. Use 400–500 with normal tracking; preserve deliberate line breaks. Font stack: "aeonikPro", "Manrope", system-ui, sans-serif.

| Recipe | Font | Weight | Size | Line height | Tracking | Use |
| --- | --- | --- | --- | --- | --- | --- |
| heading-emphasis | aeonikPro | 500 | 48px | 56px | normal | A broader platform-level promise. |
| heading | aeonikPro | 500 | 44px | 51px | normal | Default two-line section heading. |
| card-heading | aeonikPro | 500 | 28px | 32px | normal | Illustrated conversion choice titles. |
| hero-promise | Untitled Sans | 400 | 24px | 32px | -0.01em | First line beneath the monumental product name. |
| hero-continuation | Untitled Sans | 400 | 24px | 28px | -0.01em | Compact second line of the opening promise. |
| quote | Untitled Sans | 400 | 18px | 24px | normal | Customer testimony. |
| body | Untitled Sans | 400 | 16px | 1.5 | normal | One-sentence section descriptions and feature captions. |
| label | Untitled Sans | 400 | 14px | 20px | normal | Sentence-case eyebrows, small labels and muted explanatory notes. |
| action | Untitled Sans | 400 | 14px | 36px | normal | Marketing capsule labels. |

**Notes:**

- The wordmark is artwork, not the size of the ordinary heading scale; keep it visually distinct from the 44px section titles.
- Use normal tracking on the section scale; only the 24px opening support tightens to -0.01em.
- Luminous headings use a vertical text-clipped gradient and rgba(174,207,242,0.24) 0px 2px 16px text-shadow. Body copy remains flat and subdued.
- The final single-line invitation uses a lighter 400 weight at 44px; retain that softer closing emphasis.

## Layout

**Density:** Airy narrative spacing with tightly assembled technical illustrations; section padding is commonly 120px while component gaps are 8–24px.

### Spacing

| Value | Use |
| --- | --- |
| 8px | Feature tile gaps. |
| 16px | Heading-to-description distance and standard side padding. |
| 24px | Closing tile gap and eyebrow-to-rule separation. |
| 32px | Closing tile bottom text inset and quote-to-author separation. |
| 40px | Testimonial horizontal padding. |
| 48px | Testimonial vertical padding. |
| 56px | Section description to feature-grid gap. |
| 120px | Default major chapter top and bottom padding. |
| 180px | Closing chapter top padding. |

### Containers and grids

- **art stage**: max width 1440px. Centered full-width atmospheric illustrations that fade into the surrounding canvas.
- **chapter**: max width 1040px · side padding 16px. Centered product browser and technical chapter content.
- **description**: max width 440px. Default centered short support paragraph; broader promises can use 560px.
- **feature field**: max width 1076px · 3 columns · gap 8px · side padding 16px. Centered wrapping tile field: three across followed by a centered pair.
- **conversion pair**: max width 940px · 2 columns · gap 24px · side padding 16px. Two equal illustrated conversion cards.
- **testimonials**: max width 996px · 2 columns · gap 0px. Two equal outline-only customer statements separated by a faint vertical rule.

## Corner radius

| Element | Radius |
| --- | --- |
| capsules | 9999px (pill) |
| feature tiles | 16px |
| browser | 12px |
| conversion tiles | 28px |

## Surfaces and depth

### Shadows

| Name | Value | Use |
| --- | --- | --- |
| cool upper rim | `rgba(216, 236, 248, 0.2) 0px 1px 1px 0px inset, rgba(168, 216, 245, 0.06) 0px 24px 48px 0px inset` | Glass conversion cards; lighting comes from within the top edge, not a heavy exterior drop shadow. |

### Surfaces

#### Midnight canvas · level 0

**Use:** Continuous background.

**CSS:** `background: #05060f`

#### Luminous glass · level 1

**Use:** Large conversion panels.

**CSS:** `background: rgba(186, 207, 247, 0.02); border-radius: 28px; box-shadow: rgba(216, 236, 248, 0.2) 0px 1px 1px 0px inset, rgba(168, 216, 245, 0.06) 0px 24px 48px 0px inset; backdrop-filter: blur(4px)`

**Observed:** Thin gradient perimeter, faint internal circuitry and corner dots make the surface feel like a machined translucent part.

**Transfer:** Use this raised treatment for a small number of important choices.

#### Feature glass · level 1

**Use:** Small illustrated capability cards.

**CSS:** `background: rgba(186, 214, 247, 0.01); border: 1px solid rgba(186, 214, 247, 0.06); border-radius: 16px; overflow: hidden`

**Observed:** Almost the same darkness as the canvas; the illustration and illuminated edges define the tile.

**Transfer:** Keep the base dark even when the subject changes.

## Components

### Sparse navigation

**Use:** Opening utility row.

**CSS:** `display: grid; height: 105px; align-items: center; justify-content: space-between`

**Observed:** Small parent-company label on the left, centered compact symbol, repository icon and one Glowing capsule on the right. The row shares the opening's construction lines rather than sitting in an opaque bar.

**Transfer:** Retain three visual anchors with minimal navigation text.

### Glowing capsule

**Use:** Marketing actions throughout the page.

**CSS:** `display: flex; align-items: center; justify-content: center; height: 36px; padding: 0px 16px; border-radius: 9999px; background: rgba(186, 214, 247, 0.06); color: #d1e4fa; box-shadow: rgba(186, 215, 247, 0.12) 0px 0px 0px 1px inset; backdrop-filter: blur(4px)`

**Text style:** `action` — Untitled Sans 400 · 14px/36px

**Observed:** Text is lightly gradient-filled. A masked conic glint follows the perimeter, with a low-opacity blurred companion outside it; some secondary actions have an icon at the right.

**States:** Declared: hover not specified; focus-visible outline rgba(194,204,255,0.3) solid 2px.

### Ruled eyebrow

**Use:** Introduce a capability chapter or the opening.

**CSS:** `display: flex; justify-content: center; align-items: center; gap: 24px`

**Text style:** `label` — Untitled Sans 400 · 14px/20px

**Observed:** Sentence-case label flanked by two short horizontal rules that fade away from the text; never an uppercase badge with a solid fill.

### Illustrated feature tile

**Use:** Concise capability proof.

**CSS:** `display: flex; flex-direction: column; justify-content: flex-end; width: 320px; height: 242px; max-width: 320px; border-radius: 16px; background: rgba(186, 214, 247, 0.01); overflow: hidden`

**Text style:** `body` — Untitled Sans 400 · 16px/1.5

**Observed:** A miniature illuminated mechanism fills the upper region; the centered single-line caption sits in the lower region. The frame is a very faint separate hairline.

**Transfer:** Represent each capability with one meaningful miniature instrument rather than an ordinary icon above a paragraph.

### Conversion choice

**Use:** Final illustrated route to action.

**CSS:** `display: flex; justify-content: center; align-items: flex-end; width: 442px; height: 332px; border-radius: 28px; background: rgba(186, 207, 247, 0.02); backdrop-filter: blur(4px); box-shadow: rgba(216, 236, 248, 0.2) 0px 1px 1px 0px inset, rgba(168, 216, 245, 0.06) 0px 24px 48px 0px inset`

**Text style:** `card-heading` — aeonikPro 500 · 28px/32px

**Observed:** The entire tile is a link. An embossed emblem occupies the upper area over circuitry; title and one support line are grouped near the bottom, with four tiny registration lights near the corners.

**States:** Declared: hover background-color rgba(186,207,247,0.04), brighter inset lighting; focus-visible outline rgba(194,204,255,0.2) solid 2px with 2px offset; active background-color rgba(186,207,247,0.01) with a dark inset depression.

**Transfer:** Offer two genuinely different routes, such as guided setup and self-service, with equal visual weight.

### Testimonial cell

**Use:** Human proof without breaking the technical atmosphere.

**CSS:** `display: flex; flex-direction: column; padding: 48px 40px`

**Text style:** `quote` — Untitled Sans 400 · 18px/24px

**Observed:** Company mark first, then a left-aligned paragraph, then author details after 32px. Cells share an outline lattice with faded rules instead of filled rounded cards.

### Product browser

**Use:** Frame a customizable product demonstration.

**CSS:** `height: 36px; background: rgba(186, 207, 247, 0.02); border-bottom: 1px solid rgba(186, 207, 247, 0.08)`

**Observed:** This is the browser's title strip, with three dim dots at the left; it tops a 992px × 700px dark stage with 12px corners. A central product panel is surrounded by smaller floating configuration panels.

**Transfer:** Use the frame to stage a representative workflow, not to reproduce a complete application.

## Imagery and graphics

### Spotlit product fan

**Use:** Dominant opening object.

**Observed:** Three dark form panels overlap beneath the giant wordmark. The center panel is larger, frontal and brighter; side panels recede and tilt inward. Soft blue spotlights descend from above, while faint grid lines and registration dots cross behind the title and panels. No photographic setting.

**Transfer:** Stage three representative screens or states of the new product, with the most recognizable one frontmost. A simplified HTML interface is sufficient if it has the same overlap, rim light and blue-black material.

**Build:** Place a central panel roughly 392px wide ahead of two roughly 365px panels with 16px radii. Rotate the side planes about 10deg on the Y axis and lower them slightly. Behind them layer three tall conic light wedges, approximately 220–474px wide and 755–771px tall: transparent at 45%, rgba(124,145,182,0.3) at 49%, rgba(124,145,182,0.5) at 50%, transparent by 55%. Blur 15px and keep overall opacity near 0.55. Fade everything into the midnight canvas.

### Circuit instruments

**Use:** Signature product and platform illustrations throughout the narrative.

**Observed:** Isometric-free, mostly frontal circuit boards with beveled chips, recessed tiny controls, luminous nodes and routed connections. Large illustrations sit below short centered headings; outer details disappear into darkness. Colors are predominantly desaturated blue and lavender with isolated tiny warm or purple signals.

**Transfer:** Turn the new product's workflow into a connected central module and several satellite modules. Preserve the visual hierarchy even without a detailed dashboard or industrial artwork.

**Build:** Draw SVG orthogonal paths with 45deg corner cuts at 1px stroke in rgba(186,207,247,0.08). Connect dark rounded rectangular modules with brighter upper rims. Add small 3–6px light nodes and sparse dashed traces; highlight only the central module using a soft blue radial glow. Mask the edges of the entire 1040px-wide scene with a radial fade. Add a separate construction lattice of 1px rules and tiny corner dots behind important headings.

### Soft solid sculpture

**Use:** A major technology or foundation chapter.

**Observed:** An oversized blue glass emblem made from a rounded square, circle and half-disc floats in front of a collage of code snippets and small interface fragments. Its bevels catch cloudy cyan light; the lower form sinks behind a translucent action band.

**Transfer:** Use the new product's own simple abstract geometry or an original three-part emblem. The minimum equivalent is layered SVG primitives with softly lit edges and dim interface fragments behind.

**Build:** Arrange a rounded rectangle, circle and semicircle into a vertical sculpture about 560px wide. Fill each with layered blue-gray radial gradients, darken the lower-right edge and add a thin cool outer rim plus an inset blurred highlight. Place code and UI fragments behind at lower contrast, then overlay a dark translucent band across the bottom with a 6px backdrop blur.

### Embossed closing emblems

**Use:** Upper halves of Conversion choice tiles.

**Observed:** A dark plaque and round medallion are embedded into thin circuit traces; their faces are only slightly lighter than their surroundings. Text stays brighter and legible below.

**Transfer:** Use an original product plaque and a complementary route symbol, maintaining dark relief rather than colorful logo stickers.

**Build:** Layer two rounded SVG outlines with a 1px offset highlight and dark inner shape. Add a soft blue radial highlight near the upper rim; route several thin traces toward the emblem, fade them at the card boundary and add four 3px corner lights.

### Icons

**Observed:** Small action icons are filled, typically 12–16px, in icy blue; a 20px outline control uses a 1.5px rounded stroke. Larger emblems belong to the illustration rather than the navigation vocabulary.

**Transfer:** Use compact simple symbols at the action baseline; keep feature narratives in the miniature instrument artwork rather than oversized generic outline icons.

## Section recipes

How recurring sections are built.

### First screen: Spotlit opening

**Observed:** A sparse 105px navigation row shares the construction lattice with a centered vertical stage. Midnight canvas sits behind faint circuit lines and soft overhead light, followed by a small Ruled eyebrow, the 476px-wide product-name artwork in a 512px frame, and the two-line hero promise. The name spans roughly one third of the viewport, not edge to edge. A three-panel Spotlit product fan begins just below the text, with the center face raised above the sides. Within the first 900px the navigation action, name, full promise and most of the overlapping panels are visible; their bottoms, appearance switch and capability strip extend below the fold. The primary marketing action is at the upper right rather than a large button pair beneath the headline.

**Transfer:** Use a short new product name or compact typographic lockup at the same visual footprint, then a concise promise and a recognizable original product scene. The spotlight and construction lattice remain essential even when the scene is simplified. A more focused landing page can shorten the panel fan while retaining the centered hierarchy.

**Avoid:** Do not replace this with a left-copy/right-dashboard split, an enormous white paragraph headline or a bright gradient background.

**Text style:** `hero-promise` — Untitled Sans 400 · 24px/32px · tracking -0.01em

### Luminous chapter header

**Observed:** Ruled eyebrow, a centered heading usually split into two deliberate lines, then a short paragraph 16px below. Chapter padding is commonly 120px; support text defaults to 440px wide. The artwork carries far more visual area than the copy.

**Transfer:** Pair two terse benefit clauses and follow with one concrete mechanism; change the illustration per chapter.

**Text style:** `heading` — aeonikPro 500 · 44px/51px

### Customization theater

**Observed:** A Luminous chapter header sits above Product browser. A large centered UI panel is surrounded by smaller color, shape and branding control panels, all floating on the same blue-black stage with faint construction lines.

**Transfer:** Show how one representative output changes; use a few meaningful configuration fragments rather than a full settings page.

### Sculpture and fragments

**Observed:** A centered heading introduces Soft solid sculpture layered over code and interface fragments. A translucent lower band carries a Glowing capsule between faded rules.

**Transfer:** Give one important foundation or differentiator a sculptural emblem and concrete surrounding fragments.

### Centered miniature field

**Observed:** Luminous chapter header followed after 56px by Illustrated feature tiles: three on the first row and two centered below, separated by 8px. Each card carries one mechanism and one short caption.

**Transfer:** Use the same centered wrapping logic for an appropriate number of capabilities rather than forcing a rectangular matrix.

### Outline proof pair

**Observed:** Two Testimonial cells fill a 996px-wide outline field with subtle horizontal and vertical separators. Logos, quotations and authors replace the image-heavy chapter treatment.

**Transfer:** Use authenticated customer testimony with the same restrained field, giving the narrative a quieter human pause.

### Illustrated closing choice

**Observed:** After 180px of top padding, a centered closing invitation sits within construction lines. Two Conversion choice panels follow with 24px between them, and a single small social Glowing capsule sits 95px below the panel row. The page ends in dark space and fading rules, not a conventional multi-column footer.

**Transfer:** End with two actionable paths rendered as objects, followed by one light-touch community or contact action.

**Text style:** `heading` — aeonikPro 500 · 44px/51px

## Page flow

**Storyline:** product promise → architectural demonstration → adaptability → technical foundation → capability proof → platform breadth → human proof → illustrated action choice

### A flagship product landing page that makes technical infrastructure feel tangible and desirable

1. **Promise** — Centered product-name monument and spotlighted overlapping interface panels.
2. **Capability overview** — Compact strip of six capability labels below the opening stage.
3. **Architecture proof** — Connected central chip and satellite workflow modules beneath a two-part heading.
4. **Adaptability** — A browser theater with floating customization controls.
5. **Foundation credibility** — Sculptural emblem amid code and interface fragments with a small learn-more action.
6. **Capability chapters** — Miniature instrument tiles and a larger integrated platform diagram.
7. **Social proof** — Two restrained quote cells with company marks and authors.
8. **Closing call** — Two illustrated conversion routes and a small social capsule.

**Transfer:** Borrow the alternation of short claims and substantial visual demonstrations. Reorder or reduce chapters to suit the new product while retaining the luminous objects, miniature mechanisms and illustrated closing choice.

## Writing

Confident, concise and technically literate. Benefits are framed as direct ownership and flexibility, then supported by concrete mechanisms rather than exuberant storytelling.

**Do not copy:** Do not reuse AuthKit, WorkOS or Radix branding, logo artwork, customer quotations, company names, adoption claims or superiority claims as facts about another product. The examples below show the pattern only; write new copy for the new product.

- **Addressing the reader:** Use your for user outcomes; name the product in supporting explanations. The voice rarely needs we.
- **Rhythm:** Headlines favor short parallel clauses, often arranged into two lines. Support is usually one sentence; action labels are compact and literal, without exclamation marks.

| Role | Pattern | Typical length | Examples of the pattern |
| --- | --- | --- | --- |
| Opening promise | A crisp category claim followed by a foundation clause. | Two short lines | “The world’s best login box,”<br>“powered by WorkOS + Radix.” |
| Section headline | Parallel possessive fragments or paired audience benefits. | 4–10 words | “Your users. Your data. Maximum flexibility.”<br>“Designed for developers. Built for the enterprise.” |
| Supporting line | Product name plus a concrete capability and outcome. | One sentence | “[Brand] can be fully customized to fit natively with your app's unique design.” |
| Eyebrow | A compact conceptual label, sentence case. | 2–4 words | “Extensible by design”<br>“Framework freedom” |
| Primary action | Simple imperative or specific learn-more destination. | 2–8 words | “Get started”<br>“Start building today” |

**Words and phrasing to use:** your; built; designed; compatible; customized; flexibility; integrates; supports

**Avoid:** revolutionary magic; disrupt everything; !!!; vague transformation language; forced jokes

**Rules:**

- Let paired headline clauses carry the memorable language; keep the explanation literal.
- Connect technical terms to a reader benefit in the same sentence.
- Keep tile captions short enough for a single centered line when practical.
- Use specificity only when the product can substantiate it.

## Do's and Don'ts

### Do

- Keep the continuous #05060f canvas visible between every major visual scene.
- Use 44px/51px medium section headings and 16px/24px support copy.
- Keep default descriptions near 440px wide and centered.
- Make raised edges with low-alpha cool light rather than gray opaque borders.
- Retain 36px capsule actions with 16px side padding.
- Give feature illustrations a consistent 320px × 242px stage.
- Use construction lines and tiny registration dots to tie text and imagery together.
- Keep the two illustrated closing choices equal in size and emphasis.

### Don't

- Do not turn the blue atmosphere into full-width saturated blue sections.
- Do not apply the violet demo action color to the marketing navigation.
- Do not make every tile a brightly outlined dashboard widget; most edges sit near 6–12% opacity.
- Do not raise heading weight to 700 or tighten all headings with heavy negative tracking.
- Do not substitute stock people photography for the product mechanisms.
- Do not expand the 14px eyebrows into spaced uppercase editorial labels.
- Do not add dense descriptive paragraphs to the miniature feature tiles.
- Do not use broad exterior drop shadows as the primary card lighting; the material depends on inset upper rims.

## Motion and responsive

### Motion

**Observed:**

- Declared conversion-card transitions: background-color and box-shadow 0.45s cubic-bezier(0.6,0.6,0,1).
- Declared opening text opacity and transform transitions last 1.5s with delays; wordmark opacity transition is 2s with 0.1s delay.
- Declared ambient effects include 12s linear looping card lines, 40s linear radar rotation, and spotlight opacity and scale cycles of 6s and 8.5s.

**Transfer:**

- Keep ambient motion inside the instruments and light fields; typography resolves into a stable, readable layout.
- Use subtle perimeter glints and changing inset light to reinforce the glass material, not large positional hover jumps.

**Unknown:**

- Exact choreography and complete animation paths are not established.

### Responsive

**Observed:**

- Declared width breakpoints: 440px, 640px, 940px, 996px, 1199px and 1200px.

**Transfer:**

- On narrow screens preserve the centered name, short promise and one dominant frontal panel; let side panels recede or clip rather than shrinking all UI illegibly.
- Wrap miniature tiles and stack the closing choices while keeping the original rounded materials and subdued circuitry.

**Unknown:**

- Narrow-screen layouts and exact breakpoint-specific rules are not established.

## How to use this guide

1. Start from the Essentials and the first-screen recipe; where the guide offers variants, use the default named for a new marketing page.
2. Plan the page before building: map your content onto the section recipes and page flow, then check the plan against the Do's and Don'ts.
3. Build with the tokens and component specs; recreate signature graphics with their build recipes instead of generic decoration, and use the named font substitutes if a font is unavailable.
4. Render the page at desktop and mobile widths, compare it with the Essentials and the Don'ts, and fix the differences before you finish.
