# Seed: the developer's answers while shaping (2026-10-31)

This is a seed input, kept verbatim and never groomed. These are the answers to the shaping
questions asked in `brainframe-application-test-remarks.md`, and to the decisions the first clarity
gate run raised.

## Shaping questions

> 1. lookup each time ... but there can be a simple prefixes.json saved locally, if someone wants to
>    control them, and provide as paramaters (this logic existed previously in th the fingerprinter)
> 2. yes inside the html, but it is a good idea to add such filter on the generator too
> 3. keep format doc (but i'm not sure what the options are)
> 4. yeah, that looks decent, skip model2owl
> 5. both (but we will have lots of diagrams, and haing one per class it a no-go, we need somethign
>    more digestable)

## After the first clarity gate run (6.8/10)

Questions put to the developer:
1. Should shape IRIs be minted inside namespaces we don't own (accept, with a risk note)?
2. Should the prefix.cc lookup be on by default, with an opt-out?
3. Should the browser behaviour be tested by static HTML checks plus a manual check, with no
   Playwright?
4. What happens to the 1.x custom-template API: keep it, or allow a major rework?

> , we shall by default, skip also the "standard" meta namespaces, such as rdf, rdfs, owl and shacl.
> 1. fine
> 2. okay
> 3. no need for playwrite
> 4. major rework please

> proceed with implementation, afterwards

## After the second clarity gate run (7.9/10)

The question put to the developer: "prefix.cc's HTTPS certificate expired on 31 Dec 2025. The full
prefix list is still served over plain http://prefix.cc/popular/all.file.json. With the lookup on
by default, how should the fingerprinter fetch it?"

The developer's answer: **"HTTPS, fall back to HTTP (Recommended)"**. This was the first of the
options offered: try HTTPS with certificate checks, and only if that fails on the certificate,
fetch over plain HTTP, logged at INFO. Every name is still validated, so tampering in transit could
only change the labels.

> ok, carry on when the gate passes,
