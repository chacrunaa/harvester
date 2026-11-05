/* eslint-env node */
module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  settings: {
    react: { version: 'detect' },
  },
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'simple-import-sort',
  ],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
    'prettier',
  ],
  ignorePatterns: ['dist', 'node_modules', '.eslintrc.cjs'],
  rules: {
    '@typescript-eslint/consistent-type-definitions': ['error', 'type'],
    '@typescript-eslint/no-unused-vars': [
      'error',
      { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],
    'simple-import-sort/imports': [
      'error',
      {
        groups: [
          // 1. React first
          ['^react$', '^react-dom', '^react/.*'],
          // 2. Other third-party
          ['^@?\\w'],
          // 3. Absolute imports from @/
          ['^@/'],
          // 4. Relative imports
          ['^\\.\\.(?!/?$)', '^\\.\\./?$'],
          ['^\\./(?=.*/)(?!/?$)', '^\\.(?!/?$)', '^\\./?$'],
          // 5. Style imports
          ['^.+\\.s?css$', '^.+\\.module\\.s?css$'],
        ],
      },
    ],
    'simple-import-sort/exports': 'error',
    'react/prop-types': 'off',
  },
};
