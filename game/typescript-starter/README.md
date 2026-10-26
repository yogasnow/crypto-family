# FujiBall · TypeScript starting point

`game.ts` is the first typed slice of the **next** game implementation: a scene contract, game state, three financial-literacy examples, and answer progression. It is intentionally independent of the currently playable JavaScript demo; the online game still loads `game/fujiball-spiral/app.js` and `scenes.js`.

## Run and inspect

Use Node.js 22+ and TypeScript 5+:

```sh
npx --yes --package typescript tsc --strict --target ES2022 --module NodeNext --moduleResolution NodeNext --noEmit game.ts
```

No API key, wallet, account, or market data is required. The example teaches risk recognition; it does not execute trades or recommend an asset.

## Continue development

1. Review the three scene drafts and verify their sources and wording with learners before release.
2. Port the eight existing scenes from `../fujiball-spiral/scenes.js` without changing their meaning.
3. Move rendering and local progress handling from `../fujiball-spiral/app.js` into typed modules.
4. Add crypto-specific scenes, playtest them, and only then replace the live build.

The TypeScript module is licensed under [MIT](../../CODE-LICENSE.md).
