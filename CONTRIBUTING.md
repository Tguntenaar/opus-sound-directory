# Contributing to Opus Sounds Directory

Thanks for helping make the directory useful. You can suggest sounds, improve synthesis, fix the site or clarify documentation.

## Suggest a sound or report an issue

[Open an issue](https://github.com/Tguntenaar/opus-sound-directory/issues/new) with the sound's intended use, desired duration and any frame cues. For bugs, include the affected page and steps to reproduce.

## Submit a sound

Use the [submission form](https://opussounds.directory/submit), or follow [Adding an entry](docs/DEVELOPMENT.md#adding-an-entry) for a pull request.

Include the creative prompt, executable synthesis code, audio, spectrogram and measured duration, loudness and true peak. Check for clipping, clicks and unintended silence; listen to the result. For loops, check the join. Identify the actual authoring model or tool and preserve generation provenance where available.

Contribute original material that you have the right to share. Do not submit copied recordings, game melodies or trademarked sound recreations. Put unselected experiments in `provenance/` and identify them as candidates rather than replacing published assets prematurely.

## Change the site or documentation

Use a focused branch and describe the change and relevant verification in your pull request. See the [development guide](docs/DEVELOPMENT.md) for setup and operations. For application changes, run the relevant checks, such as `npm test` and `npm run build`. Documentation-only changes should check links and Markdown rendering.

## Contribution licenses

By submitting a contribution, you agree to license your code and documentation under [MIT](LICENSE), and your sound audio, spectrograms and creative sound prompts under [CC0 1.0](ASSETS-LICENSE.md). Only contribute material you can share under these terms. Third-party dependencies keep their own licenses.
