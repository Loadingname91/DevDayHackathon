# ADR-005: React (DOM) with Capacitor, Android first

## Status

Accepted · 2026-11-19 · Deciders: Quilt team · Reverses TabOS v3 ADR-5 (Expo / React Native)

## Context

TabOS v3 picks Expo mobile-first with react-native-web and rejects a web-first app. Quilt's whole look and motion already exist as DOM prototypes: CSS tokens, WAAPI, a critically damped spring, an SVG thread pull. Rebuilding them in React Native before the demo is not possible. The demo needs an installed-feeling phone app plus the same app on a laptop.

## Decision

One React app built with Vite. Capacitor wraps it as an Android app (APK, sideloaded for DevDay); the same build is served as a website for the laptop and any browser. Native needs go through Capacitor plugins: Camera, speech recognition, text-to-speech, App (deep links, later). The app holds no secrets; it calls our API (ADR-004).

## Consequences

- The prototype code ports as-is; the design book is the reference implementation.
- iOS is a later Capacitor target (needs a Mac and signing); share-into-Quilt and push arrive with native targets.
- WebView quirks replace React Native quirks: test touch, safe areas and the keyboard on the real Android phone at D3.
- v3's own reversal path already allowed a native-web renderer; blocks over the wire keep the backend unchanged either way.
- Reversal trigger: WebView performance or native feel measurably hurting retention; then a React Native renderer reads the same API.

## Alternatives considered

- **Expo per v3:** better native feel and a local SQLite store; every animation rebuilt first.
- **Web only (PWA):** fastest, but no Android share sheet, weaker camera and speech access.

## References

`docs/ui-tech-plan.md` §1, TabOS v3 §12.
