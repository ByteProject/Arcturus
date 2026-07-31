#!/bin/bash

npx wasm-pack build --target web
rm pkg/.gitignore

# Inject an export so that we can synchronously check if we've already initiated the module
echo "export {wasm}" >> pkg/glkaudio.js
echo "export let wasm: InitOutput | undefined" >> pkg/glkaudio.d.ts