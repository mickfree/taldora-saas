module.exports = {
    darkMode: 'class',
    content: [
        '../templates/**/*.html',
        '../../templates/**/*.html',
        '../../**/templates/**/*.html',
    ],
    theme: {
        extend: {
            colors: {
                brandBg: '#191919',
                brandHover: '#2a2a2a',
                brandAccent: '#48a1ff',
                brandMuted: '#bbbbbb',
                primary: {
                    50: '#ecf6ff',
                    100: '#d5ebff',
                    200: '#b4ddff',
                    300: '#82c8ff',
                    400: '#48a1ff',
                    500: '#1d81ff',
                    600: '#005eff',
                    700: '#004ee6',
                    800: '#003eb8',
                    900: '#063b94',
                }
            }
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
    ],
}
