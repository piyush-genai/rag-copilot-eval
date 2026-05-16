# Runbooks Astro

[![Built with Starlight](https://astro.badg.es/v2/built-with-starlight/tiny.svg)](https://starlight.astro.build)

```
npm create astro@latest -- --template starlight
```

## Install

```shell
(cd astro && npm install)
```

## 🧞 Build

In order to build the astro static site from the docs, use the `astro.sh` wrapper, which calls out to `npm run`.

You can use run a local dev server:

```shell
astro/astro.sh dev     # starts local dev server at `localhost:4321`
```

If you want to perform a production build (e.g. to test search or static file structure), you can use:

```shell
astro/astro.sh build   # build production site to `astro/dist/`
astro/astro.sh preview # preview your build locally, before deploying
```

## 👀 Want to learn more?

Check out [Starlight’s docs](https://starlight.astro.build/), read [the Astro documentation](https://docs.astro.build).
