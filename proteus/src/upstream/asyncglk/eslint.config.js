import eslintPluginSvelte from 'eslint-plugin-svelte'
import globals from 'globals'
import js from '@eslint/js'
import svelteParser from "svelte-eslint-parser"
import tseslint from 'typescript-eslint'

export default [
    js.configs.recommended,
    ...tseslint.configs.recommended,
    ...eslintPluginSvelte.configs['flat/recommended'],
    {
        files: ['**/*.svelte', '*.svelte'],
        languageOptions: {
            parser: svelteParser,
            parserOptions: {
                parser: '@typescript-eslint/parser',
            },
        },
    },
    {
        languageOptions: {
            ecmaVersion: 12,
            globals: {
                ...globals.browser,
                ...globals.es2020,
                ...globals.jquery,
                ...globals.node,
            },
            sourceType: 'module',
        },
        rules: {
            'brace-style': ['error', 'stroustrup', {'allowSingleLine': true}],
            'comma-dangle': ['error', 'always-multiline'],
            curly: ['error'],
            eqeqeq: ['error', 'always', {null: 'ignore'}],
            indent: ['error', 4, {SwitchCase: 1}],
            'linebreak-style': ['error', 'unix'],
            'no-constant-condition': ['error', {checkLoops: false}],
            'no-control-regex': ['off'],
            'no-empty': ['error', {allowEmptyCatch: true}],
            'prefer-const': ['error', {destructuring: 'all'}],
            quotes: ['error', 'single'],
            semi: ['error', 'never'],
            '@typescript-eslint/no-empty-function': ['off'],
            '@typescript-eslint/no-explicit-any': ['off'],
            '@typescript-eslint/no-non-null-assertion': ['off'],
            '@typescript-eslint/no-unused-vars': ['error', {'args': 'none'}],
        },
    },
]