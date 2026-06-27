#!/usr/bin/env python3
# build_vsix.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""Package the VS Code extension under editors/vscode into a .vsix file.

A .vsix is an Open Packaging Conventions zip: a root manifest and content-type
map plus an `extension/` folder holding the extension files. This builds one
with the standard library only, so no Node.js or vsce is required. The result
installs with `code --install-extension arcturus-<version>.vsix` on macOS,
Windows, and Linux.

Usage:
    python3 tools/build_vsix.py
"""

from __future__ import annotations

import json
import os
import zipfile

# Files copied into the extension/ folder of the package, relative to the
# extension directory.
_EXTENSION_FILES = [
    "package.json",
    "language-configuration.json",
    "README.md",
    "syntaxes/storyarc.tmLanguage.json",
]

_CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="md" ContentType="text/markdown" />
  <Default Extension="vsixmanifest" ContentType="text/xml" />
</Types>
"""


def _manifest(meta: dict) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{meta['name']}" Version="{meta['version']}" Publisher="{meta['publisher']}" />
    <DisplayName>{meta['displayName']}</DisplayName>
    <Description xml:space="preserve">{meta['description']}</Description>
    <Tags>{','.join(meta.get('keywords', []))}</Tags>
    <Categories>Programming Languages</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{meta['engines']['vscode']}" />
      <Property Id="Microsoft.VisualStudio.Services.Links.Source" Value="https://github.com/ByteProject/Arcturus" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true" />
  </Assets>
</PackageManifest>
"""


def build() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    ext_dir = os.path.join(repo_root, "editors", "vscode")

    with open(os.path.join(ext_dir, "package.json"), "r", encoding="utf-8") as fh:
        meta = json.load(fh)

    out_name = f"{meta['name']}-{meta['version']}.vsix"
    out_path = os.path.join(ext_dir, out_name)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as vsix:
        vsix.writestr("[Content_Types].xml", _CONTENT_TYPES)
        vsix.writestr("extension.vsixmanifest", _manifest(meta))
        for rel in _EXTENSION_FILES:
            src = os.path.join(ext_dir, rel)
            with open(src, "r", encoding="utf-8") as fh:
                vsix.writestr("extension/" + rel, fh.read())

    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    build()
